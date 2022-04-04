import sys

from django.test.testcases import TestCase

from moderation.helpers import auto_discover
from tests.utils import setup_moderation, teardown_moderation


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
        self.assertTrue("tests.moderator" in sys.modules.keys())
