Introduction
============

django-moderation is reusable application for Django framework, that allows to
moderate any model objects.

Possible use cases:

- User creates his profile, profile is not visible on site.
  It will be visible on site when moderator approves it.
- User change his profile, old profile data is visible on site.
  New data will be visible on site when moderator approves it. 

Features:

- configurable admin integration(data changed in admin can be visible on 
  site when moderator approves it)
- moderation queue in admin
- html differences of changes between versions of objects
- configurable email notifications
- custom model form that allows to edit changed data of object
- 100% PEP8 correct code
- test coverage > 80% 

Known isuses
============

- foreign-key and m2m relations in models are not currently supported
- not tested on Django 1.2, i will make a test case.

Road map
========

0.2 
---

- Add support for foreign-key and m2m relations for models that are under moderation
- Add support for ImageField, display images differences on approve/reject moderate page

0.3
---
 
- Your feature ?


Screenshots
===========

.. image:: http://dominno.pl/site_media/uploads/moderation.png
.. image:: http://dominno.pl/site_media/uploads/moderation_2.png


Requirements
============

python >= 2.4

django == 1.1


Installation
============

Download source code from http://github.com/dominno/django-moderation and run installation script::

    $> python setup.py install


Configuration
=============

1. Add to your INSTALLED_APPS in your settings.py:

    ``moderation``
2. Run command ``manage.py syncdb``
3. Register Models with moderation::

    from django.db import models
    from moderation import moderation
    
    
    class YourModel(models.Model):
        pass
        
    moderation.register(YourModel)

4. Register admin class with your Model::
    
    from django.contrib import admin
    from moderation.admin import ModerationAdmin


    class YourModelAdmin(ModerationAdmin):
        """Admin settings go here."""

    admin.site.register(YourModel, YourModelAdmin)
    
If you want to disable integration of moderation in admin,
add admin_intergration_enabled = False to your admin class::

    class YourModelAdmin(ModerationAdmin):
        admin_intergration_enabled = False
    
    admin.site.register(YourModel, YourModelAdmin)
    

How django-moderation works
===========================
    
When you change existing object or create new one, it will not be publicly
available until moderator approves it. It will be stored in ModeratedObject model.::
 
    your_model = YourModel(description='test')
    your_model.save()
    
    YourModel.objects.get(pk=your_model.pk)
    Traceback (most recent call last):
    DoesNotExist: YourModel matching query does not exist.
    
When you will approve object, then it will be publicly available.::

    your_model.moderated_object.approve(moderatated_by=user,
                                       reason='Reason for approve')
                                       
    YourModel.objects.get(pk=1)
    <YourModel: YourModel object>
    
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
    
    your_model.moderated_object.approve(moderatated_by=user,
                                       reason='Reason for approve')

    your_model = YourModel.objects.get(pk=1)
    your_model.__dict__
    {'id': 1, 'description': 'New description'}
	

Email notifications
===================

By default when user change object that is under moderation,
e-mail notification is send to moderator. It will inform him
that object was changed and need to be moderated.

When moderator approves or reject object changes then e-mail
notification is send to user that changed this object. It will
inform user if his changes were accepted or rejected and inform him
why it was rejected or approved.

How to overwrite email notification templates
---------------------------------------------

E-mail notifications use following templates:
 
- moderation/notification_subject_moderator.txt
- moderation/notification_message_moderator.txt
- moderation/notification_subject_user.txt
- moderation/notification_message_user.txt

Default context:

``content_type``
    content type object of moderated object

``moderated_object``
    ModeratedObject instance

``site``
    current Site instance


How to pass extra context to email notification templates
---------------------------------------------------------

If you want to pass extra context to email notification methods
you new need to create new class that subclass BaseModerationNotification class::


    class CustomModerationNotification(BaseModerationNotification):
        def inform_moderator(self,
                         subject_template='moderation/notification_subject_moderator.txt',
                         message_template='moderation/notification_message_moderator.txt',
                         extra_context=None):
            '''Send notification to moderator'''
            extra_context={'test':'test'}
            super(CustomModerationNotification, self).inform_moderator(subject_template,
                                                                       message_template,
                                                                       extra_context)
        
        def inform_user(self, user,
                        subject_template='moderation/notification_subject_user.txt',
                        message_template='moderation/notification_message_user.txt',
                        extra_context=None)
            '''Send notification to user when object is approved or rejected'''
            extra_context={'test':'test'}
            super(CustomModerationNotification, self).inform_user(user,
                                                                  subject_template,
                                                                  message_template,
                                                                  extra_context)



Next register it with moderation as notification_class:

    moderation.register(YourModel, notification_class=CustomModerationNotification)



Signals
=======

``moderation.signals.pre_moderation`` - signal send before object is approved or rejected

Arguments sent with this signal:

``sender``
    The model class.

``instance``
    Instance of model class that is moderated

``status``
    Moderation status, 0 - rejected, 1 - approved


``moderation.signals.post_moderation`` - signal send after object is approved or rejected

Arguments sent with this signal:

``sender``
    The model class.

``instance``
    Instance of model class that is moderated

``status``
    Moderation status, 0 - rejected, 1 - approved


Forms
=====

When creating ModelForms for models that are under moderation use
BaseModeratedObjectForm class as ModelForm class. Thanks to that form will initialized 
with data from changed_object.::


    from moderation.forms import BaseModeratedObjectForm
    
    
    class ModeratedObjectForm(BaseModeratedObjectForm):

        class Meta:
            model = MyModel


How to run django-moderation tests
==================================

1. Download source from http://github.com/dominno/django-moderation
2. Run: python bootstrap.py
3. Run tests for Django 1.1 and Django 1.2::

    bin/test-1.1
    bin/test-1.2


