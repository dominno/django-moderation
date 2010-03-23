import unittest
from moderation.tests.utils.request_factory import RequestFactory
from moderation.admin import ModerationAdmin, approve_objects, reject_objects,\
    ModeratedObjectAdmin
from django.test.testcases import TestCase
from moderation.models import ModeratedObject, MODERATION_READY_STATE,\
    MODERATION_DRAFT_STATE, MODERATION_STATUS_APPROVED,\
    MODERATION_STATUS_REJECTED
from django.contrib.admin.sites import site
from django.contrib.auth.models import User

from moderation import moderation
from moderation.tests.test_app.models import UserProfile
from django.core.exceptions import ObjectDoesNotExist


class ModerationAdminTestCase(TestCase):
    fixtures = ['test_users.json']
    urls = 'moderation.tests.test_urls'
    
    def setUp(self):
        rf = RequestFactory()
        rf.login(username='admin', password='aaaa')
        self.request = rf.get('/admin/moderation/')
        self.request.user = User.objects.get(username='admin')
        self.admin = ModeratedObjectAdmin(ModeratedObject, site)
    
    def test_get_actions_should_not_return_delete_selected(self):
        actions = self.admin.get_actions(self.request)
        self.failIfEqual('delete_selected' in actions, True)
    
    def test_content_object_returns_deserialized_object(self):
        user = User.objects.get(username='admin')
        moderated_object = ModeratedObject(content_object=user)
        moderated_object.save()
        content_object = self.admin.content_object(moderated_object)
        self.assertEqual(content_object, "admin")
        
    def test_queryset_should_return_only_moderation_ready_objects(self):
        users = User.objects.all()
        for user in users:
            ModeratedObject(content_object=user).save()
            
        object = ModeratedObject.objects.all()[0]
        object.moderation_state = MODERATION_READY_STATE
        object.save()
        
        qs = self.admin.queryset(self.request)
        qs = qs.filter(moderation_state=MODERATION_DRAFT_STATE)
        self.assertEqual(list(qs), [])
        
    def test_approve_objects(self):
        users = User.objects.all()
        for user in users:
            ModeratedObject(content_object=user).save()
        
        qs = ModeratedObject.objects.all()
        
        approve_objects(self.admin, self.request, qs)
        
        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.moderation_status,
                             MODERATION_STATUS_APPROVED)
        
    def test_reject_objects(self):
        users = User.objects.all()
        for user in users:
            ModeratedObject(content_object=user).save()
        
        qs = ModeratedObject.objects.all()
        
        reject_objects(self.admin, self.request, qs)
        
        for obj in ModeratedObject.objects.all():
            self.assertEqual(obj.moderation_status,
                             MODERATION_STATUS_REJECTED)

    def test_get_moderated_object_form(self):
        form = self.admin.get_moderated_object_form(UserProfile)
        self.assertEqual(repr(form), 
                         "<class 'moderation.admin.ModeratedObjectForm'>")
