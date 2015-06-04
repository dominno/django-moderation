from __future__ import unicode_literals
from django.forms.models import ModelForm, model_to_dict
from moderation.models import MODERATION_STATUS_PENDING,\
    MODERATION_STATUS_REJECTED
from django.core.exceptions import ObjectDoesNotExist
from moderation.utils import django_17


class BaseModeratedObjectForm(ModelForm):
    class Meta:
        if django_17():
            exclude = '__all__'

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if instance:
            try:
                if instance.moderated_object.moderation_status in\
                   [MODERATION_STATUS_PENDING, MODERATION_STATUS_REJECTED] and\
                   not instance.moderated_object.moderator.\
                   visible_until_rejected:
                    initial = model_to_dict(
                        instance.moderated_object.changed_object)
                    kwargs.setdefault('initial', {})
                    kwargs['initial'].update(initial)
            except ObjectDoesNotExist:
                pass

        super(BaseModeratedObjectForm, self).__init__(*args, **kwargs)
