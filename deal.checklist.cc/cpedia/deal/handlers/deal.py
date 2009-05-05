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

import cgi
import wsgiref.handlers
import os
import re
import datetime
import calendar
import logging
import string
import urllib

from xml.etree import ElementTree

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext import search
from google.appengine.api import images

from cpedia.deal.handlers import restful
import cpedia.deal.models.deal as models

import simplejson
import authorized
import view
import config

import sys
import urllib
from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup

class BaseRequestHandler(webapp.RequestHandler):
    """Supplies a common template generation function.

    When you call generate(), we augment the template variables supplied with
    the current user in the 'user' variable and the current webapp request
    in the 'request' variable.
    """
    def generate(self, template_name, template_values={}):
        values = {
        #'archiveList': util.getArchiveList(),
        }
        values.update(template_values)
        view.ViewPage(cache_time=0).render(self, template_name, values)

class NotFoundHandler(webapp.RequestHandler):
    def get(self):
        self.error(404)
        view.ViewPage(cache_time=36000).render(self,"notfound.html")

class UnauthorizedHandler(webapp.RequestHandler):
    def get(self):
        self.error(403)
        view.ViewPage(cache_time=36000).render(self,"unauthorized.html")

class MainPage(BaseRequestHandler):
    @authorized.role("admin")
    def get(self):
        user = users.get_current_user()
        template_values = {
        }
        self.generate('deals.html',template_values)

class DeleteDealsJob(BaseRequestHandler):
    def get(self):
        current_date = datetime.datetime.now().strftime('%b %d %Y')
        query = db.Query(models.Deals)
        query.filter("pub_date",current_date)
        query.order('-created_date')
        deals = []
        for deal in query.fetch(1000):
            deal.delete()
        self.response.out.write("Purge today's deal successfully.")                   

    def post(self):
         self.get()

class GetDealsJob(BaseRequestHandler):
    def get(self):
    #if self.get("X-AppEngine-Cron")=="true":
        dealsea_page = urlfetch.fetch(
                url="http://www.dealsea.com",
                method=urlfetch.GET,
                headers={'Content-Type': 'text/html; charset=UTF-8'}
                )
        deals = []
        if dealsea_page.status_code == 200:
            dealsea_soap = BeautifulSoup(dealsea_page.content)
            deal_divs = dealsea_soap.findAll(attrs={"class":re.compile("dealbox\d\d\d\d\d\d[\s\w]*$")})
            for deal_div in deal_divs:
                deal = models.Deals(vendor="dealsea.com")
                title_ = deal_div.find("b")
                deal.title = title_.contents[0].rstrip(", ")
                pub_date_ = title_.nextSibling
                if pub_date_:
                    deal.pub_date = str(pub_date_)+" "+ str(datetime.datetime.now().year)
                    pub_date_.extract()
                image_ = deal_div.find("img")
                image_url = image_.get("src")
                if image_url.rfind("http:")==-1:
                    image_url = "http://www.dealsea.com"+image_url
                deal.image = image_url
                expired = deal_div.find("span",attrs={"class":"colr_red xxsmall"})
                if expired:
                    deal.expired = True
                    expired.extract()
                brs_ = deal_div.findAll("br")
                internal_links = deal_div.findAll("a",attrs={"href":re.compile("\/forums\/viewtopic\.php\?t=\d*$")})
                image_.extract()
                title_.extract()
                [br_.extract() for br_ in brs_]
                [internal_link_.extract() for internal_link_ in internal_links]
                deal.content = deal_div.prettify().replace("[\n]","")
                deals+=[deal]
        current_date = datetime.datetime.now().strftime('%b %d %Y')
        for deal in deals:
            deal_ = models.Deals.gql('where pub_date =:1 and title =:2',current_date,deal.title).get()
            if deal_:
                break
            else:
                deal.put()
        self.response.out.write("Run getdeals job successfully.")

    def post(self):
         self.get()

#todo:get latest coupon code from www.retailmenot.com
class GetCouponsJob(BaseRequestHandler):
    def get(self):
    #if self.get("X-AppEngine-Cron")=="true":
        dealsea_page = urlfetch.fetch(
                url="http://www.retailmenot.com",
                method=urlfetch.GET,
                headers={'Content-Type': 'text/html; charset=UTF-8'}
                )
        deals = []
        if dealsea_page.status_code == 200:
            dealsea_soap = BeautifulSoup(dealsea_page.content)
            deal_divs = dealsea_soap.findAll(attrs={"class":re.compile("dealbox\d\d\d\d\d\d[\s\w]*$")})
            for deal_div in deal_divs:
                deal = models.Deals(vendor="dealsea.com")
                title_ = deal_div.find("b")
                deal.title = title_.contents[0].rstrip(", ")
                pub_date_ = title_.nextSibling
                if pub_date_:
                    deal.pub_date = str(pub_date_)+" "+ str(datetime.datetime.now().year)
                    pub_date_.extract()
                image_ = deal_div.find("img")
                image_url = image_.get("src")
                if image_url.rfind("http:")==-1:
                    image_url = "http://www.dealsea.com"+image_url
                deal.image = image_url
                expired = deal_div.find("span",attrs={"class":"colr_red xxsmall"})
                if expired:
                    deal.expired = True
                    expired.extract()
                brs_ = deal_div.findAll("br")
                internal_links = deal_div.findAll("a",attrs={"href":re.compile("\/forums\/viewtopic\.php\?t=\d*$")})
                image_.extract()
                title_.extract()
                [br_.extract() for br_ in brs_]
                [internal_link_.extract() for internal_link_ in internal_links]
                deal.content = deal_div.prettify().replace("[\n]","")
                deals+=[deal]
        current_date = datetime.datetime.now().strftime('%b %d %Y')
        for deal in deals:
            deal_ = models.Deals.gql('where pub_date =:1 and title =:2',current_date,deal.title).get()
            if deal_:
                break
            else:
                deal.put()
        self.response.out.write("Run getdeals job successfully.")

    def post(self):
         self.get()

