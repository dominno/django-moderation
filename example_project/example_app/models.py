from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class ExampleUserProfile(models.Model):
    user = models.ForeignKey(getattr(settings, 'AUTH_USER_MODEL', 'auth.User'))
    description = models.TextField()
    url = models.URLField()

    def __str__(self):
        return "%s - %s" % (self.user, self.url)

    def get_absolute_url(self):
        return '/test/'


class CustomUser(AbstractUser):
    date_of_birth = models.DateField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)


class UserProfileWithCustomUser(models.Model):
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'))
    description = models.TextField()
    url = models.URLField()

    def __str__(self):
        return "%s - %s" % (self.user, self.url)

    def get_absolute_url(self):
        return '/test/'
