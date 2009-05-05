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

import cpedia.deal.models.deal as models
import authorized
import config


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
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(simplejson.dumps((result)))

    # The RPCs exported to JavaScript follow here:

    #get checklist template list.
    @authorized.role('admin')
    def getDeals(self,startIndex,results):
        query = db.Query(models.Deals)
        query.order('-pub_date')
        deals = []
        for deal in query.fetch(results,startIndex):
            deals+=[deal.to_json()]
        totalRecords = query.count()
        returnValue = {"records":deals,"totalRecords":totalRecords,"startIndex":startIndex}
        return returnValue

    #get checklist template list.
    @authorized.role('admin')
    def getLatestDeals(self,results,startIndex):
        current_date = datetime.datetime.now().strftime('%b %d %Y')
        query = db.Query(models.Deals)
        query.filter("pub_date",current_date)
        query.order('-created_date')
        deals = []
        for deal in query.fetch(results,startIndex):
            deals+=[deal.to_json()]
        totalRecords = query.count()
        returnValue = {"records":deals,"totalRecords":totalRecords,"startIndex":startIndex}
        return returnValue

    @authorized.role('admin')
    def deleteDeals(self,request):
        deal_keys = request.get("deal_keys")
        deals =  models.Deals.get(deal_keys.split(","))
        for deal in deals:
            deal_comments = deal.comment_set
            for comment in deal_comments:
                comment.delete()
            deal.delete()
        return True


