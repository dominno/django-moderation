from __future__ import unicode_literals
import sys
try:
    from django.utils import unittest  # noqa
except ImportError:
    # Django < 1.3
    try:
        import unittest2 as unittest  # noqa
    except ImportError:
        if sys.version_info[1] >= 7:
            import unittest  # noqa
        else:
            raise ImportError('unittest2 is required to run the tests.')


def setup_moderation(models=[]):
    from moderation import moderation

    for model in models:
        try:
            model_class, generic_moderator = model
        except TypeError:
            moderation.register(model)
        else:
            moderation.register(model_class, generic_moderator)

    return moderation


def teardown_moderation():
    from moderation import moderation

    for model in list(moderation._registered_models.keys()):
        moderation.unregister(model)
