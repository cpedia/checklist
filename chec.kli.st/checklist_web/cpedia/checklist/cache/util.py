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
    user_obj = getUser(user)
    count = user_obj.checklists_count
    return models.UserChecklist.get_cached_page(key_,page,checklist_num_per_page,count,params=[user.user_id()])

#get user's checklists pagination. Cached.
def getUserStarredChecklistPagination(user,page,checklist_num_per_page):
    key_ = "user_starred_checklist"
    user_obj = getUser(user)
    count = user_obj.starred_checklists_count
    return models.UserChecklist.get_cached_page(key_,page,checklist_num_per_page,count,params=[user.user_id()])

#get user's checklists pagination. Cached.
def getUserPublicChecklistPagination(user,page,checklist_num_per_page):
    key_ = "user_public_checklist"
    user_obj = getUser(user)
    count = user_obj.public_checklists_count
    return models.UserChecklist.get_cached_page(key_,page,checklist_num_per_page,count,params=[user.user_id()])

#get user's checklists pagination by Tag. Cached.
def getUserTagChecklistPagination(user,tag,page,checklist_num_per_page):
    key_ = "user_tag_checklist"
    #todo: we assue the user will not have more than 1000 checklists for one tag, so we don't pass the count parameter.
    return models.UserChecklist.get_cached_page(key_,page,checklist_num_per_page,params=[user.user_id(),tag])

def getUser(user_,nocache=False):
    key_ = "user_"+user_.user_id()
    try:
        user = memcache.get(key_)
    except Exception:
        user = None
    if nocache or user is None:
        user = models.User.gql('WHERE user.user_id=:1',user_.user_id()).get()
        if user is None:
            usernew = models.User(user=user_)
            usernew.put()
            user = usernew
        memcache.add(key=key_, value=user)
    else:
        logging.debug("getUser from cache.")
    return user


def get_user_tags(user_,nocache=False):
    if user_ is not None:
        key_ = "tag_"+user_.user_id()
        try:
            tags = memcache.get(key_)
        except Exception:
            tags = None
        if nocache or tags is None:
            tags = models.Tag.gql('WHERE user.user_id=:1 ORDER BY entrycount desc',user_.user_id()).fetch(1000)
            memcache.add(key=key_, value=tags)
        else:
            logging.debug("get_user_tags from cache.")
        return tags
    return None
