# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.appstats
"""
import unittest

from nose.tools import raises

import _base


from tipfy import cleanup_wsgi_app, local, NotFound, WSGIApplication
from tipfy.ext.appstats import AppstatsMiddleware

class TestAppstatsMiddleware(unittest.TestCase):
    def tearDown(self):
        cleanup_wsgi_app()

    def test_pre_run_app_no_dev(self):
        app = WSGIApplication({
            'tipfy': {
                'middleware': ['tipfy.ext.appstats.AppstatsMiddleware'],
            }
        })

        middleware = AppstatsMiddleware()
        new_app = middleware.pre_run_app(app)

        self.assertEqual(new_app.__name__, 'appstats_wsgi_wrapper')

