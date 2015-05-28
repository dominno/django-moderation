from __future__ import unicode_literals

import sys

from django.test.testcases import TestCase

from tests.utils import setup_moderation, teardown_moderation
from tests.models import Book
from moderation.helpers import auto_discover
from moderation.utils import django_17


class AutoDiscoverAcceptanceTestCase(TestCase):
    '''
    As a developer I want to have a way auto discover all apps that have module
    moderator and register it with moderation.
    '''
    urls = 'tests.urls.auto_discover'

    def setUp(self):
        setup_moderation()

    def tearDown(self):
        teardown_moderation()

    def test_all_app_containing_moderator_module_should_be_registered(self):
        auto_discover()

        if django_17():
            self.assertTrue("tests.moderator" in sys.modules.keys())
        else:

            from moderation import moderation

            self.assertTrue(Book in moderation._registered_models)
