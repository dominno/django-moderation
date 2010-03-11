from django.forms.models import BaseModelForm, ModelFormMetaclass, ModelForm
from moderation.models import MODERATION_STATUS_PENDING,\
    MODERATION_STATUS_REJECTED


class BaseModeratedObjectForm(ModelForm):

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if instance:
            if instance.moderated_object.moderation_status in \
            [MODERATION_STATUS_PENDING, MODERATION_STATUS_REJECTED]:
                initial = \
                instance.moderated_object.changed_object.__dict__
                kwargs['initial'] = initial

        super(BaseModeratedObjectForm, self).__init__(*args, **kwargs)
