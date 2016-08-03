from django.apps import AppConfig

from .conf.settings import AUTODISCOVER


class ModerationConfig(AppConfig):
    name = "moderation"
    verbose_name = "Moderation"

    def ready(self):
        if AUTODISCOVER:
            from .helpers import auto_discover
            auto_discover()
