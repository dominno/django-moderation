"""
Test models used in django-moderations tests
"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.ForeignKey(User, related_name='user_profile_set')
    description = models.TextField()
    url = models.URLField()

    def __unicode__(self):
        return "%s - %s" % (self.user, self.url)
