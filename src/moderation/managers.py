from django.db.models.manager import Manager
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

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
        from moderation.models import MODERATION_STATUS_PENDING,\
                MODERATION_STATUS_REJECTED
        exclude_pks = []
        for obj in query_set:
            try:
                changes = get_changes_between_models(
                                        obj,
                                        obj.moderated_object.changed_object)
                if obj.moderated_object.moderation_status \
                    in [MODERATION_STATUS_PENDING,
                        MODERATION_STATUS_REJECTED] \
                    and not changes:
                    exclude_pks.append(obj.pk)
            except ObjectDoesNotExist:
                pass

        return query_set.exclude(pk__in=exclude_pks)

    def get_query_set(self):
        query_set = super(ModerationObjectsManager, self).get_query_set()
        query_set = self.filter_moderated_objects(query_set)

        return query_set


class ModeratedObjectManager(Manager):

    def get_for_instance(self, instance):
        '''Returns ModeratedObject for given model instance'''
        return self.get(object_pk=instance.pk,
           content_type=ContentType.objects.get_for_model(instance.__class__))
