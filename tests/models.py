"""
Test models used in django-moderation tests
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.manager import Manager


class UserProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_profiles',
    )
    description = models.TextField()
    url = models.URLField()

    def __str__(self):
        return f"{self.user} - {self.url}"


class SuperUserProfile(UserProfile):
    super_power = models.TextField()

    def __str__(self):
        return f"{self.user} - {self.url} - {self.super_power}"


class ModelWithSlugField(models.Model):
    slug = models.SlugField(unique=True)


class ModelWithSlugField2(models.Model):
    slug = models.SlugField(unique=True)


class MenManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(gender=1)


class WomenManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(gender=0)


class ModelWithMultipleManagers(models.Model):
    gender = models.SmallIntegerField()
    objects = Manager()
    men = MenManager()
    women = WomenManager()


class ModelWithDateField(models.Model):
    date = models.DateField(auto_now=True)


class ModelWithVisibilityField(models.Model):
    test = models.CharField(max_length=20)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return '%s - is public %s' % (self.test, self.is_public)


class ModelWithWrongVisibilityField(models.Model):
    test = models.CharField(max_length=20)
    is_public = models.IntegerField()

    def __str__(self):
        return '%s - is public %s' % (self.test, self.is_public)


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


class CustomUser(User):
    date_of_birth = models.DateField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)


class UserProfileWithCustomUser(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField()
    url = models.URLField()

    def __str__(self):
        return "%s - %s" % (self.user, self.url)

    def get_absolute_url(self):
        return '/test/'


class CustomModel(models.Model):
    name = models.CharField(max_length=20)
