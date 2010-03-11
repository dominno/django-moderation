from django.db.models import base
from moderation.models import ModeratedObject, MODERATION_STATUS_PENDING,\
    MODERATION_STATUS_APPROVED
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.manager import Manager
from django.contrib.contenttypes import generic
from moderation.managers import ModerationObjectsManager
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from moderation.notifications import BaseModerationNotification


class RegistrationError(Exception):
    """Exception thrown when registration with Moderation goes wrong."""


class ModerationInfo(object):
    """Stores registration information about a model."""

    def __init__(self, model_class, manager_name, moderation_manager_class,
                 moderated_object_name, base_manager,
                 notification_class, 
                 automoderate_in_admin=False):
        """Initializes the moderation info."""
        self.model_class = model_class
        self.manager_name = manager_name
        self.moderation_manager_class = moderation_manager_class
        self.moderated_object_name = moderated_object_name
        self.base_manager = base_manager
        self.automoderate_in_admin = automoderate_in_admin
        self.notification_class = notification_class


class ModerationManager(object):

    def __init__(self):
        """Initializes the moderation manager."""

        self._registered_models = {}

    def register(self, model_class,
                 manager_name='objects',
                 moderation_manager_class=ModerationObjectsManager,
                 moderated_object_name='moderated_object',
                 notification_class=BaseModerationNotification):
        """Registers model class with moderation"""
        if model_class in self._registered_models:
            msg = "%s has been registered with Moderation." % model_class
            raise RegistrationError(msg)
        base_manager = self._get_base_manager(model_class, manager_name)

        moderation_info = ModerationInfo(model_class,
                                        manager_name,
                                        moderation_manager_class,
                                        moderated_object_name,
                                        base_manager,
                                        notification_class,
                                        )
        self._registered_models[model_class] = moderation_info
        self._and_fields_to_model_class(model_class,
                                        base_manager,
                                        manager_name,
                                        moderation_manager_class,
                                        moderated_object_name)
        self._connect_signals(model_class)
    
    def _get_base_manager(self, model_class, manager_name):
        """Returns base manager class for given model class """
        if hasattr(model_class, manager_name):
            base_manager = getattr(model_class, manager_name).__class__
        else:
            base_manager = Manager

        return base_manager

    def _connect_signals(self, model_class):
        from django.db.models import signals
        signals.pre_save.connect(self.pre_save_handler,
                                     sender=model_class)
        signals.post_save.connect(self.post_save_handler,
                                      sender=model_class)

    def _and_fields_to_model_class(
                            self, 
                            model_class,
                            base_manager,
                            manager_name='objects',
                            moderation_manager_class=ModerationObjectsManager,
                            moderated_object_name='moderated_object'):
        """Sets moderation manager on model class,
           adds generic relation to ModeratedObject,
           sets _default_manager on model class as instance of
           ModerationObjectsManager
        """
        ModerationObjectsManager = moderation_manager_class()(base_manager)
        manager = ModerationObjectsManager()
        relation_object = generic.GenericRelation(ModeratedObject,
                                               object_id_field='object_pk')
        model_class.add_to_class('old_manager', base_manager())
        model_class.add_to_class(manager_name, manager)
        model_class.add_to_class('_' + moderated_object_name, relation_object)

        def get_modarated_object(self):
            return getattr(self, '_' + moderated_object_name).get()

        model_class.add_to_class(moderated_object_name,
                                 property(get_modarated_object))

    def unregister(self, model_class):
        """Unregister model class from moderation"""
        try:
            moderation_info = self._registered_models.pop(model_class)
        except KeyError:
            msg = "%r has not been registered with Moderation." % model_class
            raise RegistrationError(msg)

        self._remove_fields(model_class, moderation_info)
        self._disconnect_signals(model_class)

    def _remove_fields(self, model_class, moderation_info):
        """Removes fields from model class and disconnects signals"""
        from django.db.models import signals
        manager = moderation_info.base_manager()

        model_class.add_to_class(moderation_info.manager_name, manager)
        delattr(model_class, moderation_info.moderated_object_name)

    def _disconnect_signals(self, model_class):
        from django.db.models import signals
        signals.pre_save.disconnect(self.pre_save_handler, model_class)
        signals.post_save.disconnect(self.post_save_handler, model_class)

    def pre_save_handler(self, sender, instance, **kwargs):
        """Update moderation object when moderation object for
           existing instance of model does not exists
        """
        if instance.pk:
            moderated_object = self._get_or_create_moderated_object(instance)
            moderated_object.save()

    def _get_or_create_moderated_object(self, instance):
        """
        Get or create ModeratedObject instance.
        If moderated object is not equal instance then serialize unchanged
        in moderated object in order to use it later in post_save_handler
        """
        pk = instance.pk
        unchanged_obj = instance.__class__._default_manager.get(pk=pk)

        try:
            moderated_object = ModeratedObject.objects.get(object_pk=pk)

            if moderated_object._is_not_equal_instance(instance):
                moderated_object.changed_object = unchanged_obj

        except ObjectDoesNotExist:
            moderated_object = ModeratedObject(content_object=unchanged_obj)
            moderated_object.changed_object = unchanged_obj

        return moderated_object

    def post_save_handler(self, sender, instance, **kwargs):
        """
        Creates new moderation object if instance is created,
        If instance exists and is only updated then save instance as
        content_object of moderated_object
        """
        pk = instance.pk

        if kwargs['created']:
            old_object = sender._default_manager.get(pk=pk)
            moderated_object = ModeratedObject(content_object=old_object)
            moderated_object.save()
            moderated_object.notification.inform_moderator()
        else:
            moderated_object = ModeratedObject.objects.get(object_pk=pk)

            if moderated_object._is_not_equal_instance(instance):
                copied_instance = self._copy_model_instance(instance)
                # save instance with data from changed_object
                moderated_object.changed_object.save()

                # save new data in moderated object
                moderated_object.changed_object = copied_instance

                moderated_object.moderation_status = MODERATION_STATUS_PENDING
                moderated_object.save()
                moderated_object.notification.inform_moderator()
                
    def _copy_model_instance(self, obj):
        initial = dict([(f.name, getattr(obj, f.name))
                    for f in obj._meta.fields
                    if not f in obj._meta.parents.values()])
        return obj.__class__(**initial)
    
    def get_notification_class(self, model_class):
        try:
            moderation_info = moderation._registered_models[model_class]
            ModerationNotification = moderation_info.notification_class
        except KeyError:
            ModerationNotification = BaseModerationNotification
    
        return ModerationNotification


moderation = ModerationManager()
