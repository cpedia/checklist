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


import pickle

from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from google.appengine.ext import search
import logging
import datetime
import urllib
import cgi
import simplejson


class User(db.Model):
    user_email = db.StringProperty(required=True)

class Tag(db.Model):
    tag = db.StringProperty(multiline=False)
    entrycount = db.IntegerProperty(default=0)
    valid = db.BooleanProperty(default = True)

class Tagable(polymodel.PolyModel):
    tags = db.ListProperty(db.Category)

    def get_tags(self):
        '''comma delimted list of tags'''
        return ','.join([urllib.unquote(tag.encode('utf8')) for tag in self.tags])

    def set_tags(self, tags):
        if tags:
            self.tags = [db.Category(urllib.quote(tag.strip().encode('utf8'))) for tag in tags.split(',')]

    tags_commas = property(get_tags,set_tags)


class Checklist(Tagable):
    name = db.StringProperty(multiline=False)

class ChecklistTemplate(Tagable):
    name = db.StringProperty(multiline=False)
    description = db.StringProperty()
    owner = db.StringProperty()
 
class AuthSubStoredToken(db.Model):
    user_email = db.StringProperty(required=True)
    target_service = db.StringProperty(multiline=False,default='base',choices=[
          'apps','base','blogger','calendar','codesearch','contacts','docs',
          'albums','spreadsheet','youtube'])
    session_token = db.StringProperty(required=True)

