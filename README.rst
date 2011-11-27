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
- auto approve/reject for selected user groups or user types
- support for ImageField model fields on moderate object page
- 100% PEP8 correct code
- test coverage > 80% 

Known issues
============

- m2m relations in models are not currently supported

Road map
========

For road map and issues list look at:

http://github.com/dominno/django-moderation/issues


Contributors
============

Special thanks to all persons that contributed to this project.

- jonwd7 http://github.com/jonwd7
- treyhunner http://github.com/treyhunner

Thank you for all ideas, bug fixes, patches.


Screenshots
===========

.. image:: http://dominno.pl/site_media/uploads/moderation.png
.. image:: http://dominno.pl/site_media/uploads/moderation_2.png


Requirements
============

python >= 2.4

django >= 1.1


Installation
============

Use easy_install::

    $> easy_install django-moderation 

Or download source code from http://github.com/dominno/django-moderation and run
installation script::

    $> python setup.py install



Configuration
=============

1. Add to your INSTALLED_APPS in your settings.py:

    ``moderation``
2. Run command ``manage.py syncdb``
3. Register Models with moderation, put these models in module ``moderator.py`` in side of your app, ex ``myapp.moderator``::

    from moderation import moderation
    from yourapp.models import YourModel
   
        
    moderation.register(YourModel)
    

    
4. Add function ``auto_discover`` in to main urls.py::

    from moderation.helpers import auto_discover
    auto_discover() 

5. If you want to enable integration with Django Admin, then register admin class with your Model::
    
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
===========================
    
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
	
	
Moderation registration options
===============================

``moderation.register`` takes following parameters:

``model_class``
    Model class that will be registered with moderation

``moderator_class``
    Class that subclasses GenericModerator class. It Encapsulates moderation
    options for a given model. Example::
    
    
        from moderation.moderator import GenericModerator
        
        
        class UserProfileModerator(GenericModerator):
            notify_user = False
            auto_approve_for_superusers = True
        
        moderation.register(UserProfile, UserProfileModerator)


GenericModerator options
------------------------

``visible_until_rejected``
    By default moderation stores objects pending moderation in the ``changed_object`` field in the object's corresponding ``ModeratedObject`` instance. If ``visible_until_rejected`` is set to True, objects pending moderation will be stored in their original model as usual and the most recently approved version of the object will be stored in ``changed_object``. Default: False

``manager_names``
    List of manager names on which moderation manager will be enabled. Default: ['objects']

``moderation_manager_class``
    Default manager class that will enabled on model class managers passed in ``manager_names``. This class takes care of filtering out any objects that are not approved yet. Default: ModerationObjectsManager

``visibility_column``
    If you want a performance boost, define visibility field on your model and add option ``visibility_column = 'your_field'`` on moderator class. Field must by a BooleanField. The manager that decides which model objects should be excluded when it were rejected, will first use this option to properly display (or hide) objects that are registered with moderation. Use this option if you can define visibility column in your model and want to boost performance. By default when accessing model objects that are under moderation, one extra query is executed per object in query set to determine if object should be excluded from query set. This method benefit those who do not want to add any fields to their Models. Default: None.

``fields_exclude``
    Fields to exclude from object change list. Default: []

``auto_approve_for_superusers``
    Auto approve objects changed by superusers. Default: True

``auto_approve_for_staff``
    Auto approve objects changed by user that are staff. Default: True

``auto_approve_for_groups``
    List of user group names that will be auto approved. Default: None

``auto_reject_for_anonymous``
    Auto reject objects changed by users that are anonymous. Default: True

``auto_reject_for_groups``
    List of user group names that will be auto rejected. Default: None

``bypass_moderation_after_approval``
    When set to True, affected objects will be released from the model moderator's control upon initial approval. This is useful for models in which you want to avoid unnecessary repetition of potentially expensive auto-approve/reject logic upon each object edit. This cannot be used for models in which you would like to approve (auto or manually) each object edit, because changes are not tracked and the moderation logic is not run. If the object needs to be entered back into moderation you can set its status to "Pending" by unapproving it. Default: False

