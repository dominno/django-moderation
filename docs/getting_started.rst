Getting started quick guide
===========================

Installation
------------

.. code-block:: bash

    $ pip install django-moderation

Or download source code from http://github.com/dominno/django-moderation and run
installation script:

.. code-block:: bash

    $ python setup.py install


Configuration
-------------

``django-moderation`` will autodiscover moderation classes in ``<app>/moderator.py`` files by default. So the simplest moderation configuration is to simply add ``moderation`` (or ``moderation.apps.ModerationConfig``) to ``INSTALLED_APPS`` in your ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        'moderation',  # or 'moderation.apps.ModerationConfig',
        # ...
    ]

Then add all of your moderation classes to a ``moderator.py`` file in an app and register them with moderation:

.. code-block:: python

    from moderation import moderation
    from moderation.moderator import GenericModerator

    from yourapp.models import YourModel, AnotherModel


    class AnotherModelModerator(GenericModerator):
        # Add your moderator settings for AnotherModel here


    moderation.register(YourModel)  # Uses default moderation settings
    moderation.register(AnotherModel, AnotherModelModerator)  # Uses custom moderation settings

This is exactly how Django's contributed admin app registers models.


Alternative Configuration
-------------------------

If you don't want ``django-moderation`` to autodiscover your moderation classes, you will add ``moderation.apps.SimpleModerationConfig`` to ``INSTALLED_APPS`` in your ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        'moderation.apps.SimpleModerationConfig',
        # ...
    ]

Then you will need to subclass your models from ``moderation.db.ModeratedModel`` and add moderation classes to each moderated model in ``models.py``:

.. code-block:: python

    from django.db import models
    from moderation.db import ModeratedModel


    class MyModel(ModeratedModel):
        my_field = models.TextField()

        class Moderator:
            notify_user = False


Admin integration
-----------------

1. If you want to enable integration with Django Admin, then register admin class with your model:

.. code-block:: python

    from django.contrib import admin
    from moderation.admin import ModerationAdmin


    class YourModelAdmin(ModerationAdmin):
        """Admin settings go here."""

    admin.site.register(YourModel, YourModelAdmin)


If ``admin_integration_enabled`` is enabled then when saving object in admin, data
will not be saved in model instance but it will be stored in moderation queue.
Also data in the change form will not display data from the original model
instance but data from the ModeratedObject instance instead.


How django-moderation works
---------------------------

When you change existing object or create new one, it will not be publicly
available until moderator approves it. It will be stored in ModeratedObject model.:

.. code-block:: python

    your_model = YourModel(description='test')
    your_model.save()

    YourModel.objects.get(pk=your_model.pk)
    Traceback (most recent call last):
    DoesNotExist: YourModel matching query does not exist.

When you will approve object, then it will be publicly available.:

.. code-block:: python

    your_model.moderated_object.approve(by=user, reason='Reason for approve')

    YourModel.objects.get(pk=1)
    <YourModel: YourModel object>

Please note that you can also access objects that are not approved by using unmoderated_objects manager, this manager will bypass the moderation system

.. code-block:: python

    YourModel.unmoderated_objects.get(pk=your_model.pk)

You can access changed object by calling changed_object on moderated_object:

.. code-block:: python

    your_model.moderated_object.changed_object
    <YourModel: YourModel object>

This is deserialized version of object that was changed.

Now when you will change an object, old version of it will be available publicly,
new version will be saved in moderated_object:

.. code-block:: python

    your_model.description = 'New description'
    your_model.save()

    your_model = YourModel.objects.get(pk=1)
    your_model.__dict__
    {'id': 1, 'description': 'test'}

    your_model.moderated_object.changed_object.__dict__
    {'id': 1, 'description': 'New description'}

    your_model.moderated_object.approve(by=user, reason='Reason for approve')

    your_model = YourModel.objects.get(pk=1)
    your_model.__dict__
    {'id': 1, 'description': 'New description'}