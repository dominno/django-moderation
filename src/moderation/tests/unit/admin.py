import unittest
from moderation.tests.utils.request_factory import RequestFactory
from moderation.admin import ModerationAdmin, approve_objects, reject_objects,\
    ModeratedObjectAdmin, set_objects_as_pending
from django.test.testcases import TestCase
from moderation.models import ModeratedObject,\
    MODERATION_DRAFT_STATE, MODERATION_STATUS_APPROVED,\
    MODERATION_STATUS_REJECTED, MODERATION_STATUS_PENDING
from django.contrib.admin.sites import site
from django.contrib.auth.models import User

from moderation.tests.apps.test_app1.models import UserProfile, \
    ModelWithSlugField, ModelWithSlugField2, SuperUserProfile
from django.core.exceptions import ObjectDoesNotExist
from moderation.filterspecs import ContentTypeFilterSpec
from moderation.tests.utils import setup_moderation, teardown_moderation
from moderation.tests.utils.testsettingsmanager import SettingsTestCase


class ModeratedObjectAdminTestCase(TestCase):
    fixtures = ['test_users.json']
    urls = 'moderation.tests.urls.default'

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
        self.assertEqual(repr(form),
                         "<class 'moderation.admin.ModeratedObjectForm'>")


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

    def test_queryset_should_return_only_moderation_ready_objects(self):
        qs = self.admin.queryset(self.request)
        qs = qs.filter(moderation_state=MODERATION_DRAFT_STATE)
        self.assertEqual(list(qs), [])

    def test_approve_objects(self):
        approve_objects(self.admin, self.request, self.moderated_objects)

        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.moderation_status,
                             MODERATION_STATUS_APPROVED)

    def test_reject_objects(self):
        qs = ModeratedObject.objects.all()

        reject_objects(self.admin, self.request, qs)

        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.moderation_status,
                             MODERATION_STATUS_REJECTED)

    def test_set_objects_as_pending(self):
        for obj in self.moderated_objects:
            obj.approve(moderated_by=self.request.user)

        set_objects_as_pending(self.admin, self.request,
                               self.moderated_objects)

        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.moderation_status,
                             MODERATION_STATUS_PENDING)


class ModerationAdminSendMessageTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    urls = 'moderation.tests.urls.default'
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.moderation = setup_moderation([UserProfile])

        rf = RequestFactory()
        rf.login(username='admin', password='aaaa')
        self.request = rf.get('/admin/moderation/')
        self.request.user = User.objects.get(username='admin')
        self.admin = ModerationAdmin(UserProfile, site)

        self.profile = UserProfile.objects.get(user__username='moderator')
        self.moderated_obj = ModeratedObject(content_object=self.profile)
        self.moderated_obj.save()

    def tearDown(self):
        teardown_moderation()

    def test_send_message_when_object_has_no_moderated_object(self):
        profile = SuperUserProfile(description='Profile for new user',
                                   url='http://www.yahoo.com',
                                   user=User.objects.get(username='user1'),
                                   super_power='text')

        profile.save()

        self.moderation.register(SuperUserProfile)

        self.admin.send_message(self.request, profile.pk)

        message = self.request.user.message_set.get()
        self.assertEqual(unicode(message), u"This object is not registered "\
                                           u"with the moderation system.")

    def test_send_message_status_pending(self):
        self.moderated_obj.moderation_status = MODERATION_STATUS_PENDING
        self.moderated_obj.save()

        self.admin.send_message(self.request, self.profile.pk)

        message = self.request.user.message_set.get()
        self.assertEqual(unicode(message),
                         u"Object is not viewable on site, "\
                         u"it will be visible if moderator accepts it")

    def test_send_message_status_rejected(self):
        self.moderated_obj.moderation_status = MODERATION_STATUS_REJECTED
        self.moderated_obj.moderation_reason = u'Reason for rejection'
        self.moderated_obj.save()

        self.admin.send_message(self.request, self.profile.pk)

        message = self.request.user.message_set.get()
        self.assertEqual(unicode(message),
                         u"Object has been rejected by "\
                         u"moderator, reason: Reason for rejection")

    def test_send_message_status_approved(self):
        self.moderated_obj.moderation_status = MODERATION_STATUS_APPROVED
        self.moderated_obj.save()

        self.admin.send_message(self.request, self.profile.pk)

        message = self.request.user.message_set.get()
        self.assertEqual(unicode(message), "Object has been approved by "\
                                           "moderator and is visible on site")


class ContentTypeFilterSpecTextCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    urls = 'moderation.tests.urls.default'
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        from moderation.tests import setup_moderation

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
        filter_spec = ContentTypeFilterSpec(f, self.request, {},
                                            ModeratedObject, self.admin)

        self.assertEqual([x[1] for x in filter_spec.lookup_choices],
            [u'Model with slug field',
             u'Model with slug field2'])

        self.assertEqual(unicode(filter_spec.content_types),
                         u"[<ContentType: model with slug field>, "\
                         "<ContentType: model with slug field2>]")
