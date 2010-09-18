# -*- coding: utf-8 -*-
"""
Tests for tipfy config
"""
import unittest

from tipfy import Config, Tipfy, RequestHandler, get_config, REQUIRED_VALUE


class TestConfig(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_get_existing_keys(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get('foo', 'bar'), 'baz')
        self.assertEqual(config.get('foo', 'doo'), 'ding')

    def test_get_existing_keys_from_default(self):
        config = Config({}, {'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get('foo', 'bar'), 'baz')
        self.assertEqual(config.get('foo', 'doo'), 'ding')

    def test_get_non_existing_keys(self):
        config = Config()

        self.assertEqual(config.get('foo', 'bar'), None)

    def test_get_dict_existing_keys(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get('foo'), {
            'bar': 'baz',
            'doo': 'ding',
        })

    def test_get_dict_non_existing_keys(self):
        config = Config()

        self.assertEqual(config.get('bar'), None)

    def test_get_with_default(self):
        config = Config()

        self.assertEqual(config.get('foo', 'bar', 'ooops'), 'ooops')
        self.assertEqual(config.get('foo', 'doo', 'wooo'), 'wooo')

    def test_get_with_default_and_none(self):
        config = Config({'foo': {
            'bar': None,
        }})

        self.assertEqual(config.get('foo', 'bar', 'ooops'), None)

    def test_update(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get('foo', 'bar'), 'baz')
        self.assertEqual(config.get('foo', 'doo'), 'ding')

        config.update('foo', {'bar': 'other'})

        self.assertEqual(config.get('foo', 'bar'), 'other')
        self.assertEqual(config.get('foo', 'doo'), 'ding')

    def test_setdefault(self):
        config = Config()

        self.assertEqual(config.get('foo'), None)

        config.setdefault('foo', {
            'bar': 'baz',
            'doo': 'ding',
        })

        self.assertEqual(config.get('foo', 'bar'), 'baz')
        self.assertEqual(config.get('foo', 'doo'), 'ding')

    def test_setdefault2(self):
        config = Config({'foo': {
            'bar': 'baz',
        }})

        self.assertEqual(config.get('foo'), {
            'bar': 'baz',
        })

        config.setdefault('foo', {
            'bar': 'wooo',
            'doo': 'ding',
        })

        self.assertEqual(config.get('foo', 'bar'), 'baz')
        self.assertEqual(config.get('foo', 'doo'), 'ding')

    def test_setitem(self):
        config = Config()

        def setitem(key, value):
            config[key] = value
            return config

        self.assertEqual(setitem('foo', {'bar': 'baz'}), {'foo': {'bar': 'baz'}})

    def test_init_no_dict_values(self):
        self.assertRaises(AssertionError, Config, {'foo': 'bar'})
        self.assertRaises(AssertionError, Config, {'foo': None})
        self.assertRaises(AssertionError, Config, 'foo')

    def test_init_no_dict_default(self):
        self.assertRaises(AssertionError, Config, {}, {'foo': 'bar'})
        self.assertRaises(AssertionError, Config, {}, {'foo': None})
        self.assertRaises(AssertionError, Config, {}, 'foo')

    def test_update_no_dict_values(self):
        config = Config()

        self.assertRaises(AssertionError, config.update, {'foo': 'bar'}, 'baz')
        self.assertRaises(AssertionError, config.update, {'foo': None}, 'baz')
        self.assertRaises(AssertionError, config.update, 'foo', 'bar')

    def test_setdefault_no_dict_values(self):
        config = Config()

        self.assertRaises(AssertionError, config.setdefault, 'foo', 'bar')
        self.assertRaises(AssertionError, config.setdefault, 'foo', None)

    def test_setitem_no_dict_values(self):
        config = Config()

        def setitem(key, value):
            config[key] = value
            return config

        self.assertRaises(AssertionError, setitem, 'foo', 'bar')
        self.assertRaises(AssertionError, setitem, 'foo', None)


class TestLoadConfig(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_default_config(self):
        config = Config()

        from resources.template import default_config as template_config
        from resources.i18n import default_config as i18n_config

        self.assertEqual(config.get_or_load('resources.template', 'templates_dir'), template_config['templates_dir'])
        self.assertEqual(config.get_or_load('resources.i18n', 'locale'), i18n_config['locale'])
        self.assertEqual(config.get_or_load('resources.i18n', 'timezone'), i18n_config['timezone'])

    def test_default_config_with_non_existing_key(self):
        config = Config()

        from resources.i18n import default_config as i18n_config

        # In the first time the module config will be loaded normally.
        self.assertEqual(config.get_or_load('resources.i18n', 'locale'), i18n_config['locale'])

        # In the second time it won't be loaded, but won't find the value and then use the default.
        self.assertEqual(config.get_or_load('resources.i18n', 'i_dont_exist', 'foo'), 'foo')

    def test_override_config(self):
        config = Config({
            'resources.template': {
                'templates_dir': 'apps/templates'
            },
            'resources.i18n': {
                'locale': 'pt_BR',
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(config.get_or_load('resources.template', 'templates_dir'), 'apps/templates')
        self.assertEqual(config.get_or_load('resources.i18n', 'locale'), 'pt_BR')
        self.assertEqual(config.get_or_load('resources.i18n', 'timezone'), 'America/Sao_Paulo')

    def test_override_config2(self):
        config = Config({
            'resources.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(config.get_or_load('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(config.get_or_load('resources.i18n', 'timezone'), 'America/Sao_Paulo')

    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
        }})

        self.assertEqual(config.get_or_load('foo', 'bar'), 'baz')

    def test_get_with_default(self):
        config = Config()

        self.assertEqual(config.get_or_load('resources.i18n', 'bar', 'baz'), 'baz')

    def test_get_with_default_and_none(self):
        config = Config({'foo': {
            'bar': None,
        }})

        self.assertEqual(config.get_or_load('foo', 'bar', 'ooops'), None)

    def test_get_with_default_and_module_load(self):
        config = Config()
        self.assertEqual(config.get_or_load('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(config.get_or_load('resources.i18n', 'locale', 'foo'), 'en_US')

    def test_required_config(self):
        config = Config()
        self.assertRaises(KeyError, config.get_or_load, 'resources.i18n', 'foo')

    def test_missing_module(self):
        config = Config()
        self.assertRaises(KeyError, config.get_or_load, 'i_dont_exist', 'i_dont_exist')

    def test_missing_module2(self):
        config = Config()
        self.assertRaises(KeyError, config.get_or_load, 'i_dont_exist')

    def test_missing_key(self):
        config = Config()
        self.assertRaises(KeyError, config.get_or_load, 'resources.i18n', 'i_dont_exist')

    def test_missing_default_config(self):
        config = Config()
        self.assertRaises(KeyError, config.get_or_load, 'tipfy', 'foo')

    def test_app_get_config(self):
        app = Tipfy()

        self.assertEqual(app.get_config('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(app.get_config('resources.i18n', 'locale', 'foo'), 'en_US')
        self.assertEqual(app.get_config('resources.i18n'), {
            'locale': 'en_US',
            'timezone': 'America/Chicago',
            'required': REQUIRED_VALUE,
        })

    def test_request_handler_get_config(self):
        app = Tipfy()

        handler = RequestHandler(app, None)

        self.assertEqual(handler.get_config('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(handler.get_config('resources.i18n', 'locale', 'foo'), 'en_US')
        self.assertEqual(handler.get_config('resources.i18n'), {
            'locale': 'en_US',
            'timezone': 'America/Chicago',
            'required': REQUIRED_VALUE,
        })


class TestGetConfig(unittest.TestCase):
    def tearDown(self):
        try:
            Tipfy.app.clear_locals()
        except:
            pass

    def test_get_config(self):
        app = Tipfy()
        self.assertEqual(get_config('resources.i18n', 'locale'), 'en_US')
