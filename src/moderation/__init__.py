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
from django.contrib.auth.models import Group


class RegistrationError(Exception):
    """Exception thrown when registration with Moderation goes wrong."""


class GenericModerator(object):
    """
    Encapsulates moderation options for a given model.
    """
    manager_names = ['objects']
    moderation_manager_class = ModerationObjectsManager
    bypass_moderation_after_approval = False

    auto_approve_for_superusers = True
    auto_approve_for_staff = True
    auto_approve_for_groups = None

    auto_reject_for_anonymous = True
    auto_reject_for_groups = None

    notify_moderator = True
    notify_user = True

    subject_template_moderator\
     = 'moderation/notification_subject_moderator.txt'
    message_template_moderator\
     = 'moderation/notification_message_moderator.txt'
    subject_template_user = 'moderation/notification_subject_user.txt'
    message_template_user = 'moderation/notification_message_user.txt'

    def __init__(self, model_class):
        self.model_class = model_class
        self.base_managers = self._get_base_managers()

    def is_auto_approve(self, obj, user):
        '''
        Checks if change on obj by user need to be auto approved
        Returns False if change is not auto approve or reason(Unicode) if 
        change need to be auto approved.
        
        Overwrite this method if you want to provide your custom logic.
        '''
        if self.auto_approve_for_groups \
           and self._check_user_in_groups(user, self.auto_approve_for_groups):
            return self.reason(u'Auto-approved: User in allowed group')
        if self.auto_approve_for_superusers and user.is_superuser:
            return self.reason(u'Auto-approved: Superuser')
        if self.auto_approve_for_staff and user.is_staff:
            return self.reason(u'Auto-approved: Staff')

        return False

    def is_auto_reject(self, obj, user):
        '''
        Checks if change on obj by user need to be auto rejected
        Returns False if change is not auto reject or reason(Unicode) if 
        change need to be auto rejected.
        
        Overwrite this method if you want to provide your custom logic.
        '''
        if self.auto_reject_for_groups \
         and self._check_user_in_groups(user, self.auto_reject_for_groups):
            return self.reason(u'Auto-rejected: User in disallowed group')
        if self.auto_reject_for_anonymous and user.is_anonymous():
            return self.reason(u'Auto-rejected: Anonymous User')

        return False
    
    def reason(self, reason, user=None, obj=None):
        '''Returns moderation reason for auto moderation.  Optional user 
        and object can be passed for a more custom reason.
        '''
        return reason

    def _check_user_in_groups(self, user, groups):
        for group in groups:
            try:
                group = Group.objects.get(name=group)
            except ObjectDoesNotExist:
                return False
            
            if group in user.groups.all():
                return True
            
        return False

    def send(self, content_object, subject_template, message_template,
                           recipient_list, extra_context=None):
        context = {
                'moderated_object': content_object.moderated_object,
                'content_object': content_object,
                'site': Site.objects.get_current(),
                'content_type': content_object.moderated_object.content_type}

        if extra_context:
            context.update(extra_context)

        message = render_to_string(message_template, context)
        subject = render_to_string(subject_template, context)

        send_mail(subject=subject,
                  message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=recipient_list)

    def inform_moderator(self,
            content_object,
            extra_context=None):
        '''Send notification to moderator'''
        from moderation.conf.settings import MODERATORS
        if self.notify_moderator:
            self.send(content_object=content_object,
                  subject_template=self.subject_template_moderator,
                  message_template=self.message_template_moderator,
                  recipient_list=MODERATORS)

    def inform_user(self, content_object,
                user,
                extra_context=None):
        '''Send notification to user when object is approved or rejected'''
        if extra_context:
            extra_context.update({'user': user})
        else:
            extra_context = {'user': user}
        if self.notify_user:
            self.send(content_object=content_object,
                  subject_template=self.subject_template_user,
                  message_template=self.message_template_user,
                  recipient_list=[user.email],
                   extra_context=extra_context)
    
    def _get_base_managers(self):
        base_managers = []
        
        for manager_name in self.manager_names:
            base_managers.append(
                        (manager_name,
                        self._get_base_manager(self.model_class,
                                               manager_name)))
        return base_managers
    
    def _get_base_manager(self, model_class, manager_name):
        """Returns base manager class for given model class """
        if hasattr(model_class, manager_name):
            base_manager = getattr(model_class, manager_name).__class__
        else:
            base_manager = Manager

        return base_manager


