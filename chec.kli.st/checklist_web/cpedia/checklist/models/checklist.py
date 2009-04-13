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

from cpedia.checklist import models

class User(models.SerializableModel):
    user = db.UserProperty(required=True)
    date_joined = db.DateTimeProperty(auto_now_add=True)
    checklists_count = db.IntegerProperty(default=0)
    starred_checklists_count = db.IntegerProperty(default=0)
    public_checklists_count = db.IntegerProperty(default=0)

    def put(self):
        memcache.delete("user_"+self.user.email())
        super(User, self).put()

class Tag(models.SerializableModel):
    user = db.UserProperty(required=True)
    tag = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    valid = db.BooleanProperty(default = True)

    def put(self):
        memcache.delete("tag_"+str(self.user.email())) 
        super(Tag, self).put()

class Tagable(models.MemcachedModel):
    tags = db.ListProperty(db.Category)

    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([urllib.unquote(tag.encode('utf8')) for tag in self.tags])

    def set_tags(self, tags):
        if tags:
            self.tags = [db.Category(urllib.quote(tag.strip().encode('utf8'))) for tag in tags.split(',') if tag.strip()!='']

    tags_commas = property(get_tags,set_tags)

class Checklist(Tagable):
    name = db.StringProperty(multiline=False)
    description = db.StringProperty()
    show_item_number = db.BooleanProperty(default = True)
    strikeout_checked_item = db.BooleanProperty(default = True)
    auto_check_parent_item = db.BooleanProperty(default = True)
    color_for_checked_item = db.StringProperty()
    color_for_starred_item = db.StringProperty()


#system reserved checklist templates. Administrator can maintain these templates,
#user can create a checklist from the template.
class ChecklistTemplate(Checklist):
    querys = {
        "active_templates": 'select * from ChecklistTemplate WHERE active = TRUE ORDER BY order ASC',
    }
    user = db.UserProperty(required=True)
    order = db.IntegerProperty(default=0)
    active = db.BooleanProperty(default = False)
    created_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_user = db.UserProperty()


class ChecklistColumnTemplate(Tagable):
    name = db.StringProperty(multiline=False)
    type = db.StringProperty(multiline=False,default='String',choices=[
            'Checkbox','String','Category','Number','Yes/No','Date'])
    order = db.IntegerProperty(default=0)
    checklist_template = db.ReferenceProperty(ChecklistTemplate)

