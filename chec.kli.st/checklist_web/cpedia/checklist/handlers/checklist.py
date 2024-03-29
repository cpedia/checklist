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

import cpedia.checklist.cache.util as cache_util


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

        checklist_page = cache_util.getUserChecklistPagination(user,page,checklist_num_per_page)
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

        checklist_page = cache_util.getUserPublicChecklistPagination(user,page,checklist_num_per_page)
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
        checklist_page = cache_util.getUserStarredChecklistPagination(user,page,checklist_num_per_page)
        template_values = {
        "checklist_page":checklist_page,
        }
        self.generate('checklist_main.html',template_values)

class UserChecklist(BaseRequestHandler):
    @authorized.role("user")
    def get(self,checklistKey):
        checklist = models.UserChecklist.get_cached(checklistKey)
        checklist_columns = checklist.checklistcolumn_set
        checklist_items = checklist.checklistitem_set
        items = []
        for item in checklist_items:
            items +=[item.to_json()]
        template_values = {
        "checklist":checklist,
        "checklist_columns":checklist_columns,
        "checklist_items":simplejson.dumps(items),
        }
        self.generate('checklist_items.html',template_values)

class PrintChecklist(BaseRequestHandler):
    @authorized.role("user")
    def get(self,checklistKey):
        checklist = models.UserChecklist.get_cached(checklistKey)
        checklist_columns = checklist.checklistcolumn_set
        #checklist_items = checklist.checklistitem_set
        checklist_item_groups = db.GqlQuery('select * from ChecklistItem where is_item_group=:1 and checklist=:2',True,
                                            checklist).fetch(1000)
#        groups = []
#        for group in checklist_item_groups:
#            items = []
#            for item in group.sub_checklist_item_set:
#                items+=[item.to_json()]
#            groups+=[{"group":group,"items":items}]
        template_values = {
        "checklist":checklist,
        "checklist_columns":checklist_columns,
        "checklist_item_groups":checklist_item_groups,
        }
        self.generate('checklist_print.html',template_values)

#create a checklist by login user.
class CreateList(BaseRequestHandler):
    @authorized.role("user")
    def get(self):
        templates = models.ChecklistTemplate.get_cached_list("active_templates")
        template_values = {
        "checklist_templates":templates,
        }
        self.generate('checklist_detail.html',template_values)

    @authorized.role("user")
    def post(self):
        checklist = models.UserChecklist(user=users.get_current_user())
        checklist.name = self.request.get('checklistName')
        checklist.description = self.request.get('description')
        checklist.tags_commas = self.request.get('tags')
        checklist.save()
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

#edit a checklist by login user.
class ChecklistEditAdmin(BaseRequestHandler):
    @authorized.role("user")
    def get(self,checklistKey):
        checklist = models.UserChecklist.get_cached(checklistKey)
        checklist_columns = checklist.checklistcolumn_set
        columns = []
        for column in checklist_columns:
            columns +=[column.to_json()]
        templates = models.ChecklistTemplate.get_cached_list("active_templates")
        template_values = {
        "templates":templates,
        "checklist":checklist,
        "checklist_columns":simplejson.dumps(columns),
        }
        self.generate('checklist_info.html',template_values)

    @authorized.role("user")
    def post(self,checklistKey):
        checklist = models.UserChecklist.get_cached(checklistKey)
        if checklist is not None and checklist.user.user_id() != users.get_current_user().user_id():
            self.redirect('/403.html')
        checklist.name = self.request.get('checklistName')
        checklist.description = self.request.get('description')
        checklist.tags_commas = self.request.get('tags')

        checklist_columns = checklist.checklistcolumn_set
        for column in checklist_columns:
            column.delete()
        checklist.update()

        columns = self.request.get('checklist_columns')
        checklist_columns = simplejson.loads(columns)
        for column in checklist_columns:
            checklist_column = models.ChecklistColumnTemplate()
            checklist_column.name = column['name']
            checklist_column.type = column['type']
            checklist_column.order = column['order']
            checklist_column.checklist_template = checklist
            checklist_column.put()
        templates = models.ChecklistTemplate.get_cached_list("active_templates")
        template_values = {
        "templates":templates,
        "checklist":checklist,
        "checklist_columns":simplejson.dumps(columns),
        }
        self.redirect('/list')

class CreateQucikList(BaseRequestHandler):
    @authorized.role("user")
    def get(self):

        template_values = {
        }
        self.generate('checklist_quick.html',template_values)

    @authorized.role("user")
    def post(self):
        checklist_json = self.request.get('checklist')
        checklist_ = simplejson.loads(checklist_json)
        checklist = models.UserChecklist(user=users.get_current_user())
        checklist.name = checklist_['name']
        checklist.description = checklist_['description']
        checklist.save()
        i=0
        for checklist_item_ in checklist_['checklist_items']:
            i=i+1
            checklist_item = models.ChecklistItem(checklist=checklist)
            checklist_item.item = checklist_item_['item']
            checklist_item.order = i
            checklist_item.is_item_group = True
            checklist_item.checkable = False
            if len(checklist_item_['sub_items'])>0:
                checklist_item.has_sub_checklist_item=True
            checklist_item.put()
            j=0
            for sub_item_ in checklist_item_['sub_items']:
                if sub_item_['item'].strip()!='':
                    j = j+1
                    sub_item = models.ChecklistItem(checklist=checklist,parent_checklist_item=checklist_item)
                    sub_item.item = sub_item_['item']
                    sub_item.order = j
                    sub_item.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(str(checklist.key()))

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
        checklist_template = models.ChecklistTemplate(user=users.get_current_user())
        checklist_template.name = self.request.get('templateName')
        checklist_template.description = self.request.get('description')
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
        template = models.ChecklistTemplate.get_cached(templateKey)
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
        checklist_template = models.ChecklistTemplate.get_cached(templateKey)
        checklist_template.name = self.request.get('templateName')
        checklist_template.description = self.request.get('description')

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

class TagHandler(BaseRequestHandler):
    def get(self, encoded_tag):
        tag = encoded_tag
        template_values = {
          'tag':tag,
          }
        self.generate('checklists_tagged.html',template_values)

