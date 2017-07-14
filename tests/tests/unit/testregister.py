from __future__ import unicode_literals

from django import VERSION
from django.contrib.auth.models import User
from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.manager import Manager
from django.test.testcases import TestCase

from unittest import skipIf, skipUnless

from moderation.constants import (MODERATION_STATUS_REJECTED,
                                  MODERATION_STATUS_APPROVED,
                                  MODERATION_STATUS_PENDING)
from moderation.helpers import import_moderator
from moderation.managers import ModerationObjectsManager
from moderation.models import ModeratedObject
from moderation.moderator import GenericModerator
from moderation.register import ModerationManager, RegistrationError
from moderation.signals import pre_moderation, post_moderation

from tests.models import Book, UserProfile, \
    ModelWithSlugField, ModelWithSlugField2, ModelWithMultipleManagers, \
    CustomModel
from tests.utils import setup_moderation, teardown_moderation

# reload is builtin in Python 2.x. Needs to  be imported for Py3k
try:
    from importlib import reload
except ImportError:
    try:
        # Python 3.2
        from imp import reload
    except:
        pass

from django.db import IntegrityError, transaction


class MyModelModerator(GenericModerator):
    pass


class RegistrationTestCase(TestCase):
    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):
        self.moderation = setup_moderation([UserProfile])
        self.user = User.objects.get(username='moderator')

    def tearDown(self):
        teardown_moderation()

    def test_get_moderator(self):
        moderator = self.moderation.get_moderator(UserProfile)

        self.assertTrue(isinstance(moderator, GenericModerator))

    def test_get_of_new_object_should_raise_exception(self):
        """Tests if after register of model class with moderation, 
           when new object is created and getting of object 
           raise ObjectDoesNotExist"""

        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        self.assertRaises(ObjectDoesNotExist, UserProfile.objects.get,
                          pk=profile.pk)

    def test_creation_of_moderated_object(self):
        """
        Test if after create of new object moderated object should be created
        """
        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        moderated_object = ModeratedObject.objects.get_for_instance(profile)

        self.assertEqual(str(moderated_object),
                         "user1 - http://www.yahoo.com")

    def test_get_of_existing_object_should_return_old_version_of_object(self):
        """Tests if after register of model class with moderation, 
            when existing object is saved, when getting of object returns 
            old version of object"""
        profile = UserProfile.objects.get(user__username='moderator')
        moderated_object = ModeratedObject(content_object=profile)
        moderated_object.save()
        moderated_object.approve(by=self.user)

        profile.description = "New description"
        profile.save()

        old_profile = UserProfile.objects.get(pk=profile.pk)

        self.assertEqual(old_profile.description, 'Old description')

    def test_can_use_object_without_moderated_object(self):
        """
        For backwards compatibility, when django-moderation is added to an
        existing project, records with no ModeratedObject should be visible
        as before.
        """

        profile = UserProfile.objects.get(user__username='moderator')
        # Pretend that it was created before django-moderation was installed,
        # by deleting the ModeratedObject.
        ModeratedObject.objects.filter(object_pk=profile.pk).delete()

        # We should be able to load it
        profile = UserProfile.objects.get(user__username='moderator')
        # And save changes to it
        profile.description = "New description"
        profile.save()
        # And now it should be invisible, because it's pending
        self.assertEqual(
            [], list(UserProfile.objects.all()),
            "The previously unmoderated object should now be invisible, "
            "because it has never been accepted.")

    def test_register(self):
        """Tests if after creation of new model instance new 
        moderation object is created"""
        UserProfile(description='Profile for new user',
                    url='http://www.yahoo.com',
                    user=User.objects.get(username='user1')).save()

        self.assertEqual(ModeratedObject.objects.all().count(), 1,
                         "New moderation object was not created"
                         " after creation of new model instance "
                         "from model class that is registered with moderation")

    def test_exception_is_raised_when_class_is_registered(self):
        self.assertRaises(RegistrationError, self.moderation.register,
                          UserProfile)

    def test_custom_moderator_should_be_registered_with_moderation(self):
        self.moderation.register(CustomModel, MyModelModerator)
        moderator_instance = self.moderation._registered_models[CustomModel]

        self.assertTrue(isinstance(moderator_instance, MyModelModerator))


