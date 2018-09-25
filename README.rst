Introduction
============
.. image:: https://travis-ci.org/dominno/django-moderation.png
   :target: https://travis-ci.org/dominno/django-moderation
   
.. image:: https://img.shields.io/pypi/v/django-moderation.svg
   :target: https://pypi.python.org/pypi/django-moderation

.. image:: https://img.shields.io/pypi/dm/django-moderation.svg
   :target: https://pypi.python.org/pypi/django-moderation

.. image:: https://coveralls.io/repos/dominno/django-moderation/badge.png?branch=master
   :target: https://coveralls.io/r/dominno/django-moderation?branch=master

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


Requirements
============

python 2.7, 3.3+

django >= 1.8 (1.7 is also partially supported)

django-model-utils


Known issues
============

- m2m relations in models are not currently supported
- For Django 1.7, a query is run for every object in a query, resulting in N+1 total queries. For Django >= 1.8 only one additional query is run for each unmoderated query.


Documentation
=============

Full module documentation is hosted at ReadTheDocs: http://django-moderation.readthedocs.org/


Contributors
============

Special thanks to all persons that contributed to this project.

- jonwd7 http://github.com/jonwd7
- treyhunner http://github.com/treyhunner

Thank you for all ideas, bug fixes, patches.

