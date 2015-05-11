from __future__ import unicode_literals
from django.conf import settings


MODERATORS = getattr(settings, "DJANGO_MODERATION_MODERATORS", ())

SOUTH_MIGRATION_MODULES = getattr(settings, "SOUTH_MIGRATION_MODULES", {})
SOUTH_MIGRATION_MODULES['moderation'] = 'moderation.migrations-pre17'
