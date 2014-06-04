from __future__ import unicode_literals
from moderation.register import RegistrationError


def automoderate(instance, user):
    '''
    Auto moderates given model instance on user. Returns moderation status:
    0 - Rejected
    1 - Approved
    '''
    try:
        status = instance.moderated_object.automoderate(user)
    except AttributeError:
        msg = "%s has been registered with Moderation." % instance.__class__
        raise RegistrationError(msg)

    return status


def import_moderator(app):
    '''
    Import moderator module and register all models it contains with moderation
    '''
    from django.utils.importlib import import_module
    import imp

    try:
        app_path = import_module(app).__path__
    except AttributeError:
        return None

    try:
        imp.find_module('moderator', app_path)
    except ImportError:
        return None

    module = import_module("%s.moderator" % app)

    return module


def auto_discover():
    '''
    Auto register all apps that have module moderator with moderation
    '''
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        import_moderator(app)
