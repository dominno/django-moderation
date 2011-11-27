

def setup_moderation(models=[]):
    from moderation import moderation

    moderation._registered_models = {}

    for model in models:
        try:
            model_class, generic_moderator = model
            moderation.register(model_class, generic_moderator)
        except TypeError:
            moderation.register(model)

    return moderation


def teardown_moderation():
    from moderation import moderation

    for model in moderation._registered_models.keys():
        moderation.unregister(model)
