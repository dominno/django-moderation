from django.db import models
from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except:
    from django.contrib.auth.models import User
from django import VERSION
from django.contrib import admin


class ExampleUserProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    description = models.TextField()
    url = models.URLField()
    
    def __unicode__(self):
        return "%s - %s" % (self.user, self.url)
    
    def get_absolute_url(self):
        return '/test/'

if VERSION[:2] >= (1, 5):

    from django.contrib.auth.models import AbstractUser

    class CustomUser(AbstractUser):
        date_of_birth = models.DateField(blank=True, null=True)
        height = models.FloatField(blank=True, null=True)

    class UserProfileWithCustomUser(models.Model):
        user = models.ForeignKey(settings.AUTH_USER_MODEL)
        description = models.TextField()
        url = models.URLField()

        def __unicode__(self):
            return "%s - %s" % (self.user, self.url)

        def get_absolute_url(self):
            return '/test/'
