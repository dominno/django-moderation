
from moderation.tests.test_app.models import UserProfile
from moderation.forms import BaseModeratedObjectForm
from moderation import moderation
from django.contrib.auth.models import User
from moderation.tests.utils.testsettingsmanager import SettingsTestCase


class FormsTestCase(SettingsTestCase):
    fixtures = ['test_users.json']
    test_settings = 'moderation.tests.test_settings'
    
    def setUp(self):
        self.user = User.objects.get(username='moderator')
        
        class ModeratedObjectForm(BaseModeratedObjectForm):
            
            class Meta:
                model = UserProfile

        self.ModeratedObjectForm = ModeratedObjectForm
    
    def test_create_form_class(self):
        form = self.ModeratedObjectForm()
        
        self.assertEqual(form._meta.model.__name__, 'UserProfile')
        
    def test_if_form_is_initialized_new_object(self):
        moderation.register(UserProfile)
        
        profile = UserProfile(description="New descrition",
                    url='http://test.com',
                    user=self.user)
        profile.save()
        
        form = self.ModeratedObjectForm(instance=profile)
        
        self.assertEqual(form.initial,
                         {'description': u'New descrition',
                          'id': 1,
                          'url': u'http://test.com',
                          'user': 1,
                          'user_id': 1})
        
        moderation.unregister(UserProfile)
        
    def test_if_form_is_initialized_existing_object(self):
        profile = UserProfile(description="New descrition",
                    url='http://test.com',
                    user=self.user)
        profile.save()
        
        moderation.register(UserProfile)
        
        profile.description = u"Changed description"
        profile.save()
        
        form = self.ModeratedObjectForm(instance=profile)
        
        profile = UserProfile.objects.get(id=1)
        
        self.assertEqual(profile.description, u"New descrition")
        self.assertEqual(form.initial,
                         {'description': u'Changed description',
                          'id': 1,
                          'url': u'http://test.com',
                          'user': 1,
                          'user_id': 1})
        
        moderation.unregister(UserProfile)
