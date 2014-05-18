from django.db.models.manager import Manager
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist


class MetaClass(type(Manager)):

    def __new__(cls, name, bases, attrs):
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)


class ModerationObjectsManager(Manager):

    def __call__(self, base_manager, *args, **kwargs):
        return MetaClass(
            self.__class__.__name__,
            (self.__class__, base_manager),
            {'use_for_related_fields': True})

    def filter_moderated_objects(self, query_set):
        from moderation.models import MODERATION_STATUS_PENDING

        exclude_pks = []

        from models import ModeratedObject

        mobjs_set = ModeratedObject.objects.filter(
            content_type=ContentType.objects.get_for_model(query_set.model),
            object_pk__in=query_set.values_list('pk', flat=True))

        # TODO: Load this query in chunks to avoid huge RAM usage spikes
        mobjects = dict(
            [(mobject.object_pk, mobject) for mobject in mobjs_set])

        full_query_set = super(ModerationObjectsManager, self).get_query_set()\
            .filter(pk__in=query_set.values_list('pk', flat=True))

        for obj in full_query_set:
            try:
                # We cannot use dict.get() here!
                mobject = mobjects[obj.pk] if obj.pk in mobjects else \
                    obj.moderated_object

                if mobject.moderation_status == MODERATION_STATUS_PENDING and \
                   not mobject.moderation_date:
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

    def get_query_set(self):
        query_set = super(ModerationObjectsManager, self).get_query_set()

        if self.moderator.visibility_column:
            return self.exclude_objs_by_visibility_col(query_set)

        return self.filter_moderated_objects(query_set)

    @property
    def moderator(self):
        from moderation import moderation

        return moderation.get_moderator(self.model)


class ModeratedObjectManager(Manager):

    def get_for_instance(self, instance):
        '''Returns ModeratedObject for given model instance'''
        return self.get(
            object_pk=instance.pk,
            content_type=ContentType.objects.get_for_model(instance.__class__))