class AutoDiscoverTestCase(TestCase):
    urls = 'tests.urls.auto_register'

    def setUp(self):
        self.moderation = setup_moderation()

    def tearDown(self):
        teardown_moderation()

    def test_models_should_be_registered_if_moderator_in_module(self):
        module = import_moderator('tests')

        try:  # force module reload
            reload(module)
        except:
            pass

        self.assertTrue(Book in self.moderation._registered_models)
        self.assertEqual(module.__name__,
                         'tests.moderator')


class RegisterMultipleManagersTestCase(TestCase):

    def setUp(self):
        self.moderation = ModerationManager()

        class ModelWithMultipleManagersModerator(GenericModerator):
            manager_names = ['objects', 'men', 'women']

        setup_moderation([(ModelWithMultipleManagers,
                           ModelWithMultipleManagersModerator)])

    def tearDown(self):
        teardown_moderation()

    def test_multiple_managers(self):
        obj = ModelWithMultipleManagers(gender=0)
        obj.save()

        obj2 = ModelWithMultipleManagers(gender=1)
        obj2.save()

        men = ModelWithMultipleManagers.men.all()
        women = ModelWithMultipleManagers.women.all()

        self.assertEqual(men.count(), 0)
        self.assertEqual(women.count(), 0)


class IntegrityErrorTestCase(TestCase):

    def setUp(self):
        self.moderation = setup_moderation([ModelWithSlugField])

    def tearDown(self):
        teardown_moderation()

    def test_raise_integrity_error_model_registered_with_moderation(self):
        m1 = ModelWithSlugField(slug='test')
        m1.save()

        self.assertRaises(ObjectDoesNotExist, ModelWithSlugField.objects.get,
                          slug='test')

        m2 = ModelWithSlugField(slug='test')

        if hasattr(transaction, 'atomic'):
            with transaction.atomic():
                self.assertRaises(IntegrityError, m2.save)
        else:
            self.assertRaises(IntegrityError, m2.save)

        self.assertEqual(ModeratedObject.objects.all().count(), 1)

    def test_raise_integrity_error_model_not_registered_with_moderation(self):
        m1 = ModelWithSlugField2(slug='test')
        m1.save()

        m1 = ModelWithSlugField2.objects.get(slug='test')

        m2 = ModelWithSlugField2(slug='test')
        if hasattr(transaction, 'atomic'):
            with transaction.atomic():
                self.assertRaises(IntegrityError, m2.save)
        else:
            self.assertRaises(IntegrityError, m2.save)

        self.assertEqual(ModeratedObject.objects.all().count(), 0)


class IntegrityErrorRegressionTestCase(TestCase):

    def setUp(self):
        self.moderation = ModerationManager()
        self.moderation.register(ModelWithSlugField)
        self.filter_moderated_objects = ModelWithSlugField.objects.\
            filter_moderated_objects

        def filter_moderated_objects(query_set):
            exclude_pks = []
            for obj in query_set:
                try:
                    if obj.moderated_object.status\
                       in [MODERATION_STATUS_PENDING,
                           MODERATION_STATUS_REJECTED]\
                       and obj.__dict__ == \
                       obj.moderated_object.changed_object.__dict__:
                        exclude_pks.append(object.pk)
                except ObjectDoesNotExist:
                    pass

            return query_set.exclude(pk__in=exclude_pks)

        setattr(ModelWithSlugField.objects,
                'filter_moderated_objects',
                filter_moderated_objects)

    def tearDown(self):
        self.moderation.unregister(ModelWithSlugField)

    def test_old_version_of_filter_moderated_objects_method(self):
        m1 = ModelWithSlugField(slug='test')
        m1.save()

        m2 = ModelWithSlugField(slug='test')
        if hasattr(transaction, 'atomic'):
            with transaction.atomic():
                self.assertRaises(IntegrityError, m2.save)
        else:
            self.assertRaises(IntegrityError, m2.save)

        self.assertEqual(ModeratedObject.objects.all().count(), 1)


