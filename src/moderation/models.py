from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

from moderation.diff import get_changes_between_models
from moderation.fields import SerializedObjectField
from moderation.signals import post_moderation, pre_moderation
from moderation.managers import ModeratedObjectManager

import datetime

# Register new ContentTypeFilterSpec
import moderation.filterspecs


MODERATION_READY_STATE = 0
MODERATION_DRAFT_STATE = 1

MODERATION_STATUS_REJECTED = 0
MODERATION_STATUS_APPROVED = 1
MODERATION_STATUS_PENDING = 2

MODERATION_STATES = (
        (MODERATION_READY_STATE, 'Ready for moderation'),
        (MODERATION_DRAFT_STATE, 'Draft'),
    )

STATUS_CHOICES = (
        (MODERATION_STATUS_APPROVED, "Approved"),
        (MODERATION_STATUS_PENDING, "Pending"),
        (MODERATION_STATUS_REJECTED, "Rejected"),
    )


class ModeratedObject(models.Model):
    content_type = models.ForeignKey(ContentType, null=True, blank=True,
                                     editable=False)
    object_pk = models.PositiveIntegerField(null=True, blank=True,
                                            editable=False)
    content_object = generic.GenericForeignKey(ct_field="content_type",
                                               fk_field="object_pk")
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    moderation_state = models.SmallIntegerField(choices=MODERATION_STATES,
                                                default=MODERATION_READY_STATE,
                                                editable=False)
    moderation_status = models.SmallIntegerField(
        choices=STATUS_CHOICES,
        default=MODERATION_STATUS_PENDING,
        editable=False)
    moderated_by = models.ForeignKey(
        User, blank=True, null=True,
        editable=False, related_name='moderated_by_set')
    moderation_date = models.DateTimeField(editable=False, blank=True,
                                           null=True)
    moderation_reason = models.TextField(blank=True, null=True)
    changed_object = SerializedObjectField(serialize_format='json',
                                           editable=False)
    changed_by = models.ForeignKey(
        User, blank=True, null=True,
        editable=True, related_name='changed_by_set')

    objects = ModeratedObjectManager()

    content_type.content_type_filter = True

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('content_object')
        super(ModeratedObject, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return u"%s" % self.changed_object

    def save(self, *args, **kwargs):
        if self.instance:
            self.changed_object = self.instance

        super(ModeratedObject, self).save(*args, **kwargs)

    class Meta:
        ordering = ['moderation_status', 'date_created']

    def automoderate(self, user=None):
        '''Auto moderate object for given user.
          Returns status of moderation.
        '''
        if user is None:
            user = self.changed_by
        else:
            self.changed_by = user

        if self.moderator.visible_until_rejected:
            changed_object = self.get_object_for_this_type()
        else:
            changed_object = self.changed_object
        moderate_status, reason = self._get_moderation_status_and_reason(
            changed_object,
            user)

        if moderate_status == MODERATION_STATUS_REJECTED:
            self.reject(moderated_by=self.moderated_by, reason=reason)
        elif moderate_status == MODERATION_STATUS_APPROVED:
            self.approve(moderated_by=self.moderated_by, reason=reason)

        return moderate_status

    def _get_moderation_status_and_reason(self, obj, user):
        '''
        Returns tuple of moderation status and reason for auto moderation
        '''
        reason = self.moderator.is_auto_reject(obj, user)
        if reason:
            return MODERATION_STATUS_REJECTED, reason
        else:
            reason = self.moderator.is_auto_approve(obj, user)
            if reason:
                return MODERATION_STATUS_APPROVED, reason

        return MODERATION_STATUS_PENDING, None

    def get_object_for_this_type(self):
        pk = self.object_pk
        obj = self.content_type.model_class()._default_manager.get(pk=pk)
        return obj

    def get_absolute_url(self):
        if hasattr(self.changed_object, 'get_absolute_url'):
            return self.changed_object.get_absolute_url()
        return None

    def get_admin_moderate_url(self):
        return u"/admin/moderation/moderatedobject/%s/" % self.pk

    @property
    def moderator(self):
        from moderation import moderation

        model_class = self.content_object.__class__

        return moderation.get_moderator(model_class)

    def _moderate(self, status, moderated_by, reason):
        self.moderation_status = status
        self.moderation_date = datetime.datetime.now()
        self.moderated_by = moderated_by
        self.moderation_reason = reason

        if status == MODERATION_STATUS_APPROVED:
            if self.moderator.visible_until_rejected:
                try:
                    obj_class = self.changed_object.__class__
                    pk = self.changed_object.pk
                    unchanged_obj = obj_class._default_manager.get(pk=pk)
                except obj_class.DoesNotExist:
                    unchanged_obj = None
                self.changed_object = unchanged_obj

            if self.moderator.visibility_column:
                setattr(self.changed_object, self.moderator.visibility_column,
                        True)

            self.save()
            self.changed_object.save()

        else:
            self.save()
        if status == MODERATION_STATUS_REJECTED and\
           self.moderator.visible_until_rejected:
            self.changed_object.save()

        if self.changed_by:
            self.moderator.inform_user(self.content_object, self.changed_by)

    def has_object_been_changed(self, original_obj, fields_exclude=None):
        if fields_exclude is None:
            fields_exclude = self.moderator.fields_exclude
        changes = get_changes_between_models(original_obj,
                                             self.changed_object,
                                             fields_exclude)

        for change in changes:
            left_change, right_change = changes[change].change
            if left_change != right_change:
                return True

        return False

    def approve(self, moderated_by=None, reason=None):
        pre_moderation.send(sender=self.content_object.__class__,
                            instance=self.changed_object,
                            status=MODERATION_STATUS_APPROVED)

        self._moderate(MODERATION_STATUS_APPROVED, moderated_by, reason)

        post_moderation.send(sender=self.content_object.__class__,
                             instance=self.content_object,
                             status=MODERATION_STATUS_APPROVED)

    def reject(self, moderated_by=None, reason=None):
        pre_moderation.send(sender=self.content_object.__class__,
                            instance=self.changed_object,
                            status=MODERATION_STATUS_REJECTED)
        self._moderate(MODERATION_STATUS_REJECTED, moderated_by, reason)
        post_moderation.send(sender=self.content_object.__class__,
                             instance=self.content_object,
                             status=MODERATION_STATUS_REJECTED)
