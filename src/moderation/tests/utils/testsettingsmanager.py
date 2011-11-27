"""
TestSettingsManager class for making temporary changes to 
settings for the purposes of a unittest or doctest. 
It will keep track of the original settings and let 
easily revert them back when you're done.

Snippet taken from: http://www.djangosnippets.org/snippets/1011/
"""

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.test import TestCase
from django.utils.importlib import import_module

NO_SETTING = ('!', None)


class TestSettingsManager(object):
    """
    A class which can modify some Django settings temporarily for a
    test and then revert them to their original values later.

    Automatically handles resyncing the DB if INSTALLED_APPS is
    modified.

    """

    def __init__(self):
        self._original_settings = {}

    def set(self, **kwargs):
        for k, v in kwargs.iteritems():
            self._original_settings.setdefault(k, getattr(settings, k,
                                                          NO_SETTING))
            setattr(settings, k, v)
        if 'INSTALLED_APPS' in kwargs:
            self.syncdb()

    def syncdb(self):
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def revert(self):
        for k, v in self._original_settings.iteritems():
            if v == NO_SETTING:
                try:
                    delattr(settings, k)
                except AttributeError:
                    pass
            else:
                setattr(settings, k, v)
        if 'INSTALLED_APPS' in self._original_settings:
            self.syncdb()
        self._original_settings = {}


class SettingsTestCase(TestCase):
    """
    A subclass of the Django TestCase with a settings_manager
    attribute which is an instance of TestSettingsManager.

    """
    test_settings = ''

    def __init__(self, *args, **kwargs):
        super(SettingsTestCase, self).__init__(*args, **kwargs)
        self.settings_manager = TestSettingsManager()

    def _pre_setup(self):
        if self.test_settings:
            settings_module = import_module(self.test_settings)
            self.settings_manager.set(**settings_module.settings)
        super(SettingsTestCase, self)._pre_setup()

    def _post_teardown(self):
        if self.test_settings:
            self.settings_manager.revert()

        super(SettingsTestCase, self)._post_teardown()


def get_only_settings_locals(locals):
    for key in locals.keys():
        if key.islower():
            del locals[key]
    return locals