class ModerationManager(object):

    def __init__(self):
        """Initializes the moderation manager."""
        self._registered_models = {}

    def register(self, model_class, moderator_class=None):
        """Registers model class with moderation"""
        if model_class in self._registered_models:
            msg = u"%s has been registered with Moderation." % model_class
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
        relation_object = generic.GenericRelation(ModeratedObject,
                                               object_id_field='object_pk')
        
        model_class.add_to_class('_relation_object', relation_object)

        def get_modarated_object(self):
            if not hasattr(self, '_moderated_object'):
                self._moderated_object = getattr(self,
                                                 '_relation_object').get()
            return self._moderated_object
        
        model_class.add_to_class('moderated_object',
                                 property(get_modarated_object))

    def _and_fields_to_model_class(self, moderator_class_instance):
        """Sets moderation manager on model class,
           adds generic relation to ModeratedObject,
           sets _default_manager on model class as instance of
           ModerationObjectsManager
        """
        model_class = moderator_class_instance.model_class
        base_managers = moderator_class_instance.base_managers 
        moderation_manager_class\
         = moderator_class_instance.moderation_manager_class

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
        from django.db.models import signals
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
        """Update moderation object when moderation object for
           existing instance of model does not exists
        """
        #check if object was loaded from fixture, bypass moderation if so
        
        if kwargs['raw']:
            return

        unchanged_obj = self._get_unchanged_object(instance)
        moderator = self.get_moderator(sender)
        if unchanged_obj:
            moderated_obj = self._get_or_create_moderated_object(instance,
                                                                unchanged_obj)
            if moderated_obj.moderation_status != MODERATION_STATUS_APPROVED\
              and not moderator.bypass_moderation_after_approval:
                moderated_obj.save()

    def _get_unchanged_object(self, instance):
        pk = instance.pk
        try:
            unchanged_obj = instance.__class__._default_manager.get(pk=pk)
            return unchanged_obj
        except ObjectDoesNotExist:
            return None

    def _get_or_create_moderated_object(self, instance, unchanged_obj):
        """
        Get or create ModeratedObject instance.
        If moderated object is not equal instance then serialize unchanged
        in moderated object in order to use it later in post_save_handler
        """
        try:
            moderated_object\
             = ModeratedObject.objects.get_for_instance(instance)

            if moderated_object._is_not_equal_instance(instance):
                moderated_object.changed_object = unchanged_obj

        except ObjectDoesNotExist:
            moderated_object = ModeratedObject(content_object=unchanged_obj)
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
        #check if object was loaded from fixture, bypass moderation if so

        if kwargs['raw']:
            return
        
        pk = instance.pk
        moderator = self.get_moderator(sender)

        if kwargs['created']:
            old_object = sender._default_manager.get(pk=pk)
            moderated_obj = ModeratedObject(content_object=old_object)
            moderated_obj.save()
            moderator.inform_moderator(instance)
        else:
            
            moderated_obj \
             = ModeratedObject.objects.get_for_instance(instance)
             
            if moderated_obj.moderation_status == MODERATION_STATUS_APPROVED\
               and moderator.bypass_moderation_after_approval:
                return

            if moderated_obj._is_not_equal_instance(instance):
                copied_instance = self._copy_model_instance(instance)
                # save instance with data from changed_object
                moderated_obj.changed_object.save_base(raw=True)

                # save new data in moderated object
                moderated_obj.changed_object = copied_instance

                moderated_obj.moderation_status = MODERATION_STATUS_PENDING
                moderated_obj.save()
                moderator.inform_moderator(instance)

    def _copy_model_instance(self, obj):
        initial = dict([(f.name, getattr(obj, f.name))
                    for f in obj._meta.fields
                    if not f in obj._meta.parents.values()])
        return obj.__class__(**initial)


moderation = ModerationManager()
