# -*- coding: utf-8 -*-
"""
    tipfy
    ~~~~~

    Minimalist WSGI application and utilities for App Engine.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
__version__ = '0.7'
__version_info__ = tuple(int(n) for n in __version__.split('.'))

#: Default configuration values for this module. Keys are:
#:
#: auth_store_class
#:     The default auth store class to use in :class:`tipfy.Request`.
#:     Default is `tipfy.auth.appengine.AppEngineAuthStore`.
#:
#: i18n_store_class
#:     The default internationalization store class.
#:     Default is `tipfy.i18n.I18nStore`.
#:
#: session_store_class
#:     The default session store class to use in :class:`tipfy.Request`.
#:     Default is `tipfy.sessions.SessionStore`.
#:
#: server_name
#:     The server name used to calculate current subdomain. This only need
#:     to be defined to map URLs to subdomains. Default is None.
#:
#: default_subdomain
#:     The default subdomain used for rules without a subdomain defined.
#:     This only need to be defined to map URLs to subdomains. Default is ''.
default_config = {
    'auth_store_class':    'tipfy.auth.appengine.AppEngineAuthStore',
    'i18n_store_class':    'tipfy.i18n.I18nStore',
    'session_store_class': 'tipfy.sessions.SessionStore',
    'server_name':         None,
    'default_subdomain':   '',
}

from tipfy.app import *
from tipfy.config import DEFAULT_VALUE, REQUIRED_VALUE
from tipfy.routing import HandlerPrefix, NamePrefix, RegexConverter, Rule
