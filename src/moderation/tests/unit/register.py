from django.contrib.auth.models import User
from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.manager import Manager

from moderation.register import ModerationManager, RegistrationError
from moderation.moderator import GenericModerator
from moderation.managers import ModerationObjectsManager
from moderation.models import ModeratedObject, MODERATION_STATUS_APPROVED
from moderation.signals import pre_moderation, post_moderation
from moderation.tests.apps.test_app1.models import UserProfile, \
    ModelWithSlugField, ModelWithSlugField2, ModelWithMultipleManagers
from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from moderation.tests.utils import setup_moderation
from moderation.tests.utils import teardown_moderation
from moderation.helpers import import_moderator
from moderation.tests.apps.test_app2.models import Book

import unittest
from django.db import IntegrityError


class RegistrationTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

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

        self.assertEqual(unicode(moderated_object),
                         u"user1 - http://www.yahoo.com")

    def test_get_of_existing_object_should_return_old_version_of_object(self):
        """Tests if after register of model class with moderation, 
            when existing object is saved, when getting of object returns 
            old version of object"""
        profile = UserProfile.objects.get(user__username='moderator')

        profile.description = "New description"
        profile.save()

        old_profile = UserProfile.objects.get(pk=profile.pk)

        self.assertEqual(old_profile.description, u'Old description')

    def test_register(self):
        """Tests if after creation of new model instance new 
        moderation object is created"""
        UserProfile(description='Profile for new user',
                    url='http://www.yahoo.com',
                    user=User.objects.get(username='user1')).save()

        self.assertEqual(ModeratedObject.objects.all().count(),
                         1,
                         "New moderation object was not created"\
                         " after creation of new model instance "\
                         "from model class that is registered with moderation")

    def test_exception_is_raised_when_class_is_registered(self):
        self.assertRaises(RegistrationError, self.moderation.register,
                          UserProfile)

    def test_custom_moderator_should_be_registered_with_moderation(self):
        from moderation.moderator import GenericModerator
        from django.db import models

        class MyModel(models.Model):
            pass

        class MyModelModerator(GenericModerator):
            pass

        self.moderation.register(MyModel, MyModelModerator)

        moderator_instance = self.moderation._registered_models[MyModel]

        self.assertTrue(isinstance(moderator_instance, MyModelModerator))


class AutoDiscoverTestCase(SettingsTestCase):
    test_settings = 'moderation.tests.settings.auto_discover'

    def setUp(self):
        self.moderation = setup_moderation()

    def tearDown(self):
        teardown_moderation()

    def test_models_should_be_registered_if_moderator_in_module(self):
        module = import_moderator('moderation.tests.apps.test_app2')

        try:  # force module reload
            reload(module)
        except:
            pass

        self.assertTrue(Book in self.moderation._registered_models)
        self.assertEqual(module.__name__,
                         'moderation.tests.apps.test_app2.moderator')


class RegisterMultipleManagersTestCase(SettingsTestCase):
    test_settings = 'moderation.tests.settings.generic'

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


class IntegrityErrorTestCase(SettingsTestCase):
    test_settings = 'moderation.tests.settings.generic'

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
        self.assertRaises(IntegrityError, m2.save)

        self.assertEqual(ModeratedObject.objects.all().count(), 1)

    def test_raise_integrity_error_model_not_registered_with_moderation(self):
        m1 = ModelWithSlugField2(slug='test')
        m1.save()

        m1 = ModelWithSlugField2.objects.get(slug='test')

        m2 = ModelWithSlugField2(slug='test')
        self.assertRaises(IntegrityError, m2.save)

        self.assertEqual(ModeratedObject.objects.all().count(), 0)


class IntegrityErrorRegressionTestCase(SettingsTestCase):
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.moderation = ModerationManager()
        self.moderation.register(ModelWithSlugField)
        self.filter_moderated_objects\
        = ModelWithSlugField.objects.filter_moderated_objects

        def filter_moderated_objects(query_set):
            from moderation.models import MODERATION_STATUS_PENDING,\
                MODERATION_STATUS_REJECTED

            exclude_pks = []
            for obj in query_set:
                try:
                    if obj.moderated_object.moderation_status\
                       in [MODERATION_STATUS_PENDING,
                           MODERATION_STATUS_REJECTED]\
                    and obj.__dict__\
                    == obj.moderated_object.changed_object.__dict__:
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
        self.assertRaises(IntegrityError, m2.save)

        self.assertEqual(ModeratedObject.objects.all().count(), 1)


class ModerationManagerTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    urls = 'django-moderation.test_urls'
    test_settings = 'moderation.tests.settings.generic'

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
        from django.db.models import signals

        class CustomManager(Manager):
            pass

        moderator = GenericModerator(UserProfile)
        self.moderation._and_fields_to_model_class(moderator)

        self.moderation._remove_fields(moderator)

        profile = UserProfile(description='Profile for new user',
                              url='http://www.yahoo.com',
                              user=User.objects.get(username='user1'))

        profile.save()

        up = UserProfile._default_manager.filter(url='http://www.yahoo.com')
        self.assertEqual(up.count(), 1)

    def test_and_fields_to_model_class(self):

        class CustomManager(Manager):
            pass

        moderator = GenericModerator(UserProfile)
        self.moderation._and_fields_to_model_class(moderator)

        manager = ModerationObjectsManager()(CustomManager)()

        self.assertEqual(repr(UserProfile.objects.__class__),
                         repr(manager.__class__))
        self.assertEqual(hasattr(UserProfile, 'moderated_object'), True)

        #clean up
        self.moderation._remove_fields(moderator)

    def test_get_or_create_moderated_object_exist(self):
        self.moderation.register(UserProfile)
        profile = UserProfile.objects.get(user__username='moderator')

        moderator = self.moderation.get_moderator(UserProfile)

        ModeratedObject(content_object=profile).save()

        profile.description = "New description"

        unchanged_obj = self.moderation._get_unchanged_object(profile)
        object = self.moderation._get_or_create_moderated_object(profile,
                                                                 unchanged_obj,
                                                                 moderator)

        self.assertNotEqual(object.pk, None)
        self.assertEqual(object.changed_object.description,
                         u'Old description')

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
                         u'Old description')

        self.moderation.unregister(UserProfile)

    def test_get_unchanged_object(self):
        profile = UserProfile.objects.get(user__username='moderator')
        profile.description = "New description"

        object = self.moderation._get_unchanged_object(profile)

        self.assertEqual(object.description,
                         u'Old description')


class LoadingFixturesTestCase(SettingsTestCase):
    fixtures = ['test_users.json']
    test_settings = 'moderation.tests.settings.generic'

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


class ModerationSignalsTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

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
        ModeratedObject(content_object=profile).save()

        profile.description = 'New description of user profile'
        profile.save()

        moderated_object = ModeratedObject.objects.get_for_instance(profile)

        original_object = moderated_object.changed_object
        self.assertEqual(original_object.description,
                         'New description of user profile')
        self.assertEqual(UserProfile.objects.get(pk=profile.pk).description,
                         u'Old description')

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
                         u'Old description')
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
