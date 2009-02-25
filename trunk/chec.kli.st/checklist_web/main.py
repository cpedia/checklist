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

import wsgiref.handlers

from google.appengine.ext import webapp

import logging
import os

import rest
import config

from cpedia.checklist.handlers import checklist

from google.appengine.ext.webapp import template
template.register_template_library('cpedia.filter.replace')
template.register_template_library('cpedia.filter.gravatar')

# Force Django to reload its settings.
#from django.conf import settings
#settings._target = None

# Must set this env var before importing any part of Django
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

def main():
    application = webapp.WSGIApplication(
                                       [
                                        ('/403.html', checklist.UnauthorizedHandler),
                                        ('/404.html', checklist.NotFoundHandler),
                                        ('/rest/.*', rest.Dispatcher),
                                        ('/create/list/*$', checklist.CreateList),
                                        ('/create/quicklist/*$', checklist.CreateQucikList),
                                        ('/*$', checklist.MainPage),
                                       ],
                                       debug=config.DEBUG)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
