"""Test utlities for writing NDB tests.

Useful set of utilities for correctly setting up the appengine testing
environment.  Functions and test-case base classes that configure stubs
and other environment variables.

Borrowed from http://code.google.com/p/appengine-ndb-experiment/
"""
import os
import unittest

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.api.memcache import memcache_stub
from google.appengine.api import memcache
from google.appengine.api.taskqueue import taskqueue_stub
from google.appengine.api import user_service_stub

from tipfy.local import local


def main():
    unittest.main()


def set_up_basic_stubs(app_id):
    """Set up a basic set of stubs.

    Configures datastore and memcache stubs for testing.

    Args:
    app_id: Application ID to configure stubs with.

    Returns:
    Dictionary mapping stub name to stub.
    """
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

    ds_stub = datastore_file_stub.DatastoreFileStub(app_id, None)
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', ds_stub)

    mc_stub = memcache_stub.MemcacheServiceStub()
    apiproxy_stub_map.apiproxy.RegisterStub('memcache', mc_stub)

    tq_stub = taskqueue_stub.TaskQueueServiceStub()
    apiproxy_stub_map.apiproxy.RegisterStub('taskqueue', tq_stub)

    user_stub = user_service_stub.UserServiceStub()
    apiproxy_stub_map.apiproxy.RegisterStub('user', user_stub)

    return {
        'datastore': ds_stub,
        'memcache': mc_stub,
        'taskqueue': tq_stub,
        'user': user_stub,
    }


class BaseTestCase(unittest.TestCase):
    """Base class for tests that actually interact with the (stub) Datastore.

    NOTE: Care must be used when working with model classes using this test
    class.  The kind-map is reset on each iteration.  The general practice
    should be to declare test models in the sub-classes setUp method AFTER
    calling this classes setUp method.
    """

    # Override this in sub-classes to configure alternate application ids.
    APP_ID = '_'

    def setUp(self):
        """Set up test framework.

        Configures basic environment variables, stubs and creates a default
        connection.
        """
        os.environ['APPLICATION_ID'] = self.APP_ID
        self.set_up_stubs()

    def tearDown(self):
        """Tear down test framework."""
        self.datastore_stub.Clear()
        self.memcache_stub.MakeSyncCall('memcache', 'FlushAll',
                                        memcache.MemcacheFlushRequest(),
                                        memcache.MemcacheFlushResponse())
        local.__release_local__()

    def set_up_stubs(self):
        """Set up basic stubs using classes default application id.

        Set attributes on tests for each stub created.
        """
        for name, value in set_up_basic_stubs(self.APP_ID).iteritems():
            setattr(self, name + '_stub', value)
