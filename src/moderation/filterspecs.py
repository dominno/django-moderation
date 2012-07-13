from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

import moderation


try:
    from django.contrib.admin.filterspecs import FilterSpec, RelatedFilterSpec
except ImportError:
    # Django 1.4
    pass
else:
    class ContentTypeFilterSpec(RelatedFilterSpec):

        def __init__(self, *args, **kwargs):
            super(ContentTypeFilterSpec, self).__init__(*args, **kwargs)
            self.content_types = self._get_content_types()
            self.lookup_choices = [(ct.id, ct.name.capitalize())\
            for ct in self.content_types]

        def _get_content_types(self):
            content_types = []
            registered = moderation.moderation._registered_models.keys()
            registered.sort(key=lambda obj: obj.__name__)
            for model in registered:
                content_types.append(ContentType.objects.get_for_model(model))
            return content_types
    get_filter = lambda f: getattr(f, 'content_type_filter', False)
    FilterSpec.filter_specs.insert(0, (get_filter, ContentTypeFilterSpec))
