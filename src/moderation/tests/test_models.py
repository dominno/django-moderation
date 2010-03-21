from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from django.core import management
from django.contrib.auth.models import User, Group
from moderation.tests.test_app.models import UserProfile
from moderation.models import ModeratedObject, MODERATION_STATUS_APPROVED, \
    MODERATION_STATUS_PENDING, MODERATION_STATUS_REJECTED
from django.core.exceptions import ObjectDoesNotExist
from moderation.fields import SerializedObjectField
from moderation import ModerationManager, GenericModerator


class SerializationTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

    def test_serialize_of_object(self):
        """Test if object is propertly serialized to json"""

        json_field = SerializedObjectField()
        
        self.assertEqual(json_field._serialize(self.profile),
                    '[{"pk": 1, "model": "test_app.userprofile", "fields": '\
                    '{"url": "http://www.google.com", "user": 1, '\
                    '"description": "Profile description"}}]',
                         )
 
    def test_serialize_of_many_objects(self):
        """Test if object is propertly serialized to json"""

        profile = UserProfile(description='Profile for new user',
                    url='http://www.test.com',
                    user=User.objects.get(username='user1'))
        profile.save()
        json_field = SerializedObjectField()
        
        self.assertEqual(json_field._serialize(UserProfile.objects.all()),
                       '[{"pk": 1, "model": "test_app.userprofile", '\
                       '"fields": {"url": "http://www.google.com",'\
                       ' "user": 1, "description": "Profile description"}},'\
                       ' {"pk": 2, "model": "test_app.userprofile", "fields":'\
                       ' {"url": "http://www.test.com", "user": 2, '\
                       '"description": "Profile for new user"}}]')

    def test_deserialize(self):
        value = '[{"pk": 1, "model": "test_app.userprofile", "fields": '\
                '{"url": "http://www.google.com", "user": 1, '\
                '"description": "Profile description"}}]'
        json_field = SerializedObjectField()
        object = json_field._deserialize(value)

        self.assertEqual(repr(object),
                         '<UserProfile: moderator - http://www.google.com>')
        self.assertTrue(isinstance(object, UserProfile))

    def test_deserialize_many_objects(self):
        value = '[{"pk": 1, "model": "test_app.userprofile", '\
                '"fields": {"url": "http://www.google.com",'\
                ' "user": 1, "description": "Profile description"}},'\
                ' {"pk": 2, "model": "test_app.userprofile", "fields":'\
                ' {"url": "http://www.yahoo.com", "user": 2, '\
                '"description": "Profile description 2"}}]'

        json_field = SerializedObjectField()
        objects = json_field._deserialize(value)

        self.assertTrue(isinstance(objects, list))

        self.assertTrue(isinstance(objects[0], UserProfile))
        self.assertEqual(repr(objects[0]),
                         '<UserProfile: moderator - http://www.google.com>')

        self.assertTrue(isinstance(objects[1], UserProfile))
        self.assertEqual(repr(objects[1]),
                         '<UserProfile: user1 - http://www.yahoo.com>')

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
                         "Profile description")

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
    
    def setUp(self):
        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')
        
    def test_approval_status_pending(self):
        """test if before object approval status is pending"""
        
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()
        
        self.assertEqual(moderated_object.moderation_status,
                         MODERATION_STATUS_PENDING)
        
    def test_moderate(self):
        self.profile.description = 'New description'
        self.profile.save()
        
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()
        
        self.profile.description = 'Old description'
        self.profile.save()
        
        moderated_object._moderate(MODERATION_STATUS_APPROVED,
                                   self.user, "Reason")
        
        self.assertEqual(moderated_object.moderation_status,
                         MODERATION_STATUS_APPROVED)
        self.assertEqual(moderated_object.moderated_by, self.user)
        self.assertEqual(moderated_object.moderation_reason, "Reason")
        
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
        
        moderated_object = ModeratedObject(content_object=profile)
        moderated_object.save()
        
        moderated_object.approve(self.user)
        
        user_profile = UserProfile.objects.get(url='http://www.test.com')
        
        self.assertEqual(user_profile.description, 'Profile for new user')
        
    def test_reject_moderated_object(self):
        self.profile.description = 'New description'
        self.profile.save()
        
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()
        
        self.profile.description = "Old description"
        self.profile.save()
        
        moderated_object.reject(self.user)
        
        user_profile = UserProfile.objects.get(user__username='moderator')
        
        self.assertEqual(user_profile.description, "Old description")
        self.assertEqual(moderated_object.moderation_status,
                         MODERATION_STATUS_REJECTED)

    def test_is_not_equal_instance_should_be_true(self):
        self.profile.description = 'New description'

        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        user_profile = UserProfile.objects.get(user__username='moderator')

        value = moderated_object._is_not_equal_instance(user_profile)

        self.assertEqual(value, True)

    def test_is_not_equal_instance_should_be_false(self):
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        value = moderated_object._is_not_equal_instance(self.profile)

        self.assertEqual(value, False)


class AutoModerateTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        import moderation
        self.moderation = ModerationManager()

        class UserProfileModerator(GenericModerator):
            auto_approve_for_superusers = True
            auto_approve_for_staff = True
            auto_reject_for_groups = ['banned']

        self.moderation.register(UserProfile, UserProfileModerator)

        self.old_moderation = moderation
        setattr(moderation, 'moderation', self.moderation)

        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

    def tearDown(self):
        import moderation
        self.moderation.unregister(UserProfile)
        setattr(moderation, 'moderation', self.old_moderation)

    def test_auto_approve(self):
        self.profile.description = 'New description'
        self.profile.save()

        self.profile.moderated_object.changed_by = self.user 
        self.profile.moderated_object.save()

        profile = UserProfile.objects.get(user__username='moderator')

        self.assertEqual(profile.moderated_object.moderation_status,
                         MODERATION_STATUS_APPROVED)
        self.assertEqual(profile.description, 'New description')

    def test_auto_rejest(self):
        group = Group(name='banned')
        group.save()
        self.user.groups.add(group)
        self.user.save()

        self.profile.description = 'New description'
        self.profile.save()
        self.profile.moderated_object.changed_by = self.user
        self.profile.moderated_object.save()

        profile = UserProfile.objects.get(user__username='moderator')
        # = ModeratedObject.objects.get(object_pk=profile.pk)

        self.assertEqual(profile.moderated_object.moderation_status,
                         MODERATION_STATUS_REJECTED)
        self.assertEqual(profile.description, 'Profile description')
        
    def test_auto_approve_helper_status_approved(self):
        from moderation.helpers import automoderate
        
        self.profile.description = 'New description'
        self.profile.save()

        status = automoderate(self.profile, self.user)

        self.assertEqual(status, MODERATION_STATUS_APPROVED)

        profile = UserProfile.objects.get(user__username='moderator')
        self.assertEqual(profile.description, 'New description')

    def test_auto_approve_helper_status_rejected(self):
        from moderation.helpers import automoderate

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
        self.assertEqual(profile.description, 'Profile description')
