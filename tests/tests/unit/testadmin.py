from unittest import mock

from django.contrib.admin.sites import site
from django.contrib.auth.models import Permission, User
from django.test.testcases import TestCase
from django.urls import reverse

from moderation.admin import (
    ModeratedObjectAdmin,
    ModerationAdmin,
    approve_objects,
    reject_objects,
    set_objects_as_pending,
)
from moderation.constants import (
    MODERATION_STATUS_APPROVED,
    MODERATION_STATUS_PENDING,
    MODERATION_STATUS_REJECTED,
)
from moderation.models import ModeratedObject
from moderation.moderator import GenericModerator
from tests.models import (
    Book,
    ModelWithSlugField,
    ModelWithSlugField2,
    SuperUserProfile,
    UserProfile,
)
from tests.utils import setup_moderation, teardown_moderation
from tests.utils.request_factory import RequestFactory
from tests.utils.testcases import WebTestCase


class ModeratedObjectAdminTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        rf = RequestFactory()
        rf.login(username='admin', password='aaaa')
        self.request = rf.get('/admin/moderation/')
        self.request.user = User.objects.get(username='admin')
        self.admin = ModeratedObjectAdmin(ModeratedObject, site)

        for user in User.objects.all():
            ModeratedObject(content_object=user).save()

    def test_get_actions_should_not_return_delete_selected(self):
        actions = self.admin.get_actions(self.request)
        self.failIfEqual('delete_selected' in actions, True)

    def test_content_object_returns_deserialized_object(self):
        user = User.objects.get(username='admin')
        moderated_object = ModeratedObject(content_object=user)
        moderated_object.save()
        content_object = self.admin.content_object(moderated_object)
        self.assertEqual(content_object, "admin")

    def test_get_moderated_object_form(self):
        form = self.admin.get_moderated_object_form(UserProfile)
        self.assertIn('ModeratedObjectForm', repr(form))


class ModeratedObjectAdminBehaviorTestCase(WebTestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        class BookModerator(GenericModerator):
            auto_approve_for_staff = False

        self.moderation = setup_moderation([(Book, BookModerator)])

        self.user = User.objects.get(username='user1')
        self.user.user_permissions.add(Permission.objects.get(codename='change_book'))

        self.book = Book.objects.create(title="Book not modified", author="Nico")

    def tearDown(self):
        teardown_moderation()

    def test_set_changed_by_property(self):
        """even_when_auto_approve_for_staff_is_false"""
        self.assertEquals(self.book.moderated_object.changed_by, None)
        url = reverse('admin:tests_book_change', args=(self.book.pk,))
        page = self.get(url)
        form = page.form
        form['title'] = "Book modified"
        page = form.submit()
        self.assertIn(page.status_code, [302, 200])
        book = Book.unmoderated_objects.get(pk=self.book.pk)  # refetch the obj
        self.assertEquals(book.title, "Book not modified")
        moderated_obj = ModeratedObject.objects.get_for_instance(book)
        self.assertEquals(moderated_obj.changed_object.title, "Book modified")
        self.assertEquals(moderated_obj.changed_by, self.user)


class AdminActionsTestCase(TestCase):
    fixtures = ['test_users.json']
    urls = 'moderation.tests.test_urls'

    def setUp(self):
        rf = RequestFactory()
        rf.login(username='admin', password='aaaa')
        self.request = rf.get('/admin/moderation/')
        self.request.user = User.objects.get(username='admin')
        self.admin = ModeratedObjectAdmin(ModeratedObject, site)

        self.moderation = setup_moderation([User])

        for user in User.objects.all():
            ModeratedObject(content_object=user).save()

        self.moderated_objects = ModeratedObject.objects.all()

    def tearDown(self):
        teardown_moderation()

    def test_approve_objects(self):
        approve_objects(self.admin, self.request, self.moderated_objects)

        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.status, MODERATION_STATUS_APPROVED)

    def test_reject_objects(self):
        qs = ModeratedObject.objects.all()

        reject_objects(self.admin, self.request, qs)

        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.status, MODERATION_STATUS_REJECTED)

    def test_set_objects_as_pending(self):
        for obj in self.moderated_objects:
            obj.approve(by=self.request.user)

        set_objects_as_pending(self.admin, self.request, self.moderated_objects)

        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.status, MODERATION_STATUS_PENDING)


