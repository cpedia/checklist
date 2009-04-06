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
import re
import datetime
import calendar
import logging
import string
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch

from cpedia.pagination.GqlQueryPaginator import GqlQueryPaginator,GqlPage
from cpedia.pagination.paginator import InvalidPage,Paginator

import cpedia.checklist.models.checklist as models

import simplejson
import cgi
import urllib, hashlib

#get user's checklists pagination. Cached.
def getUserChecklistPagination(user,page):
    key_ = "checklist_"+page
    try:
        obj_pages = memcache.get(key_)
    except Exception:
        obj_pages = None
    if obj_pages is None or page not in obj_pages:
        checklist_query = models.UserChecklist.gql('WHERE user=:1 ORDER BY last_updated_date desc',user)
        try:
            obj_page  =  GqlQueryPaginator(checklist_query,page,cpedialog.num_post_per_page).page()
            if obj_pages is None:
                obj_pages = {}
            obj_pages[page] = obj_page
            memcache.add(key=key_, value=obj_pages, time=3600)
        except InvalidPage:
            return None
    else:
        getLogger(__name__).debug("getBlogPagination from cache. ")

    return obj_pages[page]
