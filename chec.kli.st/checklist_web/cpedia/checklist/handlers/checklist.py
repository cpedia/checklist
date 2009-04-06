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
import cpedia.checklist.models.checklist as models

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
        user = users.get_current_user()
        checklists = db.Query("select * from UserChecklist where user = :1",user)
        pageStr = self.request.get('page')
        if pageStr:
            page = int(pageStr)
        else:
            page = 1;

        #get blog pagination from cache.
        obj_page = util.getBlogPagination(page)
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
        checklist_template = models.ChecklistTemplate()
        checklist_template.name = self.request.get('templateName')
        checklist_template.description = self.request.get('description')
        checklist_template.user = users.get_current_user()
        checklist_template.last_updated_user = users.get_current_user()
        checklist_template.put()
        columns = self.request.get('template_columns')
        template_columns = simplejson.loads(columns)
        for column in template_columns:
            template_column = models.ChecklistColumnTemplate()
            template_column.name = column['name']
            template_column.type = column['type']
            template_column.order = column['order']
            template_column.checklist_template = checklist_template
            template_column.put()
        self.redirect('/admin/templates')

class TemplateEditAdmin(BaseRequestHandler):
    @authorized.role("admin")
    def get(self,templateKey):
        template = models.ChecklistTemplate.get(templateKey)
        template_columns = template.checklistcolumntemplate_set
        columns = []
        for column in template_columns:
            columns +=[column.to_json()]
        template_values = {
            "template":template,
            "template_columns":simplejson.dumps(columns),
        }
        self.generate('template_info.html',template_values)

    @authorized.role("admin")
    def post(self,templateKey):
        checklist_template = models.ChecklistTemplate.get(templateKey)
        checklist_template.name = self.request.get('templateName')
        checklist_template.description = self.request.get('description')
        checklist_template.last_updated_date = datetime.datetime.now()
        checklist_template.last_updated_user = users.get_current_user()

        template_columns = checklist_template.checklistcolumntemplate_set
        for column in template_columns:
            column.delete()
        checklist_template.put()

        columns = self.request.get('template_columns')
        template_columns = simplejson.loads(columns)
        for column in template_columns:
            template_column = models.ChecklistColumnTemplate()
            template_column.name = column['name']
            template_column.type = column['type']
            template_column.order = column['order']
            template_column.checklist_template = checklist_template
            template_column.put()

        template_values = {
            "template":template,
            "template_columns":simplejson.dumps(columns),
        }
        self.redirect('/admin/templates')

