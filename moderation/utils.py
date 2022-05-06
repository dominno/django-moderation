def clear_builtins(attrs):
    """
    Clears the builtins from an ``attrs`` dict

    Returns a new dict without the builtins

    """
    new_attrs = {}

    for key in attrs.keys():
        if not (key.startswith('__') and key.endswith('__')):
            new_attrs[key] = attrs[key]

    return new_attrs


def is_sites_framework_enabled() -> bool:
    """
    Check project's settings to see if the optional Sites framework is installed.
    """
    from django.conf import settings
    return "django.contrib.sites" in settings.INSTALLED_APPS
