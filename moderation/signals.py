from __future__ import unicode_literals
import django.dispatch

pre_moderation = django.dispatch.Signal(providing_args=["instance", "status"])

post_moderation = django.dispatch.Signal(providing_args=["instance", "status"])
