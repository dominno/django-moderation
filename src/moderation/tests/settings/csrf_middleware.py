from moderation.tests.utils.testsettingsmanager import get_only_settings_locals
import django
import os

DATABASE_ENGINE = 'sqlite3'
DEBUG = True
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'moderation',
    'moderation.tests.apps.test_app1',
    )

ROOT_URLCONF = 'moderation.tests.urls.default.py'

DJANGO_MODERATION_MODERATORS = (
    'test@example.com',
    )

version = django.get_version()[:3]

if version == '1.2':
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',

        #'django.middleware.doc.XViewMiddleware',
        )

elif version == '1.1':
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.csrf.middleware.CsrfViewMiddleware',
        'django.contrib.csrf.middleware.CsrfResponseMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.middleware.doc.XViewMiddleware',

        )

test_module_path = os.sep.join(os.path.dirname(__file__).split(os.sep)[:-1])

TEMPLATE_DIRS = (
    os.path.join(test_module_path, "templates"),
    )

settings = get_only_settings_locals(locals().copy())
