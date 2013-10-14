from django.conf import settings


MODERATORS = getattr(settings, "DJANGO_MODERATION_MODERATORS", ())
