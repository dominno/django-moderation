from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation.tests.test_app.models import UserProfile
from moderation import GenericModerator
from moderation.managers import ModerationObjectsManager
from django.core import mail
from django.contrib.auth.models import User
from moderation.models import ModeratedObject
from django.db.models.manager import Manager
import unittest


class GenericModeratorTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    urls = 'django-moderation.test_urls'
    test_settings = 'moderation.tests.test_settings'
    
    def setUp(self):
        self.user = User.objects.get(username='admin')
        obj = ModeratedObject(content_object=self.user)
        obj.save()
        self.user.moderated_object = obj
    
    def test_create_generic_moderator(self):

        moderator = GenericModerator(UserProfile)
        
        self.assertEqual(moderator.model_class, UserProfile)
        self.assertEqual(moderator.manager_names, ['objects'])
        self.assertEqual(moderator.moderation_manager_class,
                         ModerationObjectsManager)
        self.assertEqual(moderator.auto_approve_for_staff, True)
        self.assertEqual(moderator.auto_approve_for_groups, None)
        self.assertEqual(moderator.auto_reject_for_groups, None)

    def test_subclass_moderator_class(self):
        class UserProfileModerator(GenericModerator):
            auto_approve_for_staff = False
            auto_approve_for_groups = ['admins', 'moderators']
            auto_reject_for_groups = ['others']
        
        moderator = UserProfileModerator(UserProfile)
        self.assertEqual(moderator.model_class, UserProfile)
        self.assertEqual(moderator.manager_names, ['objects'])
        self.assertEqual(moderator.moderation_manager_class,
                         ModerationObjectsManager)
        self.assertEqual(moderator.auto_approve_for_staff, False)
        self.assertEqual(moderator.auto_approve_for_groups, ['admins',
                                                             'moderators'])
        self.assertEqual(moderator.auto_reject_for_groups, ['others'])
        
    def test_send_notification(self):
        moderator = GenericModerator(UserProfile)
        moderator.send(self.user,
            subject_template='moderation/notification_subject_moderator.txt',
            message_template='moderation/notification_message_moderator.txt',
            recipient_list=['test@eample.com'])
        
        self.assertEqual(len(mail.outbox), 1)
        
    def test_inform_moderator(self):
        moderator = GenericModerator(UserProfile)
        moderator.inform_moderator(self.user)

        self.assertEqual(len(mail.outbox), 1)
        
    def test_inform_user(self):
        moderator = GenericModerator(UserProfile)
        moderator.inform_user(self.user, self.user)
        self.assertEqual(len(mail.outbox), 1)


class BaseManagerTestCase(unittest.TestCase):
    
    def setUp(self):
        from django.db import models
        self.moderator = GenericModerator(UserProfile)
        
        class CustomManager(models.Manager):
            
            pass
        
        class ModelClass(models.Model):
            
            pass
        
        self.custom_manager = CustomManager
        self.model_class = ModelClass

    def test_get_base_manager(self):
        self.model_class.add_to_class('objects', self.custom_manager())

        base_manager = self.moderator._get_base_manager(self.model_class,
                                                         'objects')
        
        self.assertEqual(base_manager, self.custom_manager)
        
        delattr(self.model_class, 'objects')

    def test_get_base_manager_default_manager(self):
        base_manager = self.moderator._get_base_manager(self.model_class,
                                                         'objects')
        self.assertEqual(base_manager, Manager)
