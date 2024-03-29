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
import logging
import datetime
import simplejson
import wsgiref.handlers

from google.appengine.api import datastore
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.ext import db

import cpedia.checklist.models.checklist as models
import authorized
import config
import cpedia.checklist.cache.util as cache_util


# This handler allows the functions defined in the RPCHandler class to
# be called automatically by remote code.
class RPCHandler(webapp.RequestHandler):
    def get(self,action):
        arg_counter = 0;
        args = []
        while True:
            arg = self.request.get('arg' + str(arg_counter))
            arg_counter += 1
            if arg:
                args += (simplejson.loads(arg),);
            else:
                break;
        result = getattr(self, action)(*args)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps((result)))

    def post(self,action):
        request_ = self.request
        result = getattr(self, action)(request_)
        logging.debug('ajax action "%s" return value is %s', action,simplejson.dumps(result))
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps((result)))

    # The RPCs exported to JavaScript follow here:

    #get checklist template list.
    @authorized.role('admin')
    def getTemplates(self,startIndex,results):
        query = db.Query(models.ChecklistTemplate)
        query.order('-last_updated_date')
        templates = []
        for template in query.fetch(results,startIndex):
            templates+=[template.to_json()]
        totalRecords = query.count()
        returnValue = {"records":templates,"totalRecords":totalRecords,"startIndex":startIndex}
        return returnValue

    #get template.
    def getTemplate(self,request):
        template_key = request.get("template_key")
        template = models.ChecklistTemplate.get_cached(template_key)
        columns = []
        for column in template.checklistcolumntemplate_set:
            columns+=[column.to_json()]
        returnValue = {"columns":columns,"template":template.to_json()}
        return returnValue

    @authorized.role('admin')
    def deleteTemplates(self,request):
        template_keys = request.get("template_keys")
        templates =  models.ChecklistTemplate.get(template_keys.split(","))
        for template in templates:
            template_columns = template.checklistcolumntemplate_set
            for column in template_columns:
                column.delete()
            template.delete()   
        return True

    @authorized.role('admin')
    def publishTemplates(self,request):
        template_keys = request.get("template_keys")
        templates =  models.ChecklistTemplate.get(template_keys.split(","))
        for template in templates:
            template.active = True
            template.last_updated_date = datetime.datetime.now()
            template.last_updated_user = users.get_current_user()
            template.put()
        return True

    @authorized.role('admin')
    def holdTemplates(self,request):
        template_keys = request.get("template_keys")
        templates =  models.ChecklistTemplate.get(template_keys.split(","))
        for template in templates:
            template.active = False
            template.last_updated_date = datetime.datetime.now()
            template.last_updated_user = users.get_current_user()
            template.put()
        return True

    #get checklist.
    def getChecklist(self,request):
        checklist_key = request.get("checklist_key")
        checklist = models.UserChecklist.get_cached(checklist_key)
        columns = []
        for column in checklist.checklistcolumn_set:
            columns+=[column.to_json()]
        returnValue = {"columns":columns,"checklist":checklist.to_json()}
        return returnValue

    @authorized.role('user')
    def deleteChecklists(self,request):
        checklist_keys = request.get("checklist_keys")
        checklists =  models.UserChecklist.get(checklist_keys.split(","))
        for checklist in checklists:
            checklist_columns = checklist.checklistcolumn_set
            for column in checklist_columns:
                column.delete()
            checklist_items = checklist.checklistitem_set
            for item in checklist_items:
                item.delete()
            checklist.delete()
        return True


    #get checklist template list.
    @authorized.role('admin')
    def getUserChecklists(self,startIndex,checklist_num_per_page):
        user = users.get_current_user()
        page = startIndex +1
        #get checklist pagination from cache.
        checklist_page = cache_util.getUserChecklistPagination(user,page,checklist_num_per_page)
        checklists = []
        totalRecords = 0
        if checklist_page is not None:
            for checklist in checklist_page.object_list:
                checklists+=[checklist.to_json()]
            totalRecords = checklist_page.paginator.count
        returnValue = {"records":checklists,"totalRecords":totalRecords,"startIndex":startIndex}
        return returnValue

    #get taged checklist list.
    @authorized.role('user')
    def getUserTagChecklists(self,tag,startIndex,checklist_num_per_page):
        user = users.get_current_user()
        page = startIndex +1
        tag = tag.replace("\"","")
        #get checklist pagination from cache.
        checklist_page = cache_util.getUserTagChecklistPagination(user,tag,page,checklist_num_per_page)
        checklists = []
        totalRecords = 0
        if checklist_page is not None:
            for checklist in checklist_page.object_list:
                checklists+=[checklist.to_json()]
            totalRecords = checklist_page.paginator.count
        returnValue = {"records":checklists,"totalRecords":totalRecords,"startIndex":startIndex}
        return returnValue


