"""
Test models used in django-moderations tests
"""
from django.conf import settings
from django.db import models
from django.db.models.manager import Manager
from django import VERSION


class UserProfile(models.Model):
    user = models.ForeignKey(getattr(settings, 'AUTH_USER_MODEL', 'auth.User'), 
                             related_name='user_profile_set')
    description = models.TextField()
    url = models.URLField()

    def __unicode__(self):
        return "%s - %s" % (self.user, self.url)


class SuperUserProfile(UserProfile):
    super_power = models.TextField()

    def __unicode__(self):
        return "%s - %s - %s" % (self.user, self.url, self.super_power)


class ModelWithSlugField(models.Model):
    slug = models.SlugField(unique=True)


class ModelWithSlugField2(models.Model):
    slug = models.SlugField(unique=True)


class MenManager(Manager):

    def get_query_set(self):
        query_set = super(MenManager, self).get_query_set()
        return query_set.filter(gender=1)


class WomenManager(Manager):

    def get_query_set(self):
        query_set = super(WomenManager, self).get_query_set()
        return query_set.filter(gender=0)


class ModelWithMultipleManagers(models.Model):
    gender = models.SmallIntegerField()
    objects = Manager()
    men = MenManager()
    women = WomenManager()


class ModelWIthDateField(models.Model):
    date = models.DateField(auto_now=True)


class ModelWithVisibilityField(models.Model):
    test = models.CharField(max_length=20)
    is_public = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s - is public %s' % (self.test, self.is_public)


class ModelWithWrongVisibilityField(models.Model):
    test = models.CharField(max_length=20)
    is_public = models.IntegerField()

    def __unicode__(self):
        return u'%s - is public %s' % (self.test, self.is_public)


class ModelWithImage(models.Model):
    image = models.ImageField(upload_to='tmp')


class ModelWithModeratedFields(models.Model):
    moderated = models.CharField(max_length=20)
    also_moderated = models.CharField(max_length=20)
    unmoderated = models.CharField(max_length=20)

    moderated_fields = ('moderated', 'also_moderated')


class ProxyProfile(UserProfile):

    class Meta(object):
        proxy = True


class Book(models.Model):
    title = models.CharField(max_length=20)
    author = models.CharField(max_length=20)


if VERSION[:2] >= (1, 5):

    from django.contrib.auth.models import User

    class CustomUser(User):
        date_of_birth = models.DateField(blank=True, null=True)
        height = models.FloatField(blank=True, null=True)

    class UserProfileWithCustomUser(models.Model):
        user = models.ForeignKey(CustomUser)
        description = models.TextField()
        url = models.URLField()

        def __unicode__(self):
            return "%s - %s" % (self.user, self.url)

        def get_absolute_url(self):
            return '/test/'
