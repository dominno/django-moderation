CONTRIBUTING GUIDE
==================

Setup
=====

Fork on GitHub
--------------

Before you do anything else, login/signup on GitHub and fork **django-moderation** from the `GitHub project`_.

Clone your fork locally
-----------------------

If you have git-scm installed, you now clone your git repo using the following command-line argument where <my-github-name> is your account name on GitHub::

    git clone git@github.com:<my-github-name>/django-moderation.git

Local Installation
-------------------------

1. Create a virtualenv_ (or use virtualenvwrapper_). Activate it.
2. cd into django-moderation
3. type ``$ python setup.py develop``

Try the example projects
--------------------------

1. cd into example_project/
2. create the database: ``$ python manage.py syncdb``
3. run the dev server: ``$ python manage.py runserver``

.. _virtualenv: http://www.virtualenv.org/en/latest/
.. _virtualenvwrapper: http://virtualenvwrapper.readthedocs.org/en/latest/

How to get your pull request accepted
=====================================

We want your submission. But we also want to provide a stable experience for our users and the community. Follow these rules and you should succeed without a problem!

Run the tests!
--------------

Before you submit a pull request, please run the entire django-moderation test suite via::

    python setup.py test


If you add code/views you need to add tests!
--------------------------------------------

We've learned the hard way that code without tests is undependable. If your pull request reduces our test coverage because it lacks tests then it will be **rejected**.

For now, we use the Django Test framework (based on unittest).


Keep your pull requests limited to a single issue
--------------------------------------------------

django-moderation pull requests should be as small/atomic as possible. Large, wide-sweeping changes in a pull request will be **rejected**, with comments to isolate the specific code in your pull request


Code style
----------

Please follow PEP8 rules for code style.


Code structure
==============

- moderation/admin.py - Django admin classes for moderation queue
- moderation/diff.py - used for generation of differences between model fields
- moderation/fields.py - SerializedObjectField code
- moderation/filterspecs.py - filters definitions used in Django admin queue
- moderation/forms.py - custom ModelForm class that uses unmoderated data instead of public one.
- moderation/helpers - moderation helpers functions
- moderation/managers - Managers used by moderation
- moderation/models - ModeratedObject class code
- moderation/moderator - base class for moderation options used during model registration with moderation
- moderation/register - code responsible for model registration with moderation
- moderation/signals - signals used by moderation


Test are located in directory tests/tests.

Each file is used for tests of different part of the moderation module.

Example: tests/unit/register - tests all things related with model registration with moderation system.
