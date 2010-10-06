from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin


class ExampleUserProfile(models.Model):
    user = models.ForeignKey(User)
    description = models.TextField()
    url = models.URLField()
    
    def __unicode__(self):
        return "%s - %s" % (self.user, self.url)
    
    def get_absolute_url(self):
        return '/test/'




