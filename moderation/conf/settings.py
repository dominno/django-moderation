from __future__ import unicode_literals

import warnings

from django.conf import settings


MODERATORS = getattr(settings, "DJANGO_MODERATION_MODERATORS", ())

AUTODISCOVER = getattr(settings, "MODERATION_AUTODISCOVER", False)

SOUTH_MIGRATION_MODULES = getattr(settings, "SOUTH_MIGRATION_MODULES", {})
SOUTH_MIGRATION_MODULES['moderation'] = 'moderation.migrations-pre17'
