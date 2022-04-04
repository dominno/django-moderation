from django.contrib.auth.models import User
from django.test.testcases import TestCase

from moderation.constants import MODERATION_STATUS_APPROVED
from moderation.helpers import automoderate
from moderation.moderator import GenericModerator
from tests.models import ModelWithVisibilityField, UserProfile
from tests.utils import setup_moderation, teardown_moderation


class CSRFMiddlewareTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        setup_moderation([UserProfile])

    def tearDown(self):
        teardown_moderation()

    def test_csrf_token(self):
        profile = UserProfile(
            description='Profile for new user',
            url='http://www.yahoo.com',
            user=User.objects.get(username='user1'),
        )

        profile.save()

        user = User.objects.get(username='admin')
        self.client.force_login(user)

        url = profile.moderated_object.get_admin_moderate_url()

        post_data = {'approve': 'Approve'}

        response = self.client.post(url, post_data)

        self.assertEqual(response.status_code, 302)

        profile = UserProfile.objects.get(pk=profile.pk)

        self.assertEqual(profile.moderated_object.status, MODERATION_STATUS_APPROVED)


class AutomoderationRuntimeErrorRegressionTestCase(TestCase):
    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):
        setup_moderation([UserProfile])

        self.user = User.objects.get(username='admin')

    def tearDown(self):
        teardown_moderation()

    def test_RuntimeError(self):
        from moderation.helpers import automoderate

        profile = UserProfile.objects.get(user__username='moderator')
        profile.description = 'Change description'
        profile.save()
        profile.moderated_object.changed_by = self.user
        profile.moderated_object.save()
        automoderate(profile, self.user)
        profile.moderated_object.save()


class BypassOverwritesUpdatedObjectRegressionTestCase(TestCase):
    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):
        class BypassModerator(GenericModerator):
            visibility_column = 'is_public'
            bypass_moderation_after_approval = True

        setup_moderation([(ModelWithVisibilityField, BypassModerator)])
        self.user = User.objects.get(username='admin')

    def tearDown(self):
        teardown_moderation()

    def test_can_update_objects_with_bypass_enabled(self):
        obj = ModelWithVisibilityField.objects.create(test='initial')
        obj.save()

        # It's never been approved before, so it's now invisible
        self.assertEqual(
            [],
            list(ModelWithVisibilityField.objects.all()),
            "The ModelWithVisibilityField has never been approved and is now "
            "pending, so it should be hidden",
        )
        # So approve it
        obj.moderated_object.approve(by=self.user, reason='test')
        # Now it should be visible, with the new description
        obj = ModelWithVisibilityField.objects.get()
        self.assertEqual('initial', obj.test)

        # Now change it again. Because bypass_moderation_after_approval is
        # True, it should still be visible and we shouldn't need to approve it
        # again.
        obj.test = 'modified'
        obj.save()
        obj = ModelWithVisibilityField.objects.get()
        self.assertEqual('modified', obj.test)

        # Admin does this after saving an object. Check that it doesn't undo
        # our changes.
        automoderate(obj, self.user)
        obj = ModelWithVisibilityField.objects.get()
        self.assertEqual('modified', obj.test)
