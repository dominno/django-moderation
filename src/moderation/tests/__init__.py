from moderation.tests.test_register import *
from moderation.tests.test_menagers import *
from moderation.tests.test_models import *
from moderation.tests.test_utils_functions import *
from moderation.tests.test_admin import *
from moderation.tests.test_diff import *
from moderation.tests.test_forms import *
from moderation.tests.test_generic_moderator import *
from moderation.tests.regresion_tests import *


def setup_moderation(models):
    import moderation
    new_moderation = ModerationManager()

    for model in models:
        new_moderation.register(model)

    old_moderation = moderation
    setattr(moderation, 'moderation', new_moderation)

    return new_moderation, old_moderation


def teardown_moderation(new_moderation, old_moderation, models):
    import moderation

    for model in models:
        new_moderation.unregister(model)

    setattr(moderation, 'moderation', old_moderation)
