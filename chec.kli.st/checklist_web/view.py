# !/usr/bin/env python
#
# Copyright 2008 CPedia.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__author__ = 'Ping Chen'

import os
import re

import logging

from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

import copy
import time
import urlparse
import string

import config

import cpedia.checklist.cache.util as cache_util


class ViewPage(object):
    def __init__(self, cache_time=None):
        """Each ViewPage has a variable cache timeout"""
        if cache_time == None:
            self.cache_time = config.CHECKLIST["cache_time"]
        else:
            self.cache_time = cache_time

    def full_render(self, handler,template_file, params={}):
            #scheme, netloc, path, query, fragment = urlparse.urlsplit(handler.request.uri)
            if users.get_current_user():
                url = users.create_logout_url(handler.request.uri)
            else:
                url = users.create_login_url(handler.request.uri)

            template_params = {
                "CHECKLIST": config.CHECKLIST,
                "title": config.CHECKLIST['title'],
                'user': users.get_current_user(),
                'sign_url': url,
                'request': handler.request,
                "user_is_admin": users.is_current_user_admin(),
                "user_tags": cache_util.get_user_tags(users.get_current_user()),
            }
            template_params.update(params)
            return template.render(template_file, template_params, debug=config.DEBUG)



    def render_or_get_cache(self, handler, template_file, template_params={}):
        """Checks if there's a non-stale cached version of this view, and if so, return it."""
        if self.cache_time:
            key = handler.request.url + str(users.get_current_user() != None) + str(users.is_current_user_admin())
            output = memcache.get(key)
            if not output:
                logging.debug("Couldn't find a cache for %s", key)
            else:
                logging.debug("Using cache for %s", template_file)
                return output

            output = self.full_render(handler, template_file, template_params)
            # Add a value if it doesn't exist in the cache, with a cache expiration of 1 hour.
            memcache.add(key=key, value=output, time=self.cache_time)
            return output

        return self.full_render(handler, template_file, template_params)


    def render(self, handler,template_name, params={}):
        dirname = os.path.dirname(__file__)
        template_file = os.path.join(dirname, os.path.join('templates', template_name))
        logging.debug("Using template at %s", template_file)
        output = self.render_or_get_cache(handler, template_file, params)
        handler.response.out.write(output)