class UserChecklist(Checklist):
    page_querys = {
        "user_checklist": 'select * from UserChecklist WHERE user=:1 ORDER BY last_updated_date desc',
        "user_starred_checklist": 'select * from UserChecklist WHERE user=:1 and starred = TRUE ORDER BY last_updated_date desc',
        "user_public_checklist": 'select * from UserChecklist WHERE user=:1 and public =TRUE ORDER BY last_updated_date desc',
        "user_tag_checklist": 'select * from UserChecklist WHERE user=:1 and tags=:2 ORDER BY last_updated_date desc',
    }
    
    user = db.UserProperty(required=True)
    starred = db.BooleanProperty(default = False)
    public = db.BooleanProperty(default = False)
    created_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_user = db.UserProperty()

    def update_user(self,update):
        """Update User info"""
        users = User.all().filter('user',self.user).fetch(10)
        if users == []:
            usernew = User(user=self.user,checklists_count=1)
            if self.public is True:
                usernew.public_checklists_count=1
            if self.starred is True:
                usernew.starred_checklists_count=1
            usernew.put()
        else:
            if not update:
                users[0].checklists_count+=1
                if self.public is True:
                    users[0].public_checklists_count+=1
                if self.starred is True:
                    users[0].starred_checklists_count+=1
                users[0].put()

    def update_tags(self,update):
        """Update Tag cloud info"""
        if self.tags:
            for tag_ in self.tags:
                #tag_ = tag.encode('utf8')
                tags = Tag.all().filter('tag',tag_).filter('user',self.user).fetch(10)
                if tags == []:
                    tagnew = Tag(tag=tag_,user=self.user,entrycount=1)
                    tagnew.put()
                else:
                    memcache.delete(self.__class__.__name__+"_page_"+"user_tag_checklist"+"_"+str(self.user.email())+"_"+tag_)                    
                    if not update:
                        tags[0].entrycount+=1
                        tags[0].put()

    def save(self):
        self.update_user(False)
        self.update_tags(False)
        self.last_updated_user = self.user
        self.put()

    def update(self):
        self.update_user(True)
        self.update_tags(True)
        self.put()

    #if a checklist is already starred, then the starred method should not be called.
    def starred(self):
        self.starred = True
        users = User.all().filter('user',self.user).fetch(10)
        if users != []:
            users[0].starred_checklists_count+=1
            users[0].put()
        self.put()

    def unstarred(self):
        self.starred = False
        users = User.all().filter('user',self.user).fetch(10)
        if users != []:
            users[0].starred_checklists_count-=1
            users[0].put()
        self.put()

    #if a checklist is already public, then the starred method should not be called.
    def public(self):
        self.public = True
        users = User.all().filter('user',self.user).fetch(10)
        if users != []:
            users[0].public_checklists_count+=1
            users[0].put()
        self.put()

    def unpublic(self):
        self.public = False
        users = User.all().filter('user',self.user).fetch(10)
        if users != []:
            users[0].public_checklists_count-=1
            users[0].put()
        self.put()


    def delete(self):
        users = User.all().filter('user',self.user).fetch(10)
        if users == []:
            pass
        else:
            users[0].checklists_count-=1
            users[0].put()
        if self.tags:
            for tag_ in self.tags:
                #tag_ = tag.encode('utf8')
                tags = Tag.all().filter('tag',tag_).filter('user',self.user).fetch(10)
                if tags == []:
                    pass
                else:
                    #The only case to update a tag. The tag can not be deleted.
                    memcache.delete(self.__class__.__name__+"_page_"+"user_tag_checklist"+"_"+str(self.user.email())+"_"+tag_)
                    tags[0].entrycount-=1
                    tags[0].put()
        super(UserChecklist, self).delete()



class ChecklistColumn(Tagable):
    name = db.StringProperty(multiline=False)
    type = db.StringProperty(multiline=False,default='String',choices=[
            'Checkbox','String','Category','Number','Yes/No','Date'])
    order = db.IntegerProperty(default=0)
    checklist = db.ReferenceProperty(Checklist)

    def delete(self):
        self.update_checklist_items()
        super(ChecklistColumn, self).delete()

    def update_checklist_items(self):
        def delete_column_for_items():
            for item in self.checklist.checklistitem_set:
                if self.name in item.dynamic_properties:
                    del item.name
        try:
            db.run_in_transaction(delete_column_for_items)
        except db.TransactionFailedError():
            logging.error("Delete column  (%s) for checklist (%s) error.",
                          self.name, self.checklist.name)

class ChecklistItem(db.Expando):
    checklist = db.ReferenceProperty(UserChecklist)
    order = db.IntegerProperty(default=0)
    created_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_user = db.UserProperty()
    starred = db.BooleanProperty(default = False)
    parent_checklist_item = db.SelfReferenceProperty()

class ChecklistColumnCategory(db.Model):
    name = db.StringProperty(multiline=False)
    user = db.UserProperty(required=True)
    categorys = db.ListProperty(db.Category)

class Comment(polymodel.PolyModel):
    last_updated_date = db.DateTimeProperty(auto_now_add=True)
    last_updated_user = db.UserProperty()
    starred = db.BooleanProperty(default = False)

class AuthSubStoredToken(db.Model):
    user_email = db.StringProperty(required=True)
    target_service = db.StringProperty(multiline=False,default='base',choices=[
            'apps','base','blogger','calendar','codesearch','contacts','docs',
            'albums','spreadsheet','youtube'])
    session_token = db.StringProperty(required=True)

