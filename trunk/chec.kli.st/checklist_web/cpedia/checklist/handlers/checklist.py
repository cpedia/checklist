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

from cpedia.pagination.GqlQueryPaginator import GqlQueryPaginator,GqlPage
from cpedia.pagination.paginator import InvalidPage,Paginator

from cpedia.checklist.handlers import restful

import simplejson
import authorized
import view

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
        view.ViewPage(cache_time=36000).render(self)

class UnauthorizedHandler(webapp.RequestHandler):
    def get(self):
        self.error(403)
        view.ViewPage(cache_time=36000).render(self)

class MainPage(BaseRequestHandler):
    @authorized.role("user")
    def get(self):

        template_values = {
        }
        self.generate('checklist_main.html',template_values)

class CreateList(BaseRequestHandler):
    @authorized.role("user")
    def get(self):

        template_values = {
        }
        self.generate('checklist_main.html',template_values)

class CreateQucikList(BaseRequestHandler):
    @authorized.role("user")
    def get(self):

        template_values = {
        }
        self.generate('checklist_main.html',template_values)

class TemplateListAdmin(BaseRequestHandler):
    @authorized.role("admin")
    def get(self):

        template_values = {
        }
        self.generate('templates.html',template_values)

class TemplateCreateAdmin(BaseRequestHandler):
    @authorized.role("admin")
    def get(self):
        template_values = {
        }
        self.generate('template_info.html',template_values)

    @authorized.role("admin")
    def post(self):
        name = self.request.get('templateName')
        description = self.request.get('description')
        columns = self.request.get('template_columns')
        self.response.out.write(simplejson.dumps(True))

class TemplateEditAdmin(BaseRequestHandler):
    @authorized.role("admin")
    def get(self):

        template_values = {
        }
        self.generate('template_info.html',template_values)

