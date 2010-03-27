"""
Test models used in django-moderations tests
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.manager import Manager


class UserProfile(models.Model):
    user = models.ForeignKey(User, related_name='user_profile_set')
    description = models.TextField()
    url = models.URLField()

    def __unicode__(self):
        return "%s - %s" % (self.user, self.url)


class ModelWithSlugField(models.Model):
    slug = models.SlugField(unique=True)


class ModelWithSlugField2(models.Model):
    slug = models.SlugField(unique=True)


class MenMenager(Manager):
    
    def get_query_set(self):
        query_set = super(MenMenager, self).get_query_set()
        return query_set.filter(gender=1)


class WomenMenager(Manager):
    
    def get_query_set(self):
        query_set = super(WomenMenager, self).get_query_set()
        return query_set.filter(gender=0)


class ModelWithMultipleManagers(models.Model):
    gender = models.SmallIntegerField()
    objects = Manager()
    men = MenMenager()
    women = WomenMenager()


class ModelWIthDateField(models.Model):
    date = models.DateField(auto_now=True)
