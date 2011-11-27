from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation.tests.utils import setup_moderation, teardown_moderation
from moderation.tests.apps.test_app2.models import Book


class AutoDiscoverAcceptanceTestCase(SettingsTestCase):
    '''
    As a developer I want to have a way auto discover all apps that have module
    moderator and register it with moderation.
    '''
    test_settings = 'moderation.tests.settings.auto_discover'

    def setUp(self):
        setup_moderation()

    def tearDown(self):
        teardown_moderation()

    def test_all_app_containing_moderator_module_should_be_registered(self):
        import moderation.tests.urls.auto_discover
        from moderation import moderation

        self.assertTrue(Book in moderation._registered_models)