``notify_moderator``
    Defines if notification e-mails will be send to moderator. By default when user change object that is under moderation, e-mail notification is send to moderator. It will inform him that object was changed and need to be moderated. Default: True
    
``notify_user``
    Defines if notification e-mails will be send to user. When moderator approves or reject object changes then e-mail notification is send to user that changed this object. It will inform user if his changes were accepted or rejected and inform him why it was rejected or approved. Default: True

``subject_template_moderator``
    Subject template that will be used when sending notifications to moderators. Default: moderation/notification_subject_moderator.txt

``message_template_moderator``
    Message template that will be used when sending notifications to moderator. Default: moderation/notification_message_moderator.txt

``subject_template_user``
    Subject template that will be used when sending notifications to users. Default: moderation/notification_subject_user.txt

``message_template_user``
    Message template that will be used when sending notifications to users. Default: moderation/notification_message_user.txt


``Notes on auto moderation``
    If you want to use auto moderation in your views, then you need to save user object that has changed the object in ModeratedObject instance. You can use following helper. Example::


        moderation.register(UserProfile)
        
        new_profile = UserProfile()
        
        new_profile.save()
        
        from moderation.helpers import automoderate
        
        automoderate(new_profile, user)


``Custom auto moderation``
    If you want to define your custom logic in auto moderation, you can overwrite methods: ``is_auto_reject`` or ``is_auto_approve`` of GenericModerator class


    Example::
        
        
        class MyModelModerator(GenericModerator):
            
            def is_auto_reject(self, obj, user):
                # Auto reject spam
                if akismet_spam_check(obj.body):  # Check body of object for spam
                    # Body of object is spam, moderate
                    return self.reason('My custom reason: SPAM')
                super(MyModelModerator, self).is_auto_reject(obj, user)
                
        moderation.register(MyModel, MyModelModerator)


Default context of notification templates
-----------------------------------------

Default context:

``content_type``
    content type object of moderated object

``moderated_object``
    ModeratedObject instance

``site``
    current Site instance


How to pass extra context to email notification templates
---------------------------------------------------------

Subclass GenericModerator class and overwrite ``inform_moderator`` and
``inform_user``
methods.::

    class UserProfileModerator(GenericModerator):

        def inform_moderator(self,
                         content_object,
                         extra_context=None):
            '''Send notification to moderator'''
            extra_context={'test':'test'}
            super(UserProfileModerator, self).inform_moderator(content_object,
                                                               extra_context)
        
        def inform_user(self, content_object, user, extra_context=None)
            '''Send notification to user when object is approved or rejected'''
            extra_context={'test':'test'}
            super(CustomModerationNotification, self).inform_user(content_object,
                                                                  user,
                                                                  extra_context)

    moderation.register(UserProfile, UserProfileModerator)


ModerationAdmin
===============

If you have defined your own ``save_model`` method in your ModelAdmin then you
must::


    # Custom save_model in MyModelAdmin
    def save_model(self, request, obj, form, change):
        # Your custom stuff
        from moderation.helpers import automoderate
        automoderate(obj, request.user)


Otherwise what you save in the admin will get moderated and automoderation will
not work.


Signals
=======

``moderation.signals.pre_moderation`` - signal send before object is approved or
rejected

Arguments sent with this signal:

``sender``
    The model class.

``instance``
    Instance of model class that is moderated

``status``
    Moderation status, 0 - rejected, 1 - approved


``moderation.signals.post_moderation`` - signal send after object is approved or
rejected

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
BaseModeratedObjectForm class as ModelForm class. Thanks to that form will
initialized 
with data from changed_object.::


    from moderation.forms import BaseModeratedObjectForm
    
    
    class ModeratedObjectForm(BaseModeratedObjectForm):

        class Meta:
            model = MyModel


Settings
========

``MODERATORS``
    List of moderators e-mails to which notifications will be send.


How to run django-moderation tests
==================================

1. Download source from http://github.com/dominno/django-moderation
2. Run: python bootstrap.py
3. Run buildout:

    bin/buildout 

4. Run tests for Django 1.1, 1.2, 1.3::

    bin/test.sh


Continuous Integration system
=============================

Continuous Integration system for django-moderation is available at:

https://continuous.io/dominno/django-moderation/