class ModerationManagerTestCase(TestCase):
    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):
        self.moderation = setup_moderation()
        self.user = User.objects.get(username='moderator')

    def tearDown(self):
        teardown_moderation()

    def test_unregister(self):
        """Tests if model class is successfully unregistered from moderation"""
        from django.db.models import signals

        old_pre_save_receivers = [r for r in signals.pre_save.receivers]
        old_post_save_receivers = [r for r in signals.post_save.receivers]

        signals.pre_save.receivers = []
        signals.post_save.receivers = []
        self.moderation.register(UserProfile)

        self.assertNotEqual(signals.pre_save.receivers, [])
        self.assertNotEqual(signals.post_save.receivers, [])

        UserProfile(description='Profile for new user',
                    url='http://www.yahoo.com',
                    user=User.objects.get(username='user1')).save()

        self.moderation.unregister(UserProfile)

        self.assertEqual(signals.pre_save.receivers, [])
        self.assertEqual(signals.post_save.receivers, [])

        self.assertEqual(UserProfile.objects.__class__, Manager)
        self.assertEqual(hasattr(UserProfile, 'moderated_object'), False)

        signals.pre_save.receivers = old_pre_save_receivers
        signals.post_save.receivers = old_post_save_receivers

        UserProfile.objects.get(user__username='user1')

        User.objects.get(username='moderator')
        management.call_command('loaddata', 'test_moderation.json',
                                verbosity=0)

    def test_moderation_manager(self):
        moderation = ModerationManager()

        self.assertEqual(moderation._registered_models, {})

    def test_save_new_instance_after_add_and_remove_fields_from_class(self):
        """Test if after removing moderation from model class new 
        instance of model can be created"""

        class CustomManager(Manager):
            pass

        moderator = GenericModerator(UserProfile)
        self.moderation._add_fields_to_model_class(moderator)

        self.moderation._remove_fields(moderator)

        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        up = UserProfile._default_manager.filter(url='http://www.yahoo.com')
        self.assertEqual(up.count(), 1)

    @skipIf(VERSION >= (1, 10), "Skipping moderator class test because Django >= 1.10")
    def test_add_fields_to_model_class_django_1_9(self):

        class CustomManager(Manager):
            pass

        moderator = GenericModerator(UserProfile)
        self.moderation._add_fields_to_model_class(moderator)

        manager = ModerationObjectsManager()(CustomManager)()

        self.assertEqual(repr(UserProfile.objects.__class__),
                         repr(manager.__class__))
        self.assertEqual(hasattr(UserProfile, 'moderated_object'), True)

        # clean up
        self.moderation._remove_fields(moderator)

    @skipUnless(VERSION >= (1, 10), "Skipping moderator class test because Django < 1.10")
    def test_add_fields_to_model_class_django_1_10(self):
        class CustomManager(Manager):
            pass

        moderator = GenericModerator(UserProfile)
        self.moderation._add_fields_to_model_class(moderator)

        self.assertEqual(UserProfile.objects.__class__.__name__,
                         'ModeratedManager')
        self.assertEqual(hasattr(UserProfile, 'moderated_object'), True)

        # clean up
        self.moderation._remove_fields(moderator)

    def test_get_or_create_moderated_object_exist(self):
        self.moderation.register(UserProfile)
        profile = UserProfile.objects.get(user__username='moderator')

        moderator = self.moderation.get_moderator(UserProfile)

        ModeratedObject(content_object=profile).save()

        profile.description = "New description"

        unchanged_obj = self.moderation._get_unchanged_object(profile)
        obj = self.moderation._get_or_create_moderated_object(profile,
                                                              unchanged_obj,
                                                              moderator)

        self.assertNotEqual(obj.pk, None)
        self.assertEqual(obj.changed_object.description,
                         'Old description')

        self.moderation.unregister(UserProfile)

    def test_get_or_create_moderated_object_does_not_exist(self):
        profile = UserProfile.objects.get(user__username='moderator')
        profile.description = "New description"

        self.moderation.register(UserProfile)
        moderator = self.moderation.get_moderator(UserProfile)

        unchanged_obj = self.moderation._get_unchanged_object(profile)

        object = self.moderation._get_or_create_moderated_object(profile,
                                                                 unchanged_obj,
                                                                 moderator)

        self.assertEqual(object.pk, None)
        self.assertEqual(object.changed_object.description,
                         'Old description')

        self.moderation.unregister(UserProfile)

    def test_get_or_create_moderated_object_keep_history(self):
        profile = UserProfile.objects.get(user__username='moderator')
        profile.description = "New description"

        self.moderation.register(UserProfile)
        moderator = self.moderation.get_moderator(UserProfile)
        moderator.keep_history = True

        unchanged_obj = self.moderation._get_unchanged_object(profile)

        moderated_object = self.moderation._get_or_create_moderated_object(
            profile, unchanged_obj, moderator)
        self.assertEqual(moderated_object.pk, None)
        self.assertEqual(moderated_object.changed_object.description,
                         'Old description')

        moderated_object.save()

        # moderated_object should have a pk now, and since it's the first one
        # it should be 1
        self.assertEqual(1, moderated_object.pk)

        # If we call it again, we should get a new moderated_object, evidenced
        # by having no pk

        moderated_object_2 = self.moderation._get_or_create_moderated_object(
            profile, unchanged_obj, moderator)

        self.assertEqual(moderated_object_2.pk, None)
        self.assertEqual(moderated_object_2.changed_object.description,
                         'Old description')

    def test_get_unchanged_object(self):
        profile = UserProfile.objects.get(user__username='moderator')
        profile.description = "New description"

        object = self.moderation._get_unchanged_object(profile)

        self.assertEqual(object.description,
                         'Old description')


class LoadingFixturesTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.new_moderation = setup_moderation([UserProfile])
        self.user = User.objects.get(username='moderator')

    def tearDown(self):
        teardown_moderation()

    def test_loading_fixture_for_moderated_model(self):
        management.call_command('loaddata', 'test_moderation.json',
                                verbosity=0)

        self.assertEqual(UserProfile.objects.all().count(), 1)

    def test_loading_objs_from_fixture_should_not_create_moderated_obj(self):
        management.call_command('loaddata', 'test_moderation.json',
                                verbosity=0)

        profile = UserProfile.objects.get(user__username='moderator')

        self.assertRaises(ObjectDoesNotExist,
                          ModeratedObject.objects.get, object_pk=profile.pk)

    def test_moderated_object_is_created_when_not_loaded_from_fixture(self):
        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        moderated_objs = ModeratedObject.objects.filter(object_pk=profile.pk)
        self.assertEqual(moderated_objs.count(), 1)


class ModerationSignalsTestCase(TestCase):
    fixtures = ['test_users.json', 'test_moderation.json']

    def setUp(self):

        class UserProfileModerator(GenericModerator):

            notify_moderator = False

        self.moderation = setup_moderation(
            [(UserProfile, UserProfileModerator)])

        self.moderation._disconnect_signals(UserProfile)

        self.user = User.objects.get(username='moderator')
        self.profile = UserProfile.objects.get(user__username='moderator')

    def tearDown(self):
        teardown_moderation()

    def test_send_pre_moderation_signal(self):
        """check if custom_approve_handler function was called when """
        """moderation_approve signal was send"""

        def custom_pre_moderation_handler(sender, instance, status, **kwargs):
            # do some stuff with approved instance
            instance.description = 'Change description'
            instance.save()

        pre_moderation.connect(custom_pre_moderation_handler,
                               sender=UserProfile)

        pre_moderation.send(sender=UserProfile, instance=self.profile,
                            status=MODERATION_STATUS_APPROVED)

        self.assertEqual(self.profile.description, 'Change description')

    def test_send_post_moderation_signal(self):
        """check if custom_approve_handler function was called when """
        """moderation_approve signal was send"""

        def custom_post_moderation_handler(sender, instance, status, **kwargs):
            # do some stuff with approved instance
            instance.description = 'Change description'
            instance.save()

        post_moderation.connect(custom_post_moderation_handler,
                                sender=UserProfile)

        post_moderation.send(sender=UserProfile, instance=self.profile,
                             status=MODERATION_STATUS_APPROVED)

        self.assertEqual(self.profile.description, 'Change description')

    def test_connect_and_disconnect_signals(self):
        from django.db.models import signals

        old_pre_save_receivers = [r for r in signals.pre_save.receivers]
        old_post_save_receivers = [r for r in signals.post_save.receivers]

        signals.pre_save.receivers = []
        signals.post_save.receivers = []

        self.moderation._connect_signals(UserProfile)

        self.assertNotEqual(signals.pre_save.receivers, [])
        self.assertNotEqual(signals.post_save.receivers, [])

        self.moderation._disconnect_signals(UserProfile)

        self.assertEqual(signals.pre_save.receivers, [])
        self.assertEqual(signals.post_save.receivers, [])

        signals.pre_save.receivers = old_pre_save_receivers
        signals.post_save.receivers = old_post_save_receivers

    def test_after_disconnecting_signals_moderation_object(self):
        self.moderation._connect_signals(UserProfile)
        self.moderation._disconnect_signals(UserProfile)

        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        self.assertRaises(ObjectDoesNotExist, ModeratedObject.objects.get,
                          object_pk=profile.pk)

    def test_post_save_handler_for_existing_object(self):
        from django.db.models import signals

        signals.pre_save.connect(self.moderation.pre_save_handler,
                                 sender=UserProfile)
        signals.post_save.connect(self.moderation.post_save_handler,
                                  sender=UserProfile)
        profile = UserProfile.objects.get(user__username='moderator')
        moderated_object = ModeratedObject(content_object=profile)
        moderated_object.save()
        moderated_object.approve(by=self.user)

        profile.description = 'New description of user profile'
        profile.save()

        moderated_object = ModeratedObject.objects.get_for_instance(profile)

        original_object = moderated_object.changed_object
        self.assertEqual(original_object.description,
                         'New description of user profile')
        self.assertEqual(UserProfile.objects.get(pk=profile.pk).description,
                         'Old description')

        signals.pre_save.disconnect(self.moderation.pre_save_handler,
                                    UserProfile)
        signals.post_save.disconnect(self.moderation.post_save_handler,
                                     UserProfile)

    def test_pre_save_handler_for_existing_object(self):
        from django.db.models import signals

        signals.pre_save.connect(self.moderation.pre_save_handler,
                                 sender=UserProfile)

        profile = UserProfile.objects.get(user__username='moderator')

        profile.description = 'New description of user profile'
        profile.save()

        moderated_object = ModeratedObject.objects.get_for_instance(profile)

        original_object = moderated_object.changed_object
        content_object = moderated_object.content_object

        self.assertEqual(original_object.description,
                         'Old description')
        self.assertEqual(content_object.description,
                         'New description of user profile')

        signals.pre_save.disconnect(self.moderation.pre_save_handler,
                                    UserProfile)

    def test_post_save_handler_for_new_object(self):
        from django.db.models import signals

        signals.pre_save.connect(self.moderation.pre_save_handler,
                                 sender=UserProfile)
        signals.post_save.connect(self.moderation.post_save_handler,
                                  sender=UserProfile)
        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        moderated_object = ModeratedObject.objects.get_for_instance(profile)

        self.assertEqual(moderated_object.content_object, profile)

        signals.pre_save.disconnect(self.moderation.pre_save_handler,
                                    UserProfile)
        signals.post_save.disconnect(self.moderation.post_save_handler,
                                     UserProfile)

    def test_save_handler_keep_history(self):
        # de-register current Moderator and replace it with one that
        # has keep_history set to True
        from moderation import moderation

        class KeepHistoryModerator(GenericModerator):
            keep_history = True
            notify_moderator = False

        moderation.unregister(UserProfile)
        moderation.register(UserProfile, KeepHistoryModerator)

        from django.db.models import signals

        signals.pre_save.connect(self.moderation.pre_save_handler,
                                 sender=UserProfile)
        signals.post_save.connect(self.moderation.post_save_handler,
                                  sender=UserProfile)
        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        moderated_object = ModeratedObject.objects.get_for_instance(profile)

        self.assertEqual(moderated_object.content_object, profile)

        # Now update it and make sure it gets the right history object...
        profile.url = 'http://www.google.com'
        profile.save()

        moderated_object = ModeratedObject.objects.get_for_instance(profile)
        self.assertEqual(moderated_object.content_object, profile)

        # There should only be two moderated objects
        self.assertEqual(2, ModeratedObject.objects.count())

        # Approve the change
        moderated_object.approve(by=self.user,
                                 reason='Testing post save handlers')

        # There should *still* only be two moderated objects
        self.assertEqual(2, ModeratedObject.objects.count())

        signals.pre_save.disconnect(self.moderation.pre_save_handler,
                                    UserProfile)
        signals.post_save.disconnect(self.moderation.post_save_handler,
                                     UserProfile)

        self.moderation = False

    def test_pre_save_handler_for_new_object(self):
        from django.db.models import signals

        signals.pre_save.connect(self.moderation.pre_save_handler,
                                 sender=UserProfile)
        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        self.assertRaises(ObjectDoesNotExist,
                          ModeratedObject.objects.get_for_instance,
                          profile)

        signals.pre_save.disconnect(self.moderation.pre_save_handler,
                                    UserProfile)
