default_app_config = "moderation.apps.ModerationConfig"

from django import VERSION
if VERSION < (1, 8):
    from moderation.register import ModerationManager
    moderation = ModerationManager()
