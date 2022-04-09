Welcome to django-moderation's documentation!
=============================================


Introduction
------------

``django-moderation`` is reusable application for Django framework, that allows to
moderate any model objects.

**Possible use cases**:

- User creates his profile, profile is not visible on site.
  It will be visible on site when moderator approves it.
- User change his profile, old profile data is visible on site.
  New data will be visible on site when moderator approves it.

**Features**:

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
------------

- m2m relations in models are not currently supported

Contributors
------------

Special thanks to all persons that contributed to this project.

- `jonwd7 <https://github.com/jonwd7>`_
- `treyhunner <https://github.com/treyhunner>`_
- `DmytroLitvinov <https://github.com/DmytroLitvinov>`_

Thank you for all ideas, bug fixes, patches.

Screenshots
===========

.. image:: http://dominno.pl/site_media/uploads/moderation.png
.. image:: http://dominno.pl/site_media/uploads/moderation_2.png

Requirements
============

Python 3.6, 3.7, 3.8, 3.9

Django 2.2, 3.1, 3.2


Contents:
=========

.. toctree::
   :maxdepth: 3

   getting_started
   advanced_options
   contributing
   history



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

