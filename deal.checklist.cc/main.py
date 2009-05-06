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

import wsgiref.handlers

from google.appengine.ext import webapp

import logging
import os

import config

from cpedia.deal.handlers import deal
from cpedia.deal.handlers import rpc

from google.appengine.ext.webapp import template
template.register_template_library('cpedia.filter.replace')
template.register_template_library('cpedia.filter.gravatar')

# Force Django to reload its settings.
#from django.conf import settings
#settings._target = None

# Must set this env var before importing any part of Django
#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

def main():
    application = webapp.WSGIApplication(
                    [
                    ('/json/([-\w\.]+)/*$', rpc.RPCHandler),
                    ('/403.html', deal.UnauthorizedHandler),
                    ('/404.html', deal.NotFoundHandler),
                    ('/tasks/getdeals/*$', deal.GetDealsJob),
                    ('/tasks/getcoupons/*$', deal.GetCouponsJob),
                    ('/tasks/deletedeals/*$', deal.DeleteDeals),
                    ('/tasks/deletecoupons/*$', deal.DeleteCoupons),
                    ('/list/deals/*$', deal.MainPage),
                    ('/list/coupons/*$', deal.ListCouponsPage),
                    ('/deal/([-\w\.]+)/*$', deal.DealInfoPage),
                    ('/coupon/([-\w\.]+)/*$', deal.CouponInfoPage),
                    ('/*$', deal.MainPage),
                    ],
                    debug=config.DEBUG)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()
