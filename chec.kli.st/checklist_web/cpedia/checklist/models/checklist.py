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
import logging
import datetime
import urllib
import cgi
import simplejson

import config

from cpedia.checklist import models

class User(models.SerializableModel):
    user = db.UserProperty()
    date_joined = db.DateTimeProperty(auto_now_add=True)
    checklists_count = db.IntegerProperty(default=0)
    starred_checklists_count = db.IntegerProperty(default=0)
    public_checklists_count = db.IntegerProperty(default=0)

class Tag(models.SerializableModel):
    user = db.UserProperty()
    tag = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    valid = db.BooleanProperty(default = True)

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
    user = db.UserProperty()
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

    def save(self):
        self.update_user(False)
        self.last_updated_user = self.user
        self.put()

    def update(self):
        self.update_user(True)
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
            self.delete()
        else:
            users[0].checklists_count-=1
            users[0].put()


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

