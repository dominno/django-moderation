#!/usr/bin/env python

import sys
import os

from os.path import dirname, abspath
from optparse import OptionParser

from django.conf import settings, global_settings

from moderation.utils import django_17, django_110


if django_110():
    CONTEXT_PROCESSORS = [
        'django.contrib.auth.context_processors.auth',
        'django.template.context_processors.i18n',
        'django.template.context_processors.request',
        'django.template.context_processors.media',
        'django.contrib.messages.context_processors.messages',
    ]
else:
    CONTEXT_PROCESSORS = [
        'django.contrib.auth.context_processors.auth',
        'django.core.context_processors.i18n',
        'django.core.context_processors.request',
        'django.core.context_processors.media',
        'django.contrib.messages.context_processors.messages',
    ]

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
        SERIALIZATION_MODULES={},
        MEDIA_URL='/media/',
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls.default',

        MODERATION_MODERATORS=(
            'test@example.com',
        ),
        DEBUG=True,
        SITE_ID=1,
        # For Django 1.10 compatibility
        # See https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-TEMPLATES
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': CONTEXT_PROCESSORS,
                },
            },
        ],
    )


def prepare_test_runner(*args, **kwargs):
    """
    Configures a test runner based on Django version to
    maintain backward compatibility.
    """
    import django

    test_runner = None

    if django_17():
        django.setup()
        from django.test.runner import DiscoverRunner
        test_runner = DiscoverRunner(
            pattern='test*.py',
            verbosity=kwargs.get('verbosity', 1),
            interactive=kwargs.get('interactive', False),
            failfast=kwargs.get('failfast'),
        )
    else:
        from django.test.simple import DjangoTestSuiteRunner
        test_runner = DjangoTestSuiteRunner(
            verbosity=kwargs.get('verbosity', 1),
            interactive=kwargs.get('interactive', False),
            failfast=kwargs.get('failfast')
        )
    return test_runner


def runtests(*test_args, **kwargs):
    if not test_args:
        test_args = ['tests']

    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    test_runner = prepare_test_runner(**kwargs)
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--failfast', action='store_true', default=False, dest='failfast')

    (options, args) = parser.parse_args()

    runtests(failfast=options.failfast, *args)
