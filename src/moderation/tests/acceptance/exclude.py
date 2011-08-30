from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from moderation.register import ModerationManager 
from moderation.moderator import GenericModerator
from moderation.tests.apps.test_app1.models import UserProfile, \
        ModelWithModeratedFields
from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation.tests.utils import setup_moderation, teardown_moderation
from moderation.diff import get_changes_between_models
from moderation import moderation



class ExcludeAcceptanceTestCase(SettingsTestCase):
    '''
    As developer I want to have way to ignore/exclude model fields from 
    moderation
    '''
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'
    urls = 'moderation.tests.urls.default'
    
    def setUp(self):
        setup_moderation()
        
        self.client.login(username='admin', password='aaaa')
        
        class UserProfileModerator(GenericModerator):
            fields_exclude = ['url']
            
        moderation.register(UserProfile, UserProfileModerator)
    
    def tearDown(self):
        teardown_moderation()
        
    def test_excluded_field_should_not_be_moderated_when_object_is_edited(self):
        '''
        Change field that is excluded from moderation,
        go to moderation admin
        '''
        profile = UserProfile.objects.get(user__username='moderator')
        
        profile.url = 'http://dominno.pl'
        
        profile.save()
        
        url = reverse('admin:moderation_moderatedobject_change',
                      args=(profile.moderated_object.pk,))

        response = self.client.get(url, {})
        
        changes = response.context['changes']
        
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change, ('Old description',
                                             'Old description'))
        
    def test_non_excluded_field_should_be_moderated_when_object_is_edited(self):
        '''
        Change field that is not excluded from moderation,
        go to moderation admin
        '''
        profile = UserProfile.objects.get(user__username='moderator')
        
        profile.description = 'New description'
        
        profile.save()
        
        url = reverse('admin:moderation_moderatedobject_change',
                      args=(profile.moderated_object.pk,))

        
        response = self.client.get(url, {})
        
        changes = response.context['changes']
        
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change, ('Old description',
                                             'New description'))
        
    def test_excluded_field_should_not_be_moderated_when_object_is_created(self):
        '''
        Create new object, only non excluded fields are used by moderation system
        '''
        profile = UserProfile(description='Profile for new user',
                    url='http://www.dominno.com',
                    user=User.objects.get(username='user1'))
        profile.save()

        url = reverse('admin:moderation_moderatedobject_change',
                      args=(profile.moderated_object.pk,))

        
        response = self.client.get(url, {})
        
        changes = response.context['changes']
        
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].change, ('Profile for new user',
                                             'Profile for new user'))        


class ModeratedFieldsAcceptanceTestCase(SettingsTestCase):
    '''
    Test that `moderated_fields` model argument excludes all fields not listed
    '''
    test_settings = 'moderation.tests.settings.generic'
    urls = 'moderation.tests.urls.default'

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
