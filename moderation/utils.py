import django
from distutils.version import StrictVersion


def django_17():
    if StrictVersion(django.get_version()) >= StrictVersion('1.7.0'):
        return True
    return False
