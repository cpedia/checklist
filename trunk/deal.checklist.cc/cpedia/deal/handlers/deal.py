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
import BeautifulSoup

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
import traceback 

from xml.etree import ElementTree

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext import search
from google.appengine.api import images
from google.appengine.api import mail

from cpedia.deal.handlers import restful
import cpedia.deal.models.deal as models
from cpedia.utils import utils

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

class ListCouponsPage(BaseRequestHandler):
    @authorized.role("admin")
    def get(self):
        user = users.get_current_user()
        template_values = {
        }
        self.generate('coupons.html',template_values)

class DeleteDeals(BaseRequestHandler):
    def get(self):
        current_date = datetime.datetime.now().strftime('%b %d %Y')
        query = db.Query(models.Deals)
        query.filter("created_date_str",current_date)
        for deal in query.fetch(1000):
            deal.delete()
        template_values = {
        "msg":"Purge latest deals successfully.",
        }
        self.generate('deals.html',template_values)

    def post(self):
        self.get()

class DeleteCoupons(BaseRequestHandler):
    def get(self):
        current_date = datetime.datetime.now().strftime('%b %d %Y')
        query = db.Query(models.Coupons)
        query.filter("pub_date",current_date)
        for coupon in query.fetch(1000):
            coupon.delete()
        template_values = {
        "msg":"Purge latest coupons successfully.",
        }
        self.generate('coupons.html',template_values)

    def post(self):
        self.get()

class DealInfoPage(BaseRequestHandler):
    def get(self,deal_key):
        deal =  models.Deals.get(deal_key)
        template_values = {
        "deal":deal,
        }
        self.generate('deal_info.html',template_values)

class CouponInfoPage(BaseRequestHandler):
    def get(self,coupon_key):
        coupon =  models.Coupons.get(coupon_key)
        template_values = {
        "coupon":coupon,
        }
        self.generate('coupon_info.html',template_values)


    #get latest deal from dealsea.com
class GetDealsJob(BaseRequestHandler):
    def get(self):
    #if self.get("X-AppEngine-Cron")=="true":
        try:
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
                    title_ = deal_div.find("b",text=re.compile(".*"))
                    deal.title = utils.utf82uni(str(title_.rstrip(", ")))
                    b = deal_div.find("b")
                    pub_date_ = b.nextSibling
                    if pub_date_:
                        deal.pub_date = str(pub_date_)+" "+ str(datetime.datetime.now().year)
                        pub_date_.extract()
                    image_ = deal_div.find("img")
                    if image_:
                        image_url = image_.get("src")
                        if image_url.rfind("http:")==-1:
                            image_url = "http://www.dealsea.com"+image_url
                        deal.image = image_url
                    expired = deal_div.find("span",attrs={"class":"colr_red xxsmall"})
                    if expired:
                        deal.expired = True
                        expired.extract()
                    brs_ = deal_div.findAll("br")
                    priceSearch_links = deal_div.findAll("a",text='PriceSearch')
                    comments_links = deal_div.findAll("a",text='Comments')
                    if image_:
                        image_.extract()
                    title_.extract()
                    [br_.extract() for br_ in brs_]
                    [internal_link_.parent.extract() for internal_link_ in priceSearch_links]
                    [internal_link_.parent.extract() for internal_link_ in comments_links]
                    deal.content = utils.utf82uni(deal_div.prettify().replace("[\n]",""))
                    deals+=[deal]
            current_date = datetime.datetime.now().strftime('%b %d %Y')
            latest_deals = []
            for deal in deals:
                deal_ = models.Deals.gql('where created_date_str =:1 and title =:2',current_date,deal.title).fetch(10)
                if deal_ and len(deal_) > 0:
                    break
                else:
                    latest_deals += [deal]
            for latest_deal in reversed(latest_deals):
                latest_deal.created_date = datetime.datetime.now()   #unaccuracy for the auto_now_add
                latest_deal.put()
            template_values = {
            "msg":"Generate latest deals from dealsea.com successfully.",
            }
        except Exception, exception:
            mail.send_mail(sender="deal.checklist.cc <cpedia@checklist.cc>",
                           to="Ping Chen <cpedia@gmail.com>",
                           subject="Something wrong with the Deal Generation Job.",
                           body="""
Hi Ping,

Something wroing with the Deal Generation Job.

Below is the detailed exception information:
%s

Please access app engine console to resolve the problem.
http://appengine.google.com/a/checklist.cc

Sent from deal.checklist.cc
            """ % traceback.format_exc())

            template_values = {
            "msg":"Generate latest deals from dealsea.com unsuccessfully. An alert email sent out.<br>" + traceback.format_exc(),
            }

        self.generate('deals.html',template_values)

    def post(self):
        self.get()

    #get latest coupon code from www.retailmenot.com
