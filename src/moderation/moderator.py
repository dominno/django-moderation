from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import base
from django.db.models.fields import BooleanField
from django.db.models.manager import Manager
from django.template.loader import render_to_string
from django.conf import settings

from moderation.managers import ModerationObjectsManager


class GenericModerator(object):
    """
    Encapsulates moderation options for a given model.
    """
    manager_names = ['objects']
    moderation_manager_class = ModerationObjectsManager
    bypass_moderation_after_approval = False
    visible_until_rejected = False

    fields_exclude = []

    visibility_column = None

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
        self._validate_options()
        self.base_managers = self._get_base_managers()

        moderated_fields = getattr(model_class, 'moderated_fields', None)
        if moderated_fields:
            for field in model_class._meta.fields:
                if field.name not in moderated_fields:
                    self.fields_exclude.append(field.name)

    def is_auto_approve(self, obj, user):
        '''
        Checks if change on obj by user need to be auto approved
        Returns False if change is not auto approve or reason(Unicode) if 
        change need to be auto approved.

        Overwrite this method if you want to provide your custom logic.
        '''
        if self.auto_approve_for_groups\
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
        if self.auto_reject_for_groups\
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
                  recipient_list=recipient_list,
                  fail_silently=True)

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

    def _validate_options(self):
        if self.visibility_column:
            field_type = type(self.model_class._meta.get_field_by_name(
                self.visibility_column)[0])

            if field_type != BooleanField:
                msg = 'visibility_column field: %s on model %s should '\
                      'be BooleanField type but is %s' % (
                    self.moderator.visibility_column,
                    self.changed_object.__class__,
                    field_type)
                raise AttributeError(msg)
