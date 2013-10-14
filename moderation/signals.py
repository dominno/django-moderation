import django.dispatch

pre_moderation = django.dispatch.Signal(providing_args=["instance", "status"])

post_moderation = django.dispatch.Signal(providing_args=["instance", "status"])
