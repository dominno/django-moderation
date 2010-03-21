'''
Created on 2009-12-10

@author: dominik
'''
from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from django.core import management
from django.contrib.auth.models import User
from moderation.tests.test_app.models import UserProfile
from moderation.managers import ModerationObjectsManager
from django.db.models.manager import Manager
from moderation.models import ModeratedObject
from django.core.exceptions import ObjectDoesNotExist
from moderation import moderation, ModerationManager
from django.contrib.contenttypes import generic
from django.db.models.query import EmptyQuerySet


class ModerationObjectsManagerTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    urls = 'moderation.tests.test_urls'
    test_settings = 'moderation.tests.test_settings'

    def setUp(self):
        from django.db.models import signals
        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

        self.moderation = ModerationManager()
        self.moderation.register(UserProfile)

    def tearDown(self):
        self.moderation.unregister(UserProfile)
        
    def test_moderation_objects_manager(self):
        ManagerClass = ModerationObjectsManager()(Manager)

        self.assertEqual(unicode(ManagerClass.__bases__),
                    u"(<class 'moderation.managers.ModerationObjectsManager'>"\
                    ", <class 'django.db.models.manager.Manager'>)")

    def test_filter_moderated_objects_returns_empty_queryset(self):
        """Test filter_moderated_objects returns empty queryset
        for object that has moderated object"""

        ManagerClass = ModerationObjectsManager()(Manager)
        manager = ManagerClass()

        query_set = UserProfile._default_manager.all()
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        self.assertEqual(unicode(manager.filter_moderated_objects(query_set)),
                                                                    u"[]")

    def test_filter_moderated_objects_returns_object(self):
        """Test if filter_moderated_objects return object when object 
        doesnt have moderated object or deserialised object is <> object"""
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        self.profile.description = "New"
        self.profile.save()

        self.assertEqual(unicode(UserProfile.objects.all()),
                    u'[<UserProfile: moderator - http://www.google.com>]')
