# !/usr/bin/env python
#
# Copyright 2009 CPedia.com.
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

import pickle

from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.ext import search
from google.appengine.api import memcache
import logging
import datetime
import urllib
import cgi
import simplejson

import config

from cpedia.deal import models

class User(models.SerializableModel):
    user = db.UserProperty(required=True)
    user_id = db.StringProperty(multiline=False)
    date_joined = db.DateTimeProperty(auto_now_add=True)
    last_syn_time = db.DateTimeProperty()

    def put(self):
        memcache.delete("user_"+self.user.user_id())
        self.user_id = self.user.user_id()
        super(User, self).put()

class Tag(models.SerializableModel):
    user = db.UserProperty(required=True)
    user_id = db.StringProperty(multiline=False)
    tag = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    valid = db.BooleanProperty(default = True)

    def put(self):
        memcache.delete("tag_"+str(self.user.email()))
        self.user_id = self.user.user_id()
        super(Tag, self).put()

class Tagable(models.MemcachedModel):
    tags = db.ListProperty(db.Category)

    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([urllib.unquote(tag.encode('utf8')) for tag in self.tags])

    def set_tags(self, tags):
        if tags:
            self.tags = [db.Category(urllib.quote(tag.strip().encode('utf8'))) for tag in tags.split(',') if
                         tag.strip()!='']

    tags_commas = property(get_tags,set_tags)

class Deals(models.MemcachedModel):
    vendor = db.StringProperty(multiline=False)
    title = db.StringProperty()
    content = db.TextProperty()
    image = db.StringProperty()
    pub_date = db.StringProperty() #pub date from vendor. '%b %d %Y'
    expired = db.BooleanProperty(default = False)
    created_date_str = db.StringProperty()
    created_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_date = db.DateTimeProperty(auto_now=True)
    last_updated_user = db.UserProperty(auto_current_user=True)

    def put(self):
        date_ = self.created_date.strftime('%b %d %Y') # July 2008
        self.created_date_str = date_
        super(Deals, self).put()

class Coupons(models.MemcachedModel):
    vendor = db.StringProperty(multiline=False)
    coupon_id = db.StringProperty(multiline=False) #Coupon Id from retailmenot.com
    site_id = db.StringProperty(multiline=False) #Site Id from retailmenot.com
    code = db.StringProperty()
    discount = db.TextProperty()
    site_name = db.StringProperty()
    site_url = db.StringProperty()
    image = db.StringProperty()
    pub_date = db.StringProperty() #pub date from created_date. '%b %d %Y'
    expired = db.BooleanProperty(default = False)
    created_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_date = db.DateTimeProperty(auto_now=True)
    last_updated_user = db.UserProperty(auto_current_user=True)

    def put(self):
        date_ = self.created_date.strftime('%b %d %Y') # July 2008
        self.pub_date = date_
        super(Coupons, self).put()

class Comment(models.MemcachedModel):
    user = db.UserProperty(required=True,auto_current_user_add=True)
    user_id = db.StringProperty(multiline=False)
    content = db.StringProperty()
    created_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_date = db.DateTimeProperty(auto_now=True)
    last_updated_user = db.UserProperty()

    def put(self):
        self.user_id = self.user.user_id()
        super(Comment, self).put()

class DealComment(Comment):
    deal = db.ReferenceProperty(Deals)

class CouponComment(Comment):
    rate = db.BooleanProperty()  #Rate for the coupon. True/False.
    coupon = db.ReferenceProperty(Coupons)

class AuthSubStoredToken(db.Model):
    user_email = db.StringProperty(required=True)
    target_service = db.StringProperty(multiline=False,default='base',choices=[
            'apps','base','blogger','calendar','codesearch','contacts','docs',
            'albums','spreadsheet','youtube'])
    session_token = db.StringProperty(required=True)

