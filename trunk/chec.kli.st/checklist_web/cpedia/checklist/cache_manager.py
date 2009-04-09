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

"""This class used to manager the complex cache objects.
   If we only need simple cache manager, we just extend
   the Model to MemcachedModel
"""

CACHE_TIME = 3600

CACHE_KEY_PREFIX = {
"user_checklist_page":"user_checklist_page_",
"user_starred_checklist_page":"user_starred_checklist_page_",
"user_public_checklist_page":"user_public_checklist_page_",
"user":"user_",
}

def getCachedPagination(key_,query,page,num_per_page,count):
    try:
        obj_pages = memcache.get(key_)
    except Exception:
        obj_pages = None
    if obj_pages is None or page not in obj_pages:
        try:
            obj_page  =  GqlQueryPaginator(query,page,num_per_page,count).page()
            if obj_pages is None:
                obj_pages = {}
            obj_pages[page] = obj_page
            memcache.add(key=key_, value=obj_pages, time=CACHE_TIME)
        except InvalidPage:
            return None
    else:
        logging.debug("cache_manager.getCachedPagination(). key:%s, query:%s, page:%s, num_per_page:%s, count:%s",key_,
                      query,page,num_per_page,count)
    return obj_pages[page]


#get user's checklists pagination. Cached.
def getUserChecklistPagination(user,page,checklist_num_per_page):
    key_ = CACHE_KEY_PREFIX["user_checklist_page"]+user.email()+"_"+str(page)
    checklist_query = models.UserChecklist.gql('WHERE user=:1 ORDER BY last_updated_date desc',user)
    user_obj = getUser(user)
    count = user_obj.checklists_count
    return getCachedPagination(key_,checklist_query,page,checklist_num_per_page,count)

#get user's checklists pagination. Cached.
def getUserStarredChecklistPagination(user,page,checklist_num_per_page):
    key_ = CACHE_KEY_PREFIX["user_starred_checklist_page"]+user.email()+"_"+str(page)
    checklist_query = models.UserChecklist.gql('WHERE user=:1 and starred = TRUE ORDER BY last_updated_date desc',user)
    user_obj = getUser(user)
    count = user_obj.starred_checklists_count
    return getCachedPagination(key_,checklist_query,page,checklist_num_per_page,count)

#get user's checklists pagination. Cached.
def getUserPublicChecklistPagination(user,page,checklist_num_per_page):
    key_ = CACHE_KEY_PREFIX["user_public_checklist_page"]+user.email()+"_"+str(page)
    checklist_query = models.UserChecklist.gql('WHERE user=:1 and public =TRUE ORDER BY last_updated_date desc',user)
    user_obj = getUser(user)
    count = user_obj.public_checklists_count
    return getCachedPagination(key_,checklist_query,page,checklist_num_per_page,count)

def getUser(user_):
    key_ = CACHE_KEY_PREFIX["user"]+user_.email()
    try:
        user = memcache.get(key_)
    except Exception:
        user = None
    if user is None:
        user = models.User.gql('WHERE user=:1',user).get()
        if user is None:
            usernew = models.User(user=user_)
            usernew.put()
            user = usernew
        memcache.add(key=key_, value=usernew, time=CACHE_TIME)
    else:
        logging.debug("getUser from cache.")
    return user