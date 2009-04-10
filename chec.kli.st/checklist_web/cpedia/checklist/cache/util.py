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



#get user's checklists pagination. Cached.
def getUserChecklistPagination(user,page,checklist_num_per_page):
    key_ = "user_checklist"
    email = user.email()
    user_obj = getUser(user)
    count = user_obj.checklists_count
    return models.UserChecklist.get_cached_page(key_,page,checklist_num_per_page,count,params=[email])

#get user's checklists pagination. Cached.
def getUserStarredChecklistPagination(user,page,checklist_num_per_page):
    key_ = "user_starred_checklist"
    email = user.email()
    user_obj = getUser(user)
    count = user_obj.starred_checklists_count
    return models.UserChecklist.get_cached_page(key_,page,checklist_num_per_page,count,params=[email])

#get user's checklists pagination. Cached.
def getUserPublicChecklistPagination(user,page,checklist_num_per_page):
    key_ = "user_public_checklist"
    email = user.email()
    user_obj = getUser(user)
    count = user_obj.public_checklists_count
    return models.UserChecklist.get_cached_page(key_,page,checklist_num_per_page,count,params=[email])

def getUser(user_,nocache=False):
    key_ = "user_"+user_.email()
    try:
        user = memcache.get(key_)
    except Exception:
        user = None
    if nocache or user is None:
        user = models.User.gql('WHERE user=:1',user_).get()
        if user is None:
            usernew = models.User(user=user_)
            usernew.put()
            user = usernew
        memcache.add(key=key_, value=user)
    else:
        logging.debug("getUser from cache.")
    return user