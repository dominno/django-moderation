Changelog
=========

0.1 alpha (2010-03-11)
----------------------

* Initial release

Added features

- configurable admin integration(data changed in admin can be visible on 
  site when moderator approves it)
- moderation queue in admin
- html differences of changes between versions of objects
- configurable email notifications
- custom model form that allows to edit changed data of object

0.2 (2010-05-19)
----------------

- Added GenericModerator class that encapsulates moderation options for a given model.Changed register method, it  will get only two parameters: model class  and settings class.
- Added option to register models with multiple managers.
- Added options to GenericModerator class: auto_approve_for_superusers, auto_approve_for_staff, auto_approve_for_groups, auto_reject_for_anonymous, auto_reject_for_groups. Added methods for checking auto moderation.
- Added automoderate helper function.
- Changed moderated_object property in ModerationManager class, moderated object is get only once from database, next is cached in _moderated_object, fixed issue with not setting user object on changed_by attribute of ModeratedObject model. 
- Fixed issue when loading object from fixture for model class that is registered with moderation. Now moderated objects will not be created when objects are loaded from fixture.
- Fixed issue with TypeError when generating differences of changes between model instances that have field with non unicode value ex. DateField.
- Fixed issue with accessing objects that existed before installation of django-moderation on model class.
- Fixed issue when more then one model is registered with moderation and multiple model instances have the same pk. 
- Fixed issue with multiple model save when automoderate was used. Auto moderation in save method of ModeratedObject has been moved to separate method.
- Added admin filter that will show only content types registered with moderation in admin queue. 
- Fixed issue when creating model forms for objects that doesn't have moderated object created.
- Added possibility of passing changed object in to is_auto- methods of GenericModerator class. This will allow more useful custom auto-moderation. Ex. auto reject if akismet spam check returns True.
- Added ability to provide custom auto reject/approve reason.
- Added option bypass_moderation_after_approval in to GenericModerator class that will release object from moderation system after initial approval of object.
- Other bug fixes and code refactoring.

0.3.2 (2012-02-15)
------------------

- Added visibility_column option in to GenericModerator class. Boost performance of database queries when excluding objects that should not be available publicly. Field must by a BooleanField. The manager that decides which model objects should be excluded when it were rejected, will first use this option to properly display (or hide) objects that are registered with moderation. Use this option if you can define visibility column in your model and want to boost performance. By default when accessing model objects that are under moderation, one extra query is executed per object in query set to determine if object should be excluded from query set. This method benefit those who do not want to add any fields to their Models. Default: None. Closes #19
- Added support for ImageField model fields on moderate object page.
- Made moderation work with south and grappelli
- Added possibility of excluding fields from moderation change list. Closes #23
- Moved ModerationManager class to moderation.register module, moved GenericModerator class to moderation.moderator module.
- Added auto_discover function that discover all modules that contain moderator.py module and auto registers all models it contain with moderartion.
- Efficiency improvement: get all info needed to filter a queryset in two SQL requests, rather than one for each object in the queryset.
- Added south migrations
- Added suport for foreignkey changes
- Add support for multi-table inheritance
- Add visible_until_rejected functionality
- Added specific initials in BaseModeratedObjectForm
- Added posibility to specify list of moderated fields
- Fixed SMTPRecipientsRefused when user has no email, when sending messages by moderation. Closes #48
- Added sorting of content types list on admin moderation queue

0.3.3 (2013-10-14)
------------------

- Tests refactor
- Added Travis CI
- Added CONTRIBUTING GUIDE

0.3.4 (2013-10-18)
------------------

- Dropped support for django 1.2.X

0.3.5 (2014-06-02)
------------------
- Added message backends
- Added support for custom user model
- Added support for django 1.6.X

0.3.6 (2014-06-09)
------------------

- Added support for python 3.X
- Dropped support for python 2.5
- Dropped support for django 1.3
- Added support for ForeignKey relations

0.4.0 (2016-08-25)
------------------

- Updated to support Django 1.7 - 1.9
- Added instructions for switching from South migrations to Django 1.7+ migrations
- Improved filter logic for Django 1.8+ to only create one additional query per queryset, instead of N additional queries (eg: one additional query per object in the querset)
- Renamed model fields to be shorter, less redundant, and more semantically correct
- Modified registry to add a ``moderation_status`` shortcut to registered models
- Added support for moderating multiple objects at once
- Changed model choice fields to use ``Choices`` from django-model-utils
- Deprecated the ``DJANGO_MODERATION_MODERATORS`` setting in favor of ``MODERATION_MODERATORS``, which does the same thing
- Improved default email template formatting
- PEP8 and Flake Fixups
- Internal code and documentation typo fixes
- Bug fixes (specifically, closes #87)

0.7.0 (2019-03-11)
------------------

- Drop support of Django<1.11. Now it supports only Django>=1.11,<=2.2
- Drop support of Python2. Now it supports only Python 3.5, 3.6, 3.7
- Minor changes at docs


0.8.0 (2022-04-09)
------------------

- Drop support of Django<2.2. Now it supports only Django>=2.2,<4
- Drop support of Python3.5. Now it supports only Python 3.6, 3.7, 3.8, 3.9
- Drop support of ``DJANGO_MODERATION_MODERATORS`` setting
- Formatted code with `black`
- Drop dependency `django-model-utils` which we used for Choices functionality
- Add partial support for Django 4.0 - remove ugettext, change `smart_text` to `smart_str`,
  change `ifequal` template tag to `if`.