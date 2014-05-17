from django.test.testcases import TestCase
from django.contrib.auth.models import User
from tests.models import UserProfile, \
    ModelWithSlugField2, ModelWithVisibilityField
from moderation.managers import ModerationObjectsManager
from django.db.models.manager import Manager
from moderation.models import ModeratedObject
from django.core.exceptions import MultipleObjectsReturned
from moderation.moderator import GenericModerator
from tests.utils import setup_moderation, teardown_moderation


class ModerationObjectsManagerTestCase(TestCase):
    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):

        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

        class UserProfileModerator(GenericModerator):
            visibility_column = 'is_public'

        self.moderation = setup_moderation(
            [
                UserProfile,
                (ModelWithVisibilityField, UserProfileModerator)])

    def tearDown(self):
        teardown_moderation()

    def test_moderation_objects_manager(self):
        ManagerClass = ModerationObjectsManager()(Manager)

        self.assertEqual(
            unicode(ManagerClass.__bases__),
            u"(<class 'moderation.managers.ModerationObjectsManager'>"
            u", <class 'django.db.models.manager.Manager'>)")

    def test_filter_moderated_objects_returns_empty_queryset(self):
        """Test filter_moderated_objects returns empty queryset
        for object that has moderated object"""

        ManagerClass = ModerationObjectsManager()(Manager)
        manager = ManagerClass()
        manager.model = UserProfile

        query_set = UserProfile._default_manager.all()
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        self.assertEqual(unicode(manager.filter_moderated_objects(query_set)),
                         u"[]")

    def test_filter_moderated_objects_returns_object(self):
        """Test if filter_moderated_objects return object when object 
        doesn't have moderated object or deserialized object is <> object"""
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()
        moderated_object.approve()

        self.profile.description = "New"
        self.profile.save()

        self.assertEqual(unicode(UserProfile.objects.all()),
                         u'[<UserProfile: moderator - http://www.google.com>]')

    def test_exclude_objs_by_visibility_col(self):
        ManagerClass = ModerationObjectsManager()(Manager)
        manager = ManagerClass()
        manager.model = ModelWithVisibilityField

        ModelWithVisibilityField(test='test 1').save()
        ModelWithVisibilityField(test='test 2', is_public=True).save()

        query_set = ModelWithVisibilityField.objects.all()

        query_set = manager.exclude_objs_by_visibility_col(query_set)

        self.assertEqual(
            unicode(query_set),
            u"[<ModelWithVisibilityField: test 2 - is public True>]")


class ModeratedObjectManagerTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.moderation = setup_moderation([UserProfile, ModelWithSlugField2])

        self.user = User.objects.get(username='admin')

    def tearDown(self):
        teardown_moderation()

    def test_objects_with_same_object_id(self):
        model1 = ModelWithSlugField2(slug='test')
        model1.save()

        model2 = UserProfile(description='Profile for new user',
                             url='http://www.yahoo.com',
                             user=User.objects.get(username='user1'))

        model2.save()

        self.assertRaises(MultipleObjectsReturned,
                          ModeratedObject.objects.get,
                          object_pk=model2.pk)

        moderated_obj1 = ModeratedObject.objects.get_for_instance(model1)
        moderated_obj2 = ModeratedObject.objects.get_for_instance(model2)

        self.assertEqual(repr(moderated_obj1),
                         u"<ModeratedObject: ModelWithSlugField2 object>")
        self.assertEqual(repr(moderated_obj2),
                         u'<ModeratedObject: user1 - http://www.yahoo.com>')
