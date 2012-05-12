from django.forms.models import ModelForm, model_to_dict
from moderation.models import MODERATION_STATUS_PENDING,\
    MODERATION_STATUS_REJECTED
from django.core.exceptions import ObjectDoesNotExist

def make_moderatedform_from_modelform(parent_form_class, obj=None):
    outer_obj = obj
    class ModeratedForm(parent_form_class):
        """This form isngores kwargs['instance'] for purposes of kwargs['initial']"""
        def __init__(self, *args, **kwargs):
            if outer_obj:
                initial = moderated_modelform_kwargs(outer_obj)
                kwargs.update(initial)
            elif 'instance' in kwargs:
                initial = moderated_modelform_kwargs(kwargs['instance'])
                kwargs.update(initial)
            return super(ModeratedForm, self).__init__(*args, **kwargs)
    return ModeratedForm

def moderated_modelform_kwargs(instance):
    if not instance:
        return {}
    try:
        if instance.moderated_object.moderation_status in\
           [MODERATION_STATUS_PENDING, MODERATION_STATUS_REJECTED] and\
           not instance.moderated_object.moderator.\
           visible_until_rejected:
            initial =\
            model_to_dict(instance.moderated_object.changed_object)
            return {'initial': initial}
        return {}
    except ObjectDoesNotExist:
        return {}

