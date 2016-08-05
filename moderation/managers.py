from __future__ import unicode_literals

from django.db.models import Count, Q
from django.db.models.manager import Manager
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from . import moderation
from .constants import MODERATION_READY_STATE
from .queryset import ModeratedObjectQuerySet
from .utils import django_17, django_18


class MetaClass(type(Manager)):

    def __new__(cls, name, bases, attrs):
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)


class ModerationObjectsManager(Manager):
    class MultipleModerations(Exception):
        def __init__(self, base_object):
            self.base_object = base_object
            super(ModerationObjectsManager.MultipleModerations,
                  self).__init__(
                "Multiple moderations found for object/s: %s" %
                base_object)

    def __call__(self, base_manager, *args, **kwargs):
        return MetaClass(
            self.__class__.__name__,
            (self.__class__, base_manager),
            {'use_for_related_fields': True})

    if django_18():
        def filter_moderated_objects(self, queryset):
            # Find any objects that have more than one related ModeratedObject
            annotated_queryset = queryset\
                .annotate(num_moderation_objects=Count('_relation_object'))\
                .filter(num_moderation_objects__gt=1)

            if annotated_queryset.exists():
                # No sensible default action here. You need to override
                # filter_moderated_objects() to handle this as you see fit.
                raise self.MultipleModerations(annotated_queryset)

            filter_kwargs = {
                '_relation_object__moderation_state': MODERATION_READY_STATE,
            }

            return queryset.filter(Q(**{'_relation_object': None}) | Q(**filter_kwargs))

    else:
        # Django < 1.7 doesn't properly annotate using GenericRelation fields,
        # so we keep a copy of the old code, even though it runs N+1 queries
        def filter_moderated_objects(self, query_set):
            # We have to import this here to avoid a circular import between
            # .models and .managers
            from .models import ModeratedObject

            exclude_pks = []

            mobjs_set = ModeratedObject.objects.filter(
                content_type=ContentType.objects.get_for_model(query_set.model),
                object_pk__in=query_set.values_list('pk', flat=True))

            # TODO: Load this query in chunks to avoid huge RAM usage spikes
            mobjects = {}
            for mobject in mobjs_set:
                if mobject.object_pk in mobjects:
                    # No sensible default action here. You need to override
                    # filter_moderated_objects() to handle this as you see fit.
                    raise self.MultipleModerations(mobject)
                else:
                    mobjects[mobject.object_pk] = mobject

            full_query_set = super(ModerationObjectsManager, self).get_queryset()\
                .filter(pk__in=query_set.values_list('pk', flat=True))

            for obj in full_query_set:
                try:
                    # We cannot use dict.get() here!
                    mobject = mobjects[obj.pk] if obj.pk in mobjects else \
                        obj.moderated_object

                    if mobject.moderation_state != MODERATION_READY_STATE:
                        exclude_pks.append(obj.pk)
                except ObjectDoesNotExist:
                    pass

            return query_set.exclude(pk__in=exclude_pks)

    def exclude_objs_by_visibility_col(self, query_set):
        return query_set.exclude(**{self.moderator.visibility_column: False})

    def get_queryset(self):
        query_set = None

        try:
            query_set = super(ModerationObjectsManager, self).get_queryset()
        except AttributeError:
            query_set = super(ModerationObjectsManager, self).get_query_set()

        if self.moderator.visibility_column:
            return self.exclude_objs_by_visibility_col(query_set)

        return self.filter_moderated_objects(query_set)

    if not django_17():
        get_query_set = get_queryset
        del get_queryset

    @property
    def moderator(self):
        return moderation.get_moderator(self.model)


class ModeratedObjectManager(Manager):
    def get_queryset(self):
        return ModeratedObjectQuerySet(self.model, using=self._db)

    if not django_17():
        get_query_set = get_queryset
        del get_queryset

    def get_for_instance(self, instance):
        '''Returns ModeratedObject for given model instance'''
        try:
            moderated_object = self.get(object_pk=instance.pk,
                                        content_type=ContentType.objects
                                        .get_for_model(instance.__class__))
        except self.model.MultipleObjectsReturned:
            # Get the most recent one
            moderated_object = self.filter(object_pk=instance.pk,
                                           content_type=ContentType.objects
                                           .get_for_model(instance.__class__))\
                .order_by('-date_updated')[0]
        return moderated_object
