from moderation.tests.utils.testsettingsmanager import get_only_settings_locals

DATABASE_ENGINE = 'sqlite3'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'moderation',
    'moderation.tests.test_app',
)

ROOT_URLCONF = 'moderation.tests.test_urls.py'

DJANGO_MODERATION_MODERATORS = (
                               'test@example.com',
                               )
settings = get_only_settings_locals(locals().copy())
