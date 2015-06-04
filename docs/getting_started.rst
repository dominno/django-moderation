Getting started quick guide
===========================

Installation
------------

Use easy_install::

    $> easy_install django-moderation

Or download source code from http://github.com/dominno/django-moderation and run
installation script::

    $> python setup.py install


Updating existing projects to Django 1.7
----------------------------------------

If you are updating an existing project which uses ``django-moderation`` to Django 1.7 you need to follow these simple steps:

1. Remove ``'south'`` from your ``INSTALLED_APPS`` if present.
2. Run ``python manage.py migrate``.

That's it!


Configuration
-------------

1. Add to your INSTALLED_APPS in your settings.py:

    ``moderation``
2. Run command ``manage.py syncdb``


Usage
-----

To start using ``django-moderation`` follow these steps:

1. Create your models by extending ``moderation.db.ModeratedModel``::

    from moderation.db import ModeratedModel

    class MyModel(ModeratedModel):
         my_field = models.TextField()


2. To customize ``Moderator`` settings create ``class Moderator`` within your model definition::

    from django.db import models
    from moderation.db import ModeratedModel

    class MyModel(ModeratedModel):
        my_field = models.TextField()

        class Moderator:
            notify_user = False


The models will be automatically registered with ``django-moderation``.


Usage alternative
-----------------

Alternatively, you can follow the steps below:

1. Register Models with moderation, put these models in module ``moderator.py`` inside of your app, e.g. ``myapp.moderator``::

    from moderation import moderation
    from yourapp.models import YourModel


    moderation.register(YourModel)



2. Add function ``auto_discover`` in to main urls.py::

    from moderation.helpers import auto_discover
    auto_discover()


Admin integration
-----------------

1. If you want to enable integration with Django Admin, then register admin class with your Model::

    from django.contrib import admin
    from moderation.admin import ModerationAdmin


    class YourModelAdmin(ModerationAdmin):
        """Admin settings go here."""

    admin.site.register(YourModel, YourModelAdmin)


If admin_integration_enabled is enabled then when saving object in admin, data
will not be saved in model instance but it will be stored in moderation queue.
Also data in the change form will not display data from the original model
instance but data from the ModeratedObject instance instead.


How django-moderation works
---------------------------

When you change existing object or create new one, it will not be publicly
available until moderator approves it. It will be stored in ModeratedObject model.::

    your_model = YourModel(description='test')
    your_model.save()

    YourModel.objects.get(pk=your_model.pk)
    Traceback (most recent call last):
    DoesNotExist: YourModel matching query does not exist.

When you will approve object, then it will be publicly available.::

    your_model.moderated_object.approve(moderated_by=user,
                                       reason='Reason for approve')

    YourModel.objects.get(pk=1)
    <YourModel: YourModel object>

Please note that you can also access objects that are not approved by using unmoderated_objects manager, this manager will bypass the moderation system

    YourModel.unmoderated_objects.get(pk=your_model.pk)

You can access changed object by calling changed_object on moderated_object:

    your_model.moderated_object.changed_object
    <YourModel: YourModel object>

This is deserialized version of object that was changed.

Now when you will change an object, old version of it will be available publicly,
new version will be saved in moderated_object::

    your_model.description = 'New description'
    your_model.save()

    your_model = YourModel.objects.get(pk=1)
    your_model.__dict__
    {'id': 1, 'description': 'test'}

    your_model.moderated_object.changed_object.__dict__
    {'id': 1, 'description': 'New description'}

    your_model.moderated_object.approve(moderated_by=user,
                                       reason='Reason for approve')

    your_model = YourModel.objects.get(pk=1)
    your_model.__dict__
    {'id': 1, 'description': 'New description'}
