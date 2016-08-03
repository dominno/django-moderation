from django.db.models.query import QuerySet

from . import moderation
from .constants import (MODERATION_READY_STATE,
                        MODERATION_STATUS_REJECTED,
                        MODERATION_STATUS_APPROVED)
from .signals import post_many_moderation, pre_many_moderation


class ModeratedObjectQuerySet(QuerySet):
    def approve(self, cls, moderated_by, reason=None):
        self._send_signals_and_moderate(cls, MODERATION_STATUS_APPROVED, moderated_by, reason)

    def reject(self, cls, moderated_by, reason=None):
        self._send_signals_and_moderate(cls, MODERATION_STATUS_REJECTED, moderated_by, reason)

    def moderator(self, cls):
        return moderation.get_moderator(cls)

    def _send_signals_and_moderate(self, cls, new_status, by, reason):
        pre_many_moderation.send(sender=cls,
                                 queryset=self,
                                 status=new_status,
                                 moderated_by=by,
                                 reason=reason)

        self._moderate(cls, new_status, moderated_by, reason)

        post_many_moderation.send(sender=cls,
                                  queryset=self,
                                  status=new_status,
                                  moderated_by=by,
                                  reason=reason)

    def _moderate(self, cls, new_status, by, reason):
        mod = self.moderator(cls)
        ct = ContentType.objects.get_for_model(cls)

        if new_status == MODERATION_STATUS_APPROVED and mod.visibile_until_rejected:
            base_object_force_save = True
        else:
            base_object_force_save = False

        update_kwargs = {
            'moderation_status': new_status,
            'moderation_date': datetime.now(),
            'moderated_by': by,
            'moderation_reason': reason,
        }
        if new_status == MODERATION_STATUS_APPROVED:
            update_kwargs['moderation_state'] = MODERATION_READY_STATE

        self.update(update_kwargs)

        if mod.visibility_column:
            if new_status == MODERATION_STATUS_APPROVED:
                new_visible = True
            elif new_status == MODERATION_STATUS_REJECTED:
                new_visible = False
            else:  # MODERATION_STATUS_PENDING
                new_visible = mod.visibile_until_rejected

            cls.objects.filter(
                id__in=self.filter(content_type=ct)
                           .values_list('object_id', flat=True))\
               .update(**{mod.visibility_column: new_visible})

        mod.inform_users(self.exclude(changed_by=None).select_related('changed_by__email'))
