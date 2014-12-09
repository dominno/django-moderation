#!/usr/bin/env python
import sys
import os
from os.path import dirname, abspath
from optparse import OptionParser

from django.conf import settings, global_settings
import django

# For convenience configure settings if they are not pre-configured or if we
# haven't been provided settings to use by environment variable.
if not settings.configured and not os.environ.get('DJANGO_SETTINGS_MODULE'):
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',

            'moderation',
            'tests',
        ],
        SERIALIZATION_MODULES = {},
        MEDIA_URL = '/media/',
        STATIC_URL = '/static/',
        ROOT_URLCONF = 'tests.urls.default',

        DJANGO_MODERATION_MODERATORS = (
            'test@example.com',
        ),
        DEBUG=True,
        SITE_ID=1,
    )

django.setup()

from django.test.runner import DiscoverRunner


def runtests(*test_args, **kwargs):
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    if not test_args:
        test_args = ['tests']
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    test_runner = DiscoverRunner(pattern='*.py', verbosity=kwargs.get('verbosity', 1),
                                 interactive=kwargs.get('interactive', False), failfast=kwargs.get('failfast'))
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('--failfast', action='store_true', default=False, dest='failfast')

    (options, args) = parser.parse_args()

    runtests(failfast=options.failfast, *args)