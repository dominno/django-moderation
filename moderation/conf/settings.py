from django.conf import settings

MODERATORS = getattr(settings, 'MODERATION_MODERATORS', ())
