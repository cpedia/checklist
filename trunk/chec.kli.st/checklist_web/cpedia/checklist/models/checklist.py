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
from google.appengine.ext import search
import logging
import datetime
import urllib
import cgi
import simplejson


class User(db.Model):
    user_email = db.StringProperty(required=True)
    
class Checklist(db.Model):
    name = db.StringProperty(multiline=False)

class AuthSubStoredToken(db.Model):
    user_email = db.StringProperty(required=True)
    target_service = db.StringProperty(multiline=False,default='base',choices=[
          'apps','base','blogger','calendar','codesearch','contacts','docs',
          'albums','spreadsheet','youtube'])
    session_token = db.StringProperty(required=True)

