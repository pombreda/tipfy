# -*- coding: utf-8 -*-
"""
    Tests for tipfy.ext.jinja2
"""
import os
import sys
import unittest

from jinja2 import FileSystemLoader, Environment

from tipfy import RequestHandler, Response, Tipfy
from tipfy.ext import jinja2

current_dir = os.path.abspath(os.path.dirname(__file__))
templates_dir = os.path.join(current_dir, 'resources', 'templates')
templates_compiled_target = os.path.join(current_dir, 'resources', 'templates_compiled')


class TestJinja2(unittest.TestCase):
    def setUp(self):
        Tipfy.request = Tipfy.request_class.from_values()

    def tearDown(self):
        Tipfy.app = Tipfy.request = None

    def test_render_template(self):
        app = Tipfy({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        assert res == message

    def test_render_response(self):
        app = Tipfy({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})

        message = 'Hello, World!'
        response = jinja2.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message

    def test_render_response_force_compiled(self):
        app = Tipfy({'tipfy.ext.jinja2': {
            'templates_compiled_target': templates_compiled_target,
            'force_use_compiled': True,
        }})

        message = 'Hello, World!'
        response = jinja2.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message

    def test_jinja2_mixin_render_template(self):
        class MyHandler(RequestHandler, jinja2.Jinja2Mixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_template('template1.html', message=message)
        assert response == message

    def test_jinja2_mixin_render_response(self):
        class MyHandler(RequestHandler, jinja2.Jinja2Mixin):
            def __init__(self, app, request):
                self.app = app
                self.request = request
                self.context = {}

        app = Tipfy({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})
        message = 'Hello, World!'

        handler = MyHandler(Tipfy.app, Tipfy.request)
        response = handler.render_response('template1.html', message=message)
        assert isinstance(response, Response)
        assert response.mimetype == 'text/html'
        assert response.data == message

    def test_get_template_attribute(self):
        app = Tipfy({'tipfy.ext.jinja2': {'templates_dir': templates_dir}})

        hello = jinja2.get_template_attribute('hello.html', 'hello')
        assert hello('World') == 'Hello, World!'

    def test_engine_factory(self):
        def get_jinja2_env():
            app = Tipfy.app
            cfg = app.get_config('tipfy.ext.jinja2')

            loader = FileSystemLoader(cfg.get( 'templates_dir'))

            return Environment(loader=loader)


        app = Tipfy({'tipfy.ext.jinja2': {
            'templates_dir': templates_dir,
            'engine_factory': get_jinja2_env,
        }})

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        assert res == message

    def test_engine_factory2(self):
        old_sys_path = sys.path[:]
        sys.path.insert(0, current_dir)

        app = Tipfy({'tipfy.ext.jinja2': {
            'templates_dir': templates_dir,
            'engine_factory': 'resources.get_jinja2_env',
        }})

        message = 'Hello, World!'
        res = jinja2.render_template('template1.html', message=message)
        assert res == message

        sys.path = old_sys_path