class ModerationAdminSendMessageTestCase(TestCase):
    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):
        self.moderation = setup_moderation([UserProfile])

        rf = RequestFactory()
        rf.login(username='admin', password='aaaa')
        self.request = rf.get('/admin/moderation/')
        self.request.user = User.objects.get(username='admin')
        self.request._messages = mock.Mock()
        self.admin = ModerationAdmin(UserProfile, site)

        self.profile = UserProfile.objects.get(user__username='moderator')
        self.moderated_obj = ModeratedObject(content_object=self.profile)
        self.moderated_obj.save()

    def tearDown(self):
        teardown_moderation()

    def test_send_message_when_object_has_no_moderated_object(self):
        profile = SuperUserProfile(
            description='Profile for new user',
            url='http://www.yahoo.com',
            user=User.objects.get(username='user1'),
            super_power='text',
        )

        profile.save()

        self.moderation.register(SuperUserProfile)

        self.admin.send_message(self.request, profile.pk)

        args, kwargs = self.request._messages.add.call_args
        level, message, tags = args
        self.assertEqual(
            str(message), "This object is not registered " "with the moderation system."
        )

    def test_send_message_status_pending(self):
        self.moderated_obj.status = MODERATION_STATUS_PENDING
        self.moderated_obj.save()

        self.admin.send_message(self.request, self.profile.pk)

        args, kwargs = self.request._messages.add.call_args
        level, message, tags = args
        self.assertEqual(
            str(message),
            "Object is not viewable on site, "
            "it will be visible if moderator accepts it",
        )

    def test_send_message_status_rejected(self):
        self.moderated_obj.status = MODERATION_STATUS_REJECTED
        self.moderated_obj.reason = 'Reason for rejection'
        self.moderated_obj.save()

        self.admin.send_message(self.request, self.profile.pk)

        args, kwargs = self.request._messages.add.call_args
        level, message, tags = args
        self.assertEqual(
            str(message),
            "Object has been rejected by " "moderator, reason: Reason for rejection",
        )

    def test_send_message_status_approved(self):
        self.moderated_obj.status = MODERATION_STATUS_APPROVED
        self.moderated_obj.save()

        self.admin.send_message(self.request, self.profile.pk)

        args, kwargs = self.request._messages.add.call_args
        level, message, tags = args
        self.assertEqual(
            str(message),
            "Object has been approved by " "moderator and is visible on site",
        )


try:
    from moderation.filterspecs import ContentTypeFilterSpec
except ImportError:
    # Django 1.4
    pass
else:

    class ContentTypeFilterSpecTextCase(TestCase):

        fixtures = ['test_users.json', 'test_moderation.json']

        def setUp(self):
            from tests.utils import setup_moderation

            rf = RequestFactory()
            rf.login(username='admin', password='aaaa')
            self.request = rf.get('/admin/moderation/')
            self.request.user = User.objects.get(username='admin')
            self.admin = ModerationAdmin(UserProfile, site)

            models = [ModelWithSlugField2, ModelWithSlugField]
            self.moderation = setup_moderation(models)

            self.m1 = ModelWithSlugField(slug='test')
            self.m1.save()

            self.m2 = ModelWithSlugField2(slug='test')
            self.m2.save()

        def tearDown(self):
            teardown_moderation()

        def test_content_types_and_its_order(self):
            f = ModeratedObject._meta.get_field('content_type')
            filter_spec = ContentTypeFilterSpec(
                f, self.request, {}, ModeratedObject, self.admin
            )

            self.assertEqual(
                [x[1] for x in filter_spec.lookup_choices],
                ['Model with slug field', 'Model with slug field2'],
            )

            self.assertEqual(
                str(filter_spec.content_types),
                "[<ContentType: model with slug field>, "
                "<ContentType: model with slug field2>]",
            )
