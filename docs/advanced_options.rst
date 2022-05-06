Advanced options
================


Moderation registration options
-------------------------------

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
    If you want a performance boost, define visibility field on your model and add option ``visibility_column = 'your_field'`` on moderator class. Field must by a BooleanField. The manager that decides which model objects should be excluded when it were rejected, will first use this option to properly display (or hide) objects that are registered with moderation. Use this option if you can define visibility column in your model and want to boost performance. This method benefits those who can add fields to their models. Default: None.

``fields_exclude``
    Fields to exclude from object change list. Default: []

``resolve_foreignkeys``
    Display related object's string representation instead of their primary key. Default: True

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

``keep_history``
    When set to True this will allow multiple moderations per registered model instance. Otherwise there is only one moderation per registered model instance. Default: False.

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
    If you want to use auto moderation in your views, then you need to save user object that has changed the object in ModeratedObject instance. You can use following helper. Example:

    .. code-block:: python

        moderation.register(UserProfile)

        new_profile = UserProfile()

        new_profile.save()

        from moderation.helpers import automoderate

        automoderate(new_profile, user)


``Custom auto moderation``
    If you want to define your custom logic in auto moderation, you can overwrite methods: ``is_auto_reject`` or ``is_auto_approve`` of GenericModerator class


    Example:

    .. code-block:: python


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
    current Site instance, if Site package is enabled


How to pass extra context to email notification templates
---------------------------------------------------------

Subclass GenericModerator class and overwrite ``inform_moderator`` and
``inform_user``
methods.:

.. code-block:: python

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
---------------

If you have defined your own ``save_model`` method in your ModelAdmin then you
must:

.. code-block:: python

    # Custom save_model in MyModelAdmin
    def save_model(self, request, obj, form, change):
        # Your custom stuff
        from moderation.helpers import automoderate
        automoderate(obj, request.user)


Otherwise what you save in the admin will get moderated and automoderation will
not work.


Message backend
---------------

By default the message backend used for sending notifications is `moderation.message_backends.EmailMessageBackend`, which is trigger a synchronous task on the main thread and call the `django.core.mail.send_mail` method.

You can write your own message backend class by subclassing `moderation.message_backends.BaseMessageBackend`, in order to use another api to send your notifications (Celery, RabbitMQ, ...).

Example of a custom message backend ::

    class CustomMessageBackend(object):

        def send(self, **kwargs):
            subject = kwargs.get('subject', None)
            message = kwargs.get('message', None)
            recipient_list = kwargs.get('recipient_list', None)

            trigger_custom_message(subject, message, recipient_list)

Then specify the custom class in the moderator ::

    from moderation.moderator import GenericModerator
    from myproject.message_backends import CustomMessageBackend


    class UserProfileModerator(GenericModerator):
        message_backend_class = CustomMessageBackend

    moderation.register(UserProfile, UserProfileModerator)


Signals
-------

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
-----

When creating ModelForms for models that are under moderation use
BaseModeratedObjectForm class as ModelForm class. Thanks to that form will
initialized
with data from changed_object.::


    from moderation.forms import BaseModeratedObjectForm


    class ModeratedObjectForm(BaseModeratedObjectForm):

        class Meta:
            model = MyModel


Settings
--------

``MODERATION_MODERATORS``
    Tuple of moderators' email addresses to which notifications will be sent.
