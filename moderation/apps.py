from django.apps import AppConfig


class SimpleModerationConfig(AppConfig):
    name = 'moderation'
    verbose_name = 'Moderation'
    default_auto_field = 'django.db.models.AutoField'


class ModerationConfig(SimpleModerationConfig):
    def ready(self):
        # We have to import this here because it imports from models.py
        from .helpers import auto_discover
        auto_discover()
