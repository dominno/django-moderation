from moderation import ModerationManager


def setup_moderation(models=[]):
    import moderation
    new_moderation = ModerationManager()

    for model in models:
        try:
            model_class, generic_moderator = model
            new_moderation.register(model_class, generic_moderator)
        except TypeError:
            new_moderation.register(model)

    old_moderation = moderation
    setattr(moderation, 'moderation', new_moderation)

    return new_moderation, old_moderation


def teardown_moderation(new_moderation, old_moderation, models=[]):
    import moderation

    for model in models:
        new_moderation.unregister(model)

    setattr(moderation, 'moderation', old_moderation)
