import six

from . import moderation
from django.db.models import base


class ModeratedModelBase(type):
    def __init__(cls, name, bases, clsdict):
        super(ModeratedModelBase, cls).__init__(name, bases, clsdict)

        if (any(x.__name__ == 'ModeratedModel' for x in cls.mro()[1:])):
            moderation.register(cls)


class ModelBase(ModeratedModelBase, base.ModelBase):
    pass


class ModeratedModel(six.with_metaclass(ModelBase, base.Model)):

    class Meta:
        abstract = True
