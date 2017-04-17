import django
from distutils.version import StrictVersion


def clear_builtins(attrs):
    """
    Clears the builtins from an ``attrs`` dict

    Returns a new dict without the builtins

    """
    new_attrs = {}

    for key in attrs.keys():
        if not(key.startswith('__') and key.endswith('__')):
            new_attrs[key] = attrs[key]

    return new_attrs


def django_110():
    if StrictVersion(django.get_version()) >= StrictVersion('1.10.0'):
        return True
    return False


def django_19():
    if StrictVersion(django.get_version()) >= StrictVersion('1.9.0'):
        return True
    return False


def django_18():
    if StrictVersion(django.get_version()) >= StrictVersion('1.8.0'):
        return True
    return False


def django_17():
    if StrictVersion(django.get_version()) >= StrictVersion('1.7.0'):
        return True
    return False


def django_14():
    if StrictVersion(django.get_version()) < StrictVersion('1.5.0'):
        return True
    return False