class GetCouponsJob(BaseRequestHandler):
    def get(self):
    #if self.get("X-AppEngine-Cron")=="true":
        try:
            retailmenot_page = urlfetch.fetch(
                    url="http://www.retailmenot.com",
                    method=urlfetch.GET,
                    headers={'Content-Type': 'text/html; charset=UTF-8'}
                    )
            coupons = []
            if retailmenot_page.status_code == 200:
                retailmenot_soap = BeautifulSoup(retailmenot_page.content)
                recentCoupons = retailmenot_soap.find("div",id="recentCoupons")
                coupon_divs = recentCoupons.findAll("div",attrs={"class":"coupon"})
                for coupon_div in coupon_divs:
                    coupon = models.Coupons(vendor="retailmenot.com")
                    code_ = coupon_div.find("td",attrs={"class":"code"})
                    coupon.code = str(code_.next.contents[0])
                    discount_  = coupon_div.find("td",attrs={"class":"discount"})
                    coupon.discount = utils.utf82uni(str(discount_.contents[0]))
                    site_info = coupon_div.find("span",attrs={"class":"site"}).next.contents[0]
                    coupon.site_name = utils.utf82uni(site_info.rstrip(" coupon codes"))
                    siteTools = coupon_div.find("div",attrs={"class":"siteTools"})
                    site_img = siteTools.find("img")
                    if site_img:
                        image_url = site_img.get("src")
                        coupon.image = image_url
                        site_url = site_img.get("alt")
                        if site_url.rfind("http:")==-1:
                            site_url = "http://"+site_url
                        coupon.site_url = site_url
                    script_ = coupon_div.find("script",attrs={"type":"data"}).contents[0]
                    couponId = "couponId"
                    siteId = "siteId"
                    dict_ = eval(script_)
                    coupon.coupon_id = dict_["couponId"]
                    coupon.site_id = dict_["siteId"]
                    coupons+=[coupon]
            latest_coupons = []
            for coupon in coupons:
                coupon_ = models.Coupons.gql('where coupon_id =:1 and site_id =:2',coupon.coupon_id,coupon.site_id
                        ).fetch(10
                        )
                if coupon_ and len(coupon_) > 0:
                    break
                else:
                    latest_coupons += [coupon]
            for latest_coupon in reversed(latest_coupons):
                latest_coupon.created_date = datetime.datetime.now() #unaccuracy for the auto_now_add
                latest_coupon.put()
            template_values = {
            "msg":"Generate latest coupons from retailmenot successfully.",
            }
        except Exception, exception:
            mail.send_mail(sender="deal.checklist.cc <cpedia@checklist.cc>",
                           to="Ping Chen <cpedia@gmail.com>",
                           subject="Something wrong with the coupon generation job.",
                           body="""
Hi Ping,

Something wroing with the Coupon Generation job.

Below is the detailed exception information:
%s

Please access app engine console to resolve the problem.
http://appengine.google.com/a/checklist.cc

Sent from deal.checklist.cc
            """ % traceback.format_exc())

            template_values = {
            "msg":"Generate latest deals from dealsea.com unsuccessfully. An alert email sent out.<br>" + traceback.format_exc(),
            }

        self.generate('coupons.html',template_values)

def post(self):
    self.get()

