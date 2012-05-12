from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

import moderation

def _get_content_types(self):
    content_types = []
    for model in sorted(moderation.moderation._registered_models.keys(),
                        key=lambda obj: obj.__name__):
        content_types.append(ContentType.objects.get_for_model(model))

    return content_types


try:
    from django.contrib.admin.filters import FieldListFilter
except ImportError:
    pass
else:
    #Django 1.4 filter
    class RegisteredContentTypeListFilter(FieldListFilter):
        def __init__(self, field, request, params, model, model_admin, field_path):
            self.lookup_kwarg = '%s' % field_path
            self.lookup_val = request.GET.get(self.lookup_kwarg)
            self._types = _get_content_types(self)
            super(RegisteredContentTypeListFilter, self).__init__(
                field, request, params, model, model_admin, field_path)

        def expected_parameters(self):
            return [self.lookup_kwarg]

        def choices(self, cl):
            yield {
                'selected': self.lookup_val is None,
                'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
                'display': _('All')
            }
            for type in self._types:
                yield {
                    'selected': smart_unicode(type.id) == self.lookup_val,
                    'query_string': cl.get_query_string({
                                        self.lookup_kwarg: type.id}),
                    'display': unicode(type),
                }


try:
    from django.contrib.admin.filterspecs import FilterSpec, RelatedFilterSpec
except ImportError:
    pass
else:
    #Django 1.3 Filterspec
    #Untested.

    class ContentTypeFilterSpec(RelatedFilterSpec):

        def __init__(self, *args, **kwargs):
            super(ContentTypeFilterSpec, self).__init__(*args, **kwargs)
            self.content_types = _get_content_types()
            self.lookup_choices = [(ct.id, ct.name.capitalize())\
            for ct in self.content_types]


    FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'content_type_filter',
                                                         False),
                                       ContentTypeFilterSpec))
