import unittest  # noqa


def setup_moderation(models=None):
    from moderation import moderation

    if models is None:
        models = []

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
