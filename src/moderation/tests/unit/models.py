from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from django.core import management
from django.contrib.auth.models import User, Group
from moderation.tests.apps.test_app1.models import UserProfile,\
    SuperUserProfile, ModelWithSlugField2
from moderation.models import ModeratedObject, MODERATION_STATUS_APPROVED,\
    MODERATION_STATUS_PENDING, MODERATION_STATUS_REJECTED
from django.core.exceptions import ObjectDoesNotExist
from moderation.fields import SerializedObjectField
from moderation.register import ModerationManager, RegistrationError
from moderation.moderator import GenericModerator
from moderation.helpers import automoderate
from moderation.tests.utils import setup_moderation, teardown_moderation


class SerializationTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

    def test_serialize_of_object(self):
        """Test if object is properly serialized to json"""

        json_field = SerializedObjectField()

        self.assertEqual(
            json_field._serialize(self.profile),
            '[{"pk": 1, "model": "test_app1.userprofile", "fields": '\
            '{"url": "http://www.google.com", "user": 1, '\
            '"description": "Old description"}}]',
            )

    def test_serialize_with_inheritance(self):
        """Test if object is properly serialized to json"""

        profile = SuperUserProfile(description='Profile for new super user',
                                   url='http://www.test.com',
                                   user=User.objects.get(username='user1'),
                                   super_power='invisibility')
        profile.save()
        json_field = SerializedObjectField()

        self.assertEqual(
            json_field._serialize(profile),
            '[{"pk": 2, "model": "test_app1.superuserprofile",'\
            ' "fields": {"super_power": "invisibility"}}, '\
            '{"pk": 2, "model": "test_app1.userprofile", "fields":'\
            ' {"url": "http://www.test.com", "user": 2,'\
            ' "description": "Profile for new super user"}}]')

    def test_deserialize(self):
        value = '[{"pk": 1, "model": "test_app1.userprofile", "fields": '\
                '{"url": "http://www.google.com", "user": 1, '\
                '"description": "Profile description"}}]'
        json_field = SerializedObjectField()
        object = json_field._deserialize(value)

        self.assertEqual(repr(object),
                         '<UserProfile: moderator - http://www.google.com>')
        self.assertTrue(isinstance(object, UserProfile))

    def test_deserialize_with_inheritance(self):
        value = '[{"pk": 2, "model": "test_app1.superuserprofile",'\
                ' "fields": {"super_power": "invisibility"}}, '\
                '{"pk": 2, "model": "test_app1.userprofile", "fields":'\
                ' {"url": "http://www.test.com", "user": 2,'\
                ' "description": "Profile for new super user"}}]'

        json_field = SerializedObjectField()
        object = json_field._deserialize(value)

        self.assertTrue(isinstance(object, SuperUserProfile))
        self.assertEqual(
            repr(object),
            '<SuperUserProfile: user1 - http://www.test.com - invisibility>')

    def test_deserialzed_object(self):
        moderated_object = ModeratedObject(content_object=self.profile)
        self.profile.description = 'New description'
        moderated_object.changed_object = self.profile
        moderated_object.save()
        pk = moderated_object.pk

        moderated_object = ModeratedObject.objects.get(pk=pk)

        self.assertEqual(moderated_object.changed_object.description,
                         'New description')

        self.assertEqual(moderated_object.content_object.description,
                         u'Old description')

    def test_change_of_deserialzed_object(self):
        self.profile.description = 'New description'
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()
        pk = moderated_object.pk

        self.profile.description = 'New changed description'
        moderated_object.changed_object = self.profile.description
        moderated_object.save()

        moderated_object = ModeratedObject.objects.get(pk=pk)

        self.assertEqual(moderated_object.changed_object.description,
                         'New changed description')


class ModerateTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'
    urls = 'moderation.tests.urls.default'

    def setUp(self):
        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')
        self.moderation = setup_moderation([UserProfile])

    def tearDown(self):
        teardown_moderation()

    def test_approval_status_pending(self):
        """test if before object approval status is pending"""

        self.profile.description = 'New description'
        self.profile.save()

        self.assertEqual(self.profile.moderated_object.moderation_status,
                         MODERATION_STATUS_PENDING)

    def test_moderate(self):
        self.profile.description = 'New description'
        self.profile.save()

        self.profile.moderated_object._moderate(MODERATION_STATUS_APPROVED,
                                                self.user, "Reason")

        self.assertEqual(self.profile.moderated_object.moderation_status,
                         MODERATION_STATUS_APPROVED)
        self.assertEqual(self.profile.moderated_object.moderated_by, self.user)
        self.assertEqual(self.profile.moderated_object.moderation_reason,
                         "Reason")

    def test_approve_moderated_object(self):
        """test if after object approval new data is saved."""
        self.profile.description = 'New description'

        moderated_object = ModeratedObject(content_object=self.profile)

        moderated_object.save()

        moderated_object.approve(moderated_by=self.user)

        user_profile = UserProfile.objects.get(user__username='moderator')

        self.assertEqual(user_profile.description, 'New description')

    def test_approve_moderated_object_new_model_instance(self):
        profile = UserProfile(description='Profile for new user',
                              url='http://www.test.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        profile.moderated_object.approve(self.user)

        user_profile = UserProfile.objects.get(url='http://www.test.com')

        self.assertEqual(user_profile.description, 'Profile for new user')

    def test_reject_moderated_object(self):
        self.profile.description = 'New description'
        self.profile.save()

        self.profile.moderated_object.reject(self.user)

        user_profile = UserProfile.objects.get(user__username='moderator')

        self.assertEqual(user_profile.description, "Old description")
        self.assertEqual(self.profile.moderated_object.moderation_status,
                         MODERATION_STATUS_REJECTED)

    def test_has_object_been_changed_should_be_true(self):
        self.profile.description = 'New description'

        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        user_profile = UserProfile.objects.get(user__username='moderator')

        value = moderated_object.has_object_been_changed(user_profile)

        self.assertEqual(value, True)

    def test_has_object_been_changed_should_be_false(self):
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        value = moderated_object.has_object_been_changed(self.profile)

        self.assertEqual(value, False)


class AutoModerateTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.moderation = ModerationManager()

        class UserProfileModerator(GenericModerator):
            auto_approve_for_superusers = True
            auto_approve_for_staff = True
            auto_reject_for_groups = ['banned']

        self.moderation.register(UserProfile, UserProfileModerator)

        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

    def tearDown(self):
        teardown_moderation()

    def test_auto_approve_helper_status_approved(self):
        self.profile.description = 'New description'
        self.profile.save()

        status = automoderate(self.profile, self.user)

        self.assertEqual(status, MODERATION_STATUS_APPROVED)

        profile = UserProfile.objects.get(user__username='moderator')
        self.assertEqual(profile.description, 'New description')

    def test_auto_approve_helper_status_rejected(self):
        group = Group(name='banned')
        group.save()
        self.user.groups.add(group)
        self.user.save()

        self.profile.description = 'New description'
        self.profile.save()

        status = automoderate(self.profile, self.user)

        profile = UserProfile.objects.get(user__username='moderator')

        self.assertEqual(status,
                         MODERATION_STATUS_REJECTED)
        self.assertEqual(profile.description, u'Old description')

    def test_model_not_registered_with_moderation(self):
        obj = ModelWithSlugField2(slug='test')
        obj.save()

        self.assertRaises(RegistrationError, automoderate, obj, self.user)
