from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation.tests.test_app.models import UserProfile
from moderation import GenericModerator
from moderation.managers import ModerationObjectsManager
from django.core import mail
from django.contrib.auth.models import User, Group
from moderation.models import ModeratedObject
from django.db.models.manager import Manager
import unittest
from django.test.testcases import TestCase
from mock import Mock


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


class AutoModerateModeratorTestCase(TestCase):
    fixtures = ['test_users.json']
    
    def setUp(self):
        self.user = User.objects.get(username='admin')
        self.moderator = GenericModerator(UserProfile)

    def test_is_auto_approve_user_superuser(self):
        self.moderator.auto_approve_for_superusers = True
        self.user.is_superuser = True
        self.assertTrue(self.moderator.is_auto_approve(self.user))

    def test_is_auto_approve_user_is_staff(self):
        self.moderator.auto_approve_for_staff = True
        self.assertTrue(self.moderator.is_auto_approve(self.user))

    def test_is_auto_approve_not_user_superuser(self):
        self.moderator.auto_approve_for_superusers = True
        self.moderator.auto_approve_for_staff = True
        self.user.is_superuser = False
        self.user.is_staff = False
        self.assertFalse(self.moderator.is_auto_approve(self.user))

    def test_is_auto_approve_not_user_is_staff(self):
        self.moderator.auto_approve_for_staff = True
        self.user.is_staff = False
        self.user.is_superuser = False
        self.assertFalse(self.moderator.is_auto_approve(self.user))

    def test_auto_approve_for_groups_user_in_group(self):
        self.moderator.auto_approve_for_superusers = False
        self.moderator.auto_approve_for_staff = False
        self.moderator.auto_approve_for_groups = ['moderators']
        group = Group(name='moderators')
        group.save()
        self.user.groups.add(group)
        self.user.save()
        self.assertTrue(self.moderator.is_auto_approve(self.user))

    def test_auto_approve_for_groups_user_not_in_group(self):
        self.moderator.auto_approve_for_superusers = False
        self.moderator.auto_approve_for_staff = False
        self.moderator.auto_approve_for_groups = ['banned']
        self.assertFalse(self.moderator.is_auto_approve(self.user))

    def test_is_auto_reject_user_is_anonymous(self):
        self.user.is_anonymous = Mock()
        self.user.is_anonymous.return_value = True
        self.assertTrue(self.moderator.is_auto_reject(self.user))

    def test_is_auto_reject_user_is_not_anonymous(self):
        self.user.is_anonymous = Mock()
        self.user.is_anonymous.return_value = False
        self.assertFalse(self.moderator.is_auto_reject(self.user))

    def test_auto_reject_for_groups_user_in_group(self):
        self.moderator.auto_reject_for_groups = ['banned']
        group = Group(name='banned')
        group.save()
        self.user.groups.add(group)
        self.user.save()
        self.assertTrue(self.moderator.is_auto_reject(self.user))

    def test_auto_reject_for_groups_user_not_in_group(self):
        self.moderator.auto_reject_for_groups = ['banned']
        self.assertFalse(self.moderator.is_auto_reject(self.user))


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
