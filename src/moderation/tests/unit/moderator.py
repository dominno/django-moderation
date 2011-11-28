from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation.tests.apps.test_app1.models import UserProfile,\
    ModelWithVisibilityField, ModelWithWrongVisibilityField
from moderation.register import ModerationManager
from moderation.moderator import GenericModerator
from moderation.managers import ModerationObjectsManager
from django.core import mail
from django.contrib.auth.models import User, Group
from moderation.models import ModeratedObject, MODERATION_STATUS_APPROVED
from django.db.models.manager import Manager
import unittest
from django.test.testcases import TestCase
from moderation.tests.utils import setup_moderation, teardown_moderation


class GenericModeratorTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    urls = 'django-moderation.test_urls'
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.user = User.objects.get(username='admin')
        obj = ModeratedObject(content_object=self.user)
        obj.save()
        self.user.moderated_object = obj
        self.moderator = GenericModerator(UserProfile)

    def test_create_generic_moderator(self):
        self.assertEqual(self.moderator.model_class, UserProfile)
        self.assertEqual(self.moderator.manager_names, ['objects'])
        self.assertEqual(self.moderator.moderation_manager_class,
                         ModerationObjectsManager)
        self.assertEqual(self.moderator.auto_approve_for_staff, True)
        self.assertEqual(self.moderator.auto_approve_for_groups, None)
        self.assertEqual(self.moderator.auto_reject_for_groups, None)

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
        self.moderator.send(
            self.user,
            subject_template='moderation/notification_subject_moderator.txt',
            message_template='moderation/notification_message_moderator.txt',
            recipient_list=['test@example.com'])

        self.assertEqual(len(mail.outbox), 1)

    def test_inform_moderator(self):
        self.moderator = GenericModerator(UserProfile)
        self.moderator.inform_moderator(self.user)

        self.assertEqual(len(mail.outbox), 1)

    def test_inform_user(self):
        self.moderator = GenericModerator(UserProfile)
        self.moderator.inform_user(self.user, self.user)
        self.assertEqual(len(mail.outbox), 1)

    def test_moderator_should_have_field_exclude(self):
        self.assertTrue(hasattr(self.moderator, 'fields_exclude'))


class AutoModerateModeratorTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.user = User.objects.get(username='admin')
        self.moderator = GenericModerator(UserProfile)
        self.obj = object

    def test_is_auto_approve_user_superuser(self):
        self.moderator.auto_approve_for_superusers = True
        self.user.is_superuser = True
        reason = self.moderator.is_auto_approve(self.obj, self.user)
        self.assertTrue(reason)
        self.assertEqual(reason, 'Auto-approved: Superuser')

    def test_is_auto_approve_user_is_staff(self):
        self.moderator.auto_approve_for_staff = True
        self.user.is_superuser = False
        reason = self.moderator.is_auto_approve(self.obj, self.user)
        self.assertTrue(reason)
        self.assertEqual(reason, 'Auto-approved: Staff')

    def test_is_auto_approve_not_user_superuser(self):
        self.moderator.auto_approve_for_superusers = True
        self.moderator.auto_approve_for_staff = True
        self.user.is_superuser = False
        self.user.is_staff = False
        self.assertFalse(self.moderator.is_auto_approve(self.obj, self.user))

    def test_is_auto_approve_not_user_is_staff(self):
        self.moderator.auto_approve_for_staff = True
        self.user.is_staff = False
        self.user.is_superuser = False
        self.assertFalse(self.moderator.is_auto_approve(self.obj, self.user))

    def test_auto_approve_for_groups_user_in_group(self):
        self.moderator.auto_approve_for_superusers = False
        self.moderator.auto_approve_for_staff = False
        self.moderator.auto_approve_for_groups = ['moderators']
        group = Group(name='moderators')
        group.save()
        self.user.groups.add(group)
        self.user.save()
        reason = self.moderator.is_auto_approve(self.obj, self.user)
        self.assertTrue(reason)
        self.assertEqual(reason, 'Auto-approved: User in allowed group')

    def test_auto_approve_for_groups_user_not_in_group(self):
        self.moderator.auto_approve_for_superusers = False
        self.moderator.auto_approve_for_staff = False
        self.moderator.auto_approve_for_groups = ['banned']
        self.assertFalse(self.moderator.is_auto_approve(self.obj, self.user))

    def test_is_auto_reject_user_is_anonymous(self):
        from mock import Mock

        self.user.is_anonymous = Mock()
        self.user.is_anonymous.return_value = True
        reason = self.moderator.is_auto_reject(self.obj, self.user)
        self.assertTrue(reason)
        self.assertEqual(reason, u'Auto-rejected: Anonymous User')

    def test_is_auto_reject_user_is_not_anonymous(self):
        from mock import Mock

        self.user.is_anonymous = Mock()
        self.user.is_anonymous.return_value = False
        self.assertFalse(self.moderator.is_auto_reject(self.obj, self.user))

    def test_auto_reject_for_groups_user_in_group(self):
        self.moderator.auto_reject_for_groups = ['banned']
        group = Group(name='banned')
        group.save()
        self.user.groups.add(group)
        self.user.save()
        reason = self.moderator.is_auto_reject(self.obj, self.user)
        self.assertTrue(reason)
        self.assertEqual(reason, 'Auto-rejected: User in disallowed group')

    def test_auto_reject_for_groups_user_not_in_group(self):
        self.moderator.auto_reject_for_groups = ['banned']
        self.assertFalse(self.moderator.is_auto_reject(self.obj, self.user))

    def test_overwrite_automoderation_method(self):

        def akismet_spam_check(obj):
            return True

        class UserProfileModerator(GenericModerator):
            # Inside MyModelModerator, which is registered with MyModel

            def is_auto_reject(self, obj, user):
                # Auto reject spam
                if akismet_spam_check(obj):  # Check body of object for spam
                    # Body of object is spam, moderate
                    return self.reason('Auto rejected: SPAM')
                super(UserProfile, self).is_auto_reject(obj, user)

        moderator = UserProfileModerator(UserProfile)
        reason = moderator.is_auto_reject(self.obj, self.user)
        self.assertTrue(reason)
        self.assertEqual(reason, 'Auto rejected: SPAM')


class ByPassModerationTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):

        class UserProfileModerator(GenericModerator):
            bypass_moderation_after_approval = True

        self.moderation = setup_moderation([(UserProfile,
                                             UserProfileModerator)])

        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

    def tearDown(self):
        teardown_moderation()

    def test_bypass_moderation_after_approval(self):
        profile = UserProfile(description='Profile for new user',
                              url='http://www.test.com',
                              user=User.objects.get(username='user1'))
        profile.save()

        profile.moderated_object.approve(self.user)

        profile.description = 'New description'
        profile.save()

        self.assertEqual(profile.moderated_object.moderation_status,
                         MODERATION_STATUS_APPROVED)


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


class VisibilityColumnTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):

        class UserProfileModerator(GenericModerator):
            visibility_column = 'is_public'

        self.moderation = setup_moderation([(ModelWithVisibilityField,
                                             UserProfileModerator)])

        self.user = User.objects.get(username='moderator')
        #self.profile = UserProfile.objects.get(user__username='moderator')

    def tearDown(self):
        teardown_moderation()

    def _create_userprofile(self):
        profile = ModelWithVisibilityField(test='Profile for new user')
        profile.save()
        return profile

    def test_exclude_of_not_is_public_object(self):
        '''Verify new object with visibility column is accessible by manager'''
        self._create_userprofile()

        objects = ModelWithVisibilityField.objects.all()

        self.assertEqual(list(objects), [])

    def test_approved_obj_should_be_return_by_manager(self):
        '''Verify new object with visibility column is accessible '''\
        '''by manager after approve'''
        profile = self._create_userprofile()
        profile.moderated_object.approve(self.user)

        objects = ModelWithVisibilityField.objects.all()

        self.assertEqual(objects.count(), 1)

    def test_invalid_visibility_column_field_should_rise_exception(self):
        '''Verify correct exception is raised when model has '''\
        '''invalid visibility column'''

        class UserProfileModerator(GenericModerator):
            visibility_column = 'is_public'

        self.assertRaises(AttributeError,
                          self.moderation.register,
                          ModelWithWrongVisibilityField,
                          UserProfileModerator)

    def test_model_should_be_saved_properly(self):
        '''Verify that after approve of object that has visibility column '''\
        '''value is changed from False to True'''
        profile = self._create_userprofile()

        self.assertEqual(profile.is_public, False)

        profile.moderated_object.approve(self.user)

        self.assertEqual(ModelWithVisibilityField.unmoderated_objects.get()\
                         .is_public,
                         True)
