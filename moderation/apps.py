from django.apps import AppConfig

import moderation

class ModerationConfig(AppConfig):
    name = "moderation"
    verbose_name = "Django moderation"

    def ready(self):
        from moderation.register import ModerationManager
        moderation.moderation = ModerationManager()
