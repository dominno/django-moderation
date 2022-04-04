from django.contrib.auth.models import User
from django.test.testcases import TestCase
from django.urls import reverse

from moderation.moderator import GenericModerator
from tests.models import ModelWithModeratedFields, UserProfile
from tests.utils import setup_moderation, teardown_moderation


class ExcludeAcceptanceTestCase(TestCase):
    '''
    As developer I want to have way to ignore/exclude model fields from
    moderation
    '''

    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):
        self.client.force_login(User.objects.get(username='admin'))

        class UserProfileModerator(GenericModerator):
            fields_exclude = ['url']

        setup_moderation([(UserProfile, UserProfileModerator)])

    def tearDown(self):
        teardown_moderation()

    def test_excluded_field_should_not_be_moderated_when_obj_is_edited(self):
        '''
        Change field that is excluded from moderation,
        go to moderation admin
        '''
        profile = UserProfile.objects.get(user__username='moderator')

        profile.url = 'http://dominno.pl'

        profile.save()

        url = reverse(
            'admin:moderation_moderatedobject_change',
            args=(profile.moderated_object.pk,),
        )

        response = self.client.get(url, {})

        changes = [change.change for change in response.context['changes']]

        self.assertFalse(('http://www.google.com', 'http://dominno.pl') in changes)

    def test_non_excluded_field_should_be_moderated_when_obj_is_edited(self):
        '''
        Change field that is not excluded from moderation,
        go to moderation admin
        '''
        profile = UserProfile.objects.get(user__username='moderator')

        profile.description = 'New description'

        profile.save()

        url = reverse(
            'admin:moderation_moderatedobject_change',
            args=(profile.moderated_object.pk,),
        )

        response = self.client.get(url, {})

        changes = [change.change for change in response.context['changes']]

        self.assertTrue(("Old description", 'New description') in changes)

    def test_excluded_field_should_not_be_moderated_when_obj_is_created(self):
        '''
        Create new object, only non excluded fields are used
        by moderation system
        '''
        profile = UserProfile(
            description='Profile for new user',
            url='http://www.dominno.com',
            user=User.objects.get(username='user1'),
        )
        profile.save()

        url = reverse(
            'admin:moderation_moderatedobject_change',
            args=(profile.moderated_object.pk,),
        )

        response = self.client.get(url, {})

        changes = [change.change for change in response.context['changes']]

        self.assertFalse(
            ('http://www.dominno.com', 'http://www.dominno.com') in changes
        )

    def test_excluded_field_should_always_be_saved(self):
        '''
        Ensure that excluded fields are always saved to the object.
        '''
        profile = UserProfile(
            description='Profile for new user',
            url='http://www.dominno.com',
            user=User.objects.get(username='user1'),
        )
        profile.save()
        profile.moderated_object.approve()

        profile = UserProfile.objects.get(id=profile.id)
        profile.description = 'New profile'
        profile.save()
        profile.url = 'http://dominno.pl'
        profile.save()
        profile.moderated_object.approve()
        profile = UserProfile.objects.get(id=profile.id)

        self.assertEqual(profile.description, 'New profile')
        self.assertEqual(profile.url, 'http://dominno.pl')

        profile.url = 'http://www.google.com'
        profile.save()
        profile.moderated_object.approve()
        profile = UserProfile.objects.get(id=profile.id)

        self.assertEqual(profile.url, 'http://www.google.com')


class ModeratedFieldsAcceptanceTestCase(TestCase):
    '''
    Test that `moderated_fields` model argument excludes all fields not listed
    '''

    def setUp(self):
        setup_moderation([ModelWithModeratedFields])

    def tearDown(self):
        teardown_moderation()

    def test_moderated_fields_not_added_to_excluded_fields_list(self):
        from moderation import moderation

        moderator = moderation._registered_models[ModelWithModeratedFields]

        self.assertTrue('moderated' not in moderator.fields_exclude)
        self.assertTrue('also_moderated' not in moderator.fields_exclude)

    def test_unmoderated_fields_added_to_excluded_fields_list(self):
        from moderation import moderation

        moderator = moderation._registered_models[ModelWithModeratedFields]

        self.assertTrue('unmoderated' in moderator.fields_exclude)
