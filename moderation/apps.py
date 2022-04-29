from django.apps import AppConfig


class SimpleModerationConfig(AppConfig):
    name = 'moderation'
    verbose_name = 'Moderation'
    default_auto_field = 'django.db.models.AutoField'
    default = False


class ModerationConfig(SimpleModerationConfig):
    default = True

    def ready(self):
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("moderator")
