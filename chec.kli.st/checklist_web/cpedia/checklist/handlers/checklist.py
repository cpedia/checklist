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
import config

from cpedia.checklist import cache_manager

querys = {
   "active_checklist": models.ChecklistTemplate.gql('WHERE active =:1 ORDER BY order ASC',True),
   "active_templates": "", 
}

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
        pageStr = self.request.get('page')
        if pageStr:
            page = int(pageStr)
        else:
            page = 1;
        checklist_num_per_page_ = self.request.get('checklist_num_per_page')
        if checklist_num_per_page_:
            checklist_num_per_page = int(checklist_num_per_page_)
        else:
            checklist_num_per_page = config.CHECKLIST["checklist_num_per_page"];

        checklist_page = cache_manager.getUserChecklistPagination(user,page,checklist_num_per_page)
        template_values = {
        "checklist_page":checklist_page,
        }
        self.generate('checklist_main.html',template_values)

class UserChecklistPage(BaseRequestHandler):
    @authorized.role("user")
    def get(self):
        template_values = {
         }
        self.generate('checklists.html',template_values)

class UserPublicChecklistPage(BaseRequestHandler):
    @authorized.role("user")
    def get(self,user_key):
        if user_key is None:
            user = users.get_current_user()
        else:
            user = models.User.get(user_key).user
        pageStr = self.request.get('page')
        if pageStr:
            page = int(pageStr)
        else:
            page = 1;
        checklist_num_per_page_ = self.request.get('checklist_num_per_page')
        if checklist_num_per_page_:
            checklist_num_per_page = int(checklist_num_per_page_)
        else:
            checklist_num_per_page = config.CHECKLIST["checklist_num_per_page"];

        checklist_page = cache_manager.getUserPublicChecklistPagination(user,page,checklist_num_per_page)
        template_values = {
        "checklist_page":checklist_page,
        }
        self.generate('checklist_main.html',template_values)

class UserStarredChecklistPage(BaseRequestHandler):
    @authorized.role("user")
    def get(self):
        user = users.get_current_user()
        pageStr = self.request.get('page')
        if pageStr:
            page = int(pageStr)
        else:
            page = 1;
        checklist_num_per_page_ = self.request.get('checklist_num_per_page')
        if checklist_num_per_page_:
            checklist_num_per_page = int(checklist_num_per_page_)
        else:
            checklist_num_per_page = config.CHECKLIST["checklist_num_per_page"];
        checklist_page = cache_manager.getUserStarredChecklistPagination(user,page,checklist_num_per_page)
        template_values = {
        "checklist_page":checklist_page,
        }
        self.generate('checklist_main.html',template_values)

class UserChecklist(BaseRequestHandler):
    @authorized.role("user")
    def get(self,checklist_key):

        template_values = {
        }
        self.generate('checklist_main.html',template_values)

class CreateList(BaseRequestHandler):
    @authorized.role("user")
    def get(self):
        query = models.ChecklistTemplate.gql('WHERE active =:1 ORDER BY order ASC',True)
        templates = models.ChecklistTemplate.get_cached_list(models.ChecklistTemplate.__name__,query)
        template_values = {
        "checklist_templates":templates,
        }
        self.generate('checklist_info.html',template_values)

    @authorized.role("user")
    def post(self):
        checklist = models.UserChecklist(user=users.get_current_user())
        checklist.name = self.request.get('checklistName')
        checklist.description = self.request.get('description')
        checklist.tags_commas = self.request.get('tags')
        checklist.last_updated_user = users.get_current_user()
        checklist.put()
        columns = self.request.get('checklist_columns')
        checklist_columns = simplejson.loads(columns)
        for column in checklist_columns:
            checklist_column = models.ChecklistColumn()
            checklist_column.name = column['name']
            checklist_column.type = column['type']
            checklist_column.order = column['order']
            checklist_column.checklist = checklist
            checklist_column.put()
        self.redirect('/list')

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

class ChecklistEditAdmin(BaseRequestHandler):
    @authorized.role("user")
    def get(self,checklistKey):
        checklist = models.UserChecklist.get_cached(checklistKey)
        checklist_columns = checklist.checklistcolumn_set
        columns = []
        for column in checklist_columns:
            columns +=[column.to_json()]
        query = models.ChecklistTemplate.gql('WHERE active =:1 ORDER BY order ASC',True)
        templates = models.ChecklistTemplate.get_cached_list(models.ChecklistTemplate.__name__,query)
        template_values = {
        "templates":templates,
        "checklist":checklist,
        "checklist_columns":simplejson.dumps(columns),
        }
        self.generate('checklist_info.html',template_values)

    @authorized.role("user")
    def post(self,checklistKey):
        checklist = models.UserChecklist.get_cached(checklistKey)
        checklist.name = self.request.get('checklistName')
        checklist.description = self.request.get('description')
        checklist.tags_commas = self.request.get('tags')
        checklist.last_updated_date = datetime.datetime.now()
        checklist.last_updated_user = users.get_current_user()

        checklist_columns = checklist.checklistcolumn_set
        for column in checklist_columns:
            column.delete()
        checklist.put()

        columns = self.request.get('checklist_columns')
        checklist_columns = simplejson.loads(columns)
        for column in checklist_columns:
            checklist_column = models.ChecklistColumnTemplate()
            checklist_column.name = column['name']
            checklist_column.type = column['type']
            checklist_column.order = column['order']
            checklist_column.checklist_template = checklist
            checklist_column.put()
        query = models.ChecklistTemplate.gql('WHERE active =:1 ORDER BY order ASC',True)
        templates = models.ChecklistTemplate.get_cached_list(models.ChecklistTemplate.__name__,query)
        template_values = {
        "templates":templates,
        "checklist":checklist,
        "checklist_columns":simplejson.dumps(columns),
        }
        self.redirect('/list')

