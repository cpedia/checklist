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

import cgi
import wsgiref.handlers
import os
import re
import datetime
import calendar
import logging
import string
import urllib

from xml.etree import ElementTree

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext import search

from cpedia.deal.handlers import restful
import cpedia.deal.models.deal as models

import simplejson
import authorized
import view
import config

import sys
import urllib
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup

class BaseRequestHandler(webapp.RequestHandler):
    """Supplies a common template generation function.

    When you call generate(), we augment the template variables supplied with
    the current user in the 'user' variable and the current webapp request
    in the 'request' variable.
    """
    def generate(self, template_name, template_values={}):
        values = {
        #'archiveList': util.getArchiveList(),
        }
        values.update(template_values)
        view.ViewPage(cache_time=0).render(self, template_name, values)

class NotFoundHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        view.ViewPage(cache_time=36000).render(self,"notfound.html")

class UnauthorizedHandler(webapp.RequestHandler):
    def get(self):
        self.error(403)
        view.ViewPage(cache_time=36000).render(self,"unauthorized.html")

class MainPage(BaseRequestHandler):
    @authorized.role("admin")
    def get(self):
        user = users.get_current_user()
        template_values = {
        }
        self.generate('deals.html',template_values)

class GetDealsJob(BaseRequestHandler):
    def get(self):
        #if self.get("X-AppEngine-Cron")=="true":
        dealsea_page = urlfetch.fetch(
            url="http://www.dealsea.com",
            method=urlfetch.GET,
            headers={'Content-Type': 'text/html; charset=UTF-8'}
        )
        if dealsea_page.status_code == 200:
            dealsea_soup = BeautifulSoup(dealsea_page.content)
            deals_div = dealsea_soup("div",class="dealbox")
        return True;

