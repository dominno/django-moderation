from django.db.models.manager import Manager
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from moderation.models import ModeratedObject, MODERATION_STATUS_PENDING,\
    MODERATION_STATUS_REJECTED
from django.db.models.query import QuerySet
from moderation.diff import get_changes_between_models


class MetaClass(type):

    def __new__(cls, name, bases, attrs):
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)


class ModerationObjectsManager(Manager):

    def __call__(self, base_manager, *args, **kwargs):
        return MetaClass(self.__class__.__name__,
                         (self.__class__, base_manager),
                         {'use_for_related_fields': True})

    def filter_moderated_objects(self, query_set):
        exclude_pks = []
        for object in query_set:
            try:
                changes = get_changes_between_models(
                                        object,
                                        object.moderated_object.changed_object)
                if object.moderated_object.moderation_status \
                    in [MODERATION_STATUS_PENDING,
                        MODERATION_STATUS_REJECTED] \
                    and not changes:
                    exclude_pks.append(object.pk)
            except ObjectDoesNotExist:
                pass

        return query_set.exclude(pk__in=exclude_pks)

    def get_query_set(self):
        query_set = super(ModerationObjectsManager, self).get_query_set()
        query_set = self.filter_moderated_objects(query_set)

        return query_set
