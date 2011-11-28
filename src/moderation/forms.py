from django.forms.models import ModelForm
from moderation.models import MODERATION_STATUS_PENDING,\
    MODERATION_STATUS_REJECTED
from django.core.exceptions import ObjectDoesNotExist


class BaseModeratedObjectForm(ModelForm):

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if instance:
            try:
                if instance.moderated_object.moderation_status in\
                   [MODERATION_STATUS_PENDING, MODERATION_STATUS_REJECTED] and\
                   not instance.moderated_object.moderator.\
                   visible_until_rejected:
                    initial =\
                    instance.moderated_object.changed_object.__dict__
                    kwargs.setdefault('initial', {})
                    kwargs['initial'].update(initial)
            except ObjectDoesNotExist:
                pass

        super(BaseModeratedObjectForm, self).__init__(*args, **kwargs)
