from __future__ import unicode_literals
from django.utils.six import with_metaclass
from moderation.models import ModeratedObject, MODERATION_STATUS_PENDING,\
    MODERATION_STATUS_APPROVED, MODERATION_DRAFT_STATE
from django.core.exceptions import ObjectDoesNotExist

from django import VERSION
if VERSION >= (1, 8):
    from django.contrib.contenttypes.fields import GenericRelation
else:
    from django.contrib.contenttypes.generic import GenericRelation

from moderation.moderator import GenericModerator


class RegistrationError(Exception):
    """Exception thrown when registration with Moderation goes wrong."""


class ModerationManagerSingleton(type):

    def __init__(cls, name, bases, dict):
        super(ModerationManagerSingleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(ModerationManagerSingleton, cls)\
                .__call__(*args, **kw)

        return cls.instance


class ModerationManager(with_metaclass(ModerationManagerSingleton, object)):
    def __init__(self, *args, **kwargs):
        """Initializes the moderation manager."""
        self._registered_models = {}

        super(ModerationManager, self).__init__(*args, **kwargs)

    def register(self, model_class, moderator_class=None):
        """Registers model class with moderation"""
        if model_class in self._registered_models:
            msg = "%s has been registered with Moderation." % model_class
            raise RegistrationError(msg)
        if not moderator_class:
            moderator_class = GenericModerator

        if not issubclass(moderator_class, GenericModerator):
            msg = 'moderator_class must subclass '\
                  'GenericModerator class, found %s' % moderator_class
            raise AttributeError(msg)

        self._registered_models[model_class] = moderator_class(model_class)

        self._and_fields_to_model_class(self._registered_models[model_class])
        self._connect_signals(model_class)

    def _connect_signals(self, model_class):
        from django.db.models import signals

        signals.pre_save.connect(self.pre_save_handler,
                                 sender=model_class)
        signals.post_save.connect(self.post_save_handler,
                                  sender=model_class)

    def _add_moderated_object_to_class(self, model_class):
        if hasattr(model_class, '_relation_object'):
            relation_object = getattr(model_class, '_relation_object')
        else:
            relation_object = GenericRelation(
                ModeratedObject,
                object_id_field='object_pk')

        model_class.add_to_class('_relation_object', relation_object)

        def get_moderated_object(self):
            if not hasattr(self, '_moderated_object'):
                if self._relation_object.count() > 0:
                    self._moderated_object = getattr(self, '_relation_object')\
                        .filter().order_by('-date_updated')[0]
                else:
                    self._moderated_object = getattr(self, '_relation_object')\
                        .get()
            return self._moderated_object

        model_class.add_to_class('moderated_object',
                                 property(get_moderated_object))

    def _and_fields_to_model_class(self, moderator_class_instance):
        """Sets moderation manager on model class,
           adds generic relation to ModeratedObject,
           sets _default_manager on model class as instance of
           ModerationObjectsManager
        """
        model_class = moderator_class_instance.model_class
        base_managers = moderator_class_instance.base_managers
        moderation_manager_class = moderator_class_instance.\
            moderation_manager_class

        for manager_name, mgr_class in base_managers:
            ModerationObjectsManager = moderation_manager_class()(mgr_class)
            manager = ModerationObjectsManager()
            model_class.add_to_class('unmoderated_%s' % manager_name,
                                     mgr_class())
            model_class.add_to_class(manager_name, manager)

        self._add_moderated_object_to_class(model_class)

    def unregister(self, model_class):
        """Unregister model class from moderation"""
        try:
            moderator_instance = self._registered_models.pop(model_class)
        except KeyError:
            msg = "%r has not been registered with Moderation." % model_class
            raise RegistrationError(msg)

        self._remove_fields(moderator_instance)
        self._disconnect_signals(model_class)

    def _remove_fields(self, moderator_class_instance):
        """Removes fields from model class and disconnects signals"""

        model_class = moderator_class_instance.model_class
        base_managers = moderator_class_instance.base_managers

        for manager_name, manager_class in base_managers:
            manager = manager_class()
            delattr(model_class, 'unmoderated_%s' % manager_name)
            model_class.add_to_class(manager_name, manager)

        delattr(model_class, 'moderated_object')

    def _disconnect_signals(self, model_class):
        from django.db.models import signals

        signals.pre_save.disconnect(self.pre_save_handler, model_class)
        signals.post_save.disconnect(self.post_save_handler, model_class)

    def pre_save_handler(self, sender, instance, **kwargs):
        """
        Create a new moderation for the instance if it doesn't have any.
        If it does have a previous moderation, get that one
        """
        # check if object was loaded from fixture, bypass moderation if so
        if kwargs['raw']:
            return

        unchanged_obj = self._get_unchanged_object(instance)
        moderator = self.get_moderator(sender)
        if unchanged_obj:
            moderated_obj = self._get_or_create_moderated_object(instance,
                                                                 unchanged_obj,
                                                                 moderator)
            if moderated_obj.moderation_status != \
               MODERATION_STATUS_APPROVED and \
               not moderator.bypass_moderation_after_approval:
                moderated_obj.save()

    def _get_unchanged_object(self, instance):
        if instance.pk is None:
            return None
        pk = instance.pk
        try:
            unchanged_obj = instance.__class__._default_manager.get(pk=pk)
            return unchanged_obj
        except ObjectDoesNotExist:
            return None

    def _get_or_create_moderated_object(self, instance,
                                        unchanged_obj, moderator):
        """
        Get or create ModeratedObject instance.
        If moderated object is not equal instance then serialize unchanged
        in moderated object in order to use it later in post_save_handler
        """
        def get_new_instance(unchanged_obj):
            moderated_object = ModeratedObject(content_object=unchanged_obj)
            moderated_object.changed_object = unchanged_obj
            return moderated_object

        try:
            # if moderator.keep_history:
            #     moderated_object = get_new_instance(unchanged_obj)
            # else:
            #     moderated_object = ModeratedObject.objects.\
            #         get_for_instance(instance)

            moderated_object = ModeratedObject.objects.get_for_instance(
                instance)
            if moderated_object is None:
                moderated_object = get_new_instance(unchanged_obj)
            elif moderator.keep_history and \
                    moderated_object.has_object_been_changed(
                    instance):
                # We're keeping history and this isn't an update of an existing
                # moderation
                moderated_object = get_new_instance(unchanged_obj)

        except ObjectDoesNotExist:
            moderated_object = get_new_instance(unchanged_obj)

        else:
            if moderated_object.has_object_been_changed(instance):
                if moderator.visible_until_rejected:
                    moderated_object.changed_object = instance
                else:
                    moderated_object.changed_object = unchanged_obj

        return moderated_object

    def get_moderator(self, model_class):
        try:
            moderator_instance = self._registered_models[model_class]
        except KeyError:
            msg = "%r has not been registered with Moderation." % model_class
            raise RegistrationError(msg)

        return moderator_instance

    def post_save_handler(self, sender, instance, **kwargs):
        """
        Creates new moderation object if instance is created,
        If instance exists and is only updated then save instance as
        content_object of moderated_object
        """
        # check if object was loaded from fixture, bypass moderation if so

        if kwargs['raw']:
            return

        pk = instance.pk
        moderator = self.get_moderator(sender)

        if kwargs['created']:
            old_object = sender._default_manager.get(pk=pk)
            moderated_obj = ModeratedObject(content_object=old_object)
            if not moderator.visible_until_rejected:
                # Hide it by placing in draft state
                moderated_obj.moderation_state = MODERATION_DRAFT_STATE
            moderated_obj.save()
            moderator.inform_moderator(instance)
            return

        moderated_obj = ModeratedObject.objects.get_for_instance(instance)

        if (moderated_obj.moderation_status == MODERATION_STATUS_APPROVED and
                moderator.bypass_moderation_after_approval):
            # save new data in moderated object
            moderated_obj.changed_object = instance
            moderated_obj.save()
            return

        if moderated_obj.has_object_been_changed(instance):
            copied_instance = self._copy_model_instance(instance)

            if not moderator.visible_until_rejected:
                # Save instance with old data from changed_object, undoing
                # the changes that save() just saved to the database.
                moderated_obj.changed_object.save_base(raw=True)

                # Save the new data in moderated_object, so it will be applied
                # to the real record when the moderator approves the change.
                moderated_obj.changed_object = copied_instance

            moderated_obj.moderation_status = MODERATION_STATUS_PENDING
            moderated_obj.save()
            moderator.inform_moderator(instance)
            instance._moderated_object = moderated_obj

    def _copy_model_instance(self, obj):
        initial = dict(
            [(f.name, getattr(obj, f.name)) for f in obj._meta.fields])
        return obj.__class__(**initial)
