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

    @authorized.role('admin')
    def saveTemplate(self,request):
        checklistTemplate = datastore.Entity("ChecklistTemplate")
        checklistTemplate["user_email"] = users.get_current_user().email()
        checklistTemplate["name"] = ""
        checklistTemplate["description"] = ""
        datastore.Put(checklistTemplate)
        util.flushMenuList()
        checklistTemplate['key'] = str(models.checklistTemplate.key())
        checklistTemplate['id'] = str(models.checklistTemplate.key().id())
        return checklistTemplate


      

