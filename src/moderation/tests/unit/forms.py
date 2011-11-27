from moderation.tests.apps.test_app1.models import UserProfile
from django.forms import CharField
from moderation.forms import BaseModeratedObjectForm
from moderation.register import ModerationManager
from django.contrib.auth.models import User
from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation.tests.utils import setup_moderation, teardown_moderation


class FormsTestCase(SettingsTestCase):
    fixtures = ['test_users.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.user = User.objects.get(username='moderator')

        class ModeratedObjectForm(BaseModeratedObjectForm):
            extra = CharField(required=False)

            class Meta:
                model = UserProfile

        self.ModeratedObjectForm = ModeratedObjectForm
        self.moderation = setup_moderation([UserProfile])

    def tearDown(self):
        teardown_moderation()

    def test_create_form_class(self):
        form = self.ModeratedObjectForm()
        self.assertEqual(form._meta.model.__name__, 'UserProfile')

    def test_if_form_is_initialized_new_object(self):
        profile = UserProfile(description="New description",
                              url='http://test.com',
                              user=self.user)
        profile.save()

        form = self.ModeratedObjectForm(instance=profile)
        self.assertEqual(form.initial['description'], u'New description')

    def test_if_form_is_initialized_existing_object(self):
        profile = UserProfile(description="old description",
                              url='http://test.com',
                              user=self.user)
        profile.save()

        profile.moderated_object.approve(moderated_by=self.user)

        profile.description = u"Changed description"
        profile.save()

        form = self.ModeratedObjectForm(instance=profile)

        profile = UserProfile.objects.get(id=1)

        self.assertEqual(profile.description, u"old description")
        self.assertEqual(form.initial['description'], u'Changed description')

    def test_form_when_obj_has_no_moderated_obj(self):
        self.moderation.unregister(UserProfile)
        profile = UserProfile(description="old description",
                              url='http://test.com',
                              user=self.user)
        profile.save()
        self.moderation.register(UserProfile)

        form = self.ModeratedObjectForm(instance=profile)

        self.assertEqual(form.initial['description'], u'old description')

    def test_if_form_is_initialized_new_object_with_initial(self):
        profile = UserProfile(description="New description",
                              url='http://test.com',
                              user=self.user)
        profile.save()

        form = self.ModeratedObjectForm(initial={'extra': 'value'},
                                        instance=profile)

        self.assertEqual(form.initial['description'], u'New description')
        self.assertEqual(form.initial['extra'], u'value')
