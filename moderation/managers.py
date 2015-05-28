from __future__ import unicode_literals
from django.db.models.manager import Manager
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from moderation.utils import django_17


class MetaClass(type(Manager)):

    def __new__(cls, name, bases, attrs):
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)


class ModerationObjectsManager(Manager):
    class MultipleModerations(Exception):
        def __init__(self, base_object):
            self.base_object = base_object
            super(ModerationObjectsManager.MultipleModerations,
                  self).__init__(
                "Multiple moderations found for a single object, %s" %
                base_object)

    def __call__(self, base_manager, *args, **kwargs):
        return MetaClass(
            self.__class__.__name__,
            (self.__class__, base_manager),
            {'use_for_related_fields': True})

    def filter_moderated_objects(self, query_set):
        from moderation.models import MODERATION_READY_STATE

        exclude_pks = []

        from .models import ModeratedObject

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

        full_query_set = None

        if django_17():
            full_query_set = super(ModerationObjectsManager, self).get_queryset()\
                .filter(pk__in=query_set.values_list('pk', flat=True))
        else:
            full_query_set = super(ModerationObjectsManager, self).get_query_set()\
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
        from moderation.models import MODERATION_STATUS_REJECTED

        kwargs = {}
        kwargs[self.moderator.visibility_column] =\
            bool(MODERATION_STATUS_REJECTED)

        return query_set.exclude(**kwargs)

    def get_queryset(self):
        query_set = None

        if django_17():
            query_set = super(ModerationObjectsManager, self).get_queryset()
        else:
            query_set = super(ModerationObjectsManager, self).get_query_set()

        if self.moderator.visibility_column:
            return self.exclude_objs_by_visibility_col(query_set)

        return self.filter_moderated_objects(query_set)

    if not django_17():
        get_query_set = get_queryset
        del get_queryset

    @property
    def moderator(self):
        from moderation import moderation

        return moderation.get_moderator(self.model)


class ModeratedObjectManager(Manager):
    def get_for_instance(self, instance):
        '''Returns ModeratedObject for given model instance'''
        try:
            moderated_object = self.get(object_pk=instance.pk,
                                        content_type=ContentType.objects
                                        .get_for_model(instance.__class__))
        except MultipleObjectsReturned:
            # Get the most recent one
            moderated_object = self.filter(object_pk=instance.pk,
                                           content_type=ContentType.objects
                                           .get_for_model(instance.__class__))\
                .order_by('-date_updated')[0]
        return moderated_object
