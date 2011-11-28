# -*- coding: utf-8 -*-

import unittest
from moderation.diff import get_changes_between_models, html_to_list,\
    TextChange, get_diff_operations, ImageChange
from django.test.testcases import TestCase, OutputChecker
from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from django.core import management
from django.contrib.auth.models import User
from django.db.models import fields
from moderation.tests.apps.test_app1.models import UserProfile, \
    ModelWIthDateField, ModelWithImage
from moderation.models import ModeratedObject
import re


_norm_whitespace_re = re.compile(r'\s+')


def norm_whitespace(s):
    return _norm_whitespace_re.sub(' ', s).strip()


class TextChangeObjectTestCase(unittest.TestCase):

    def setUp(self):
        self.change = TextChange(verbose_name='description',
                                 field=fields.CharField,
                                 change=('test1', 'test2'))

    def test_verbose_name(self):
        self.assertEqual(self.change.verbose_name, 'description')

    def test_field(self):
        self.assertEqual(self.change.field, fields.CharField)

    def test_change(self):
        self.assertEqual(self.change.change, ('test1', 'test2'))

    def test_diff_text_change(self):
        self.assertEqual(self.change.diff,
                         u'<del class="diff modified">test1'\
                         u'</del><ins class="diff modified">test2</ins>\n')

    def test_render_diff(self):
        diff_operations = get_diff_operations('test1', 'test2')
        self.assertEqual(self.change.render_diff('moderation/html_diff.html',
                {'diff_operations': diff_operations}),
                         u'<del class="diff modified">test1'\
                         u'</del><ins class="diff modified">test2</ins>\n')


class ImageChangeObjectTestCase(unittest.TestCase):

    def setUp(self):
        image1 = ModelWithImage(image='my_image.jpg')
        image1.save()
        image2 = ModelWithImage(image='my_image2.jpg')
        image2.save()
        self.left_image = image1.image
        self.right_image = image2.image
        self.change = ImageChange(verbose_name='image',
                                  field=fields.files.ImageField,
                                  change=(self.left_image, self.right_image))

    def test_verbose_name(self):
        self.assertEqual(self.change.verbose_name, 'image')

    def test_field(self):
        self.assertEqual(self.change.field, fields.files.ImageField)

    def test_change(self):
        self.assertEqual(self.change.change, (self.left_image,
                                              self.right_image))

    def test_diff(self):
        self.assertEqual(norm_whitespace(self.change.diff),
                         norm_whitespace(u'<img src="/media/my_image.jpg"> '
                                         u'<img style="margin-left: 10px;" '
                                         u'src="/media/my_image2.jpg">'))


class DiffModeratedObjectTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.profile = UserProfile.objects.get(user__username='moderator')

    def test_get_changes_between_models(self):
        self.profile.description = 'New description'
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        self.profile = UserProfile.objects.get(user__username='moderator')

        changes = get_changes_between_models(moderated_object.changed_object,
                                             self.profile)

        self.assertEqual(
            unicode(changes),
            u"{u'userprofile__url': Change object: http://www.google.com"\
            u" - http://www.google.com, u'userprofile__description': "\
            u"Change object: New description - Old description, "\
            u"u'userprofile__user': Change object: 1 - 1}")

    def test_foreign_key_changes(self):
        self.profile.user = User.objects.get(username='admin')
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        self.profile = UserProfile.objects.get(user__username='moderator')

        changes = get_changes_between_models(moderated_object.changed_object,
                                             self.profile)

        self.assertEqual(
            unicode(changes),
            u"{u'userprofile__url': Change object: http://www.google.com"\
            u" - http://www.google.com, u'userprofile__description': "\
            u"Change object: Old description - Old description, "\
            u"u'userprofile__user': Change object: 4 - 1}")

    def test_get_changes_between_models_image(self):
        '''Verify proper diff for ImageField fields'''

        image1 = ModelWithImage(image='tmp/test1.jpg')
        image1.save()
        image2 = ModelWithImage(image='tmp/test2.jpg')
        image2.save()

        changes = get_changes_between_models(image1, image2)
        self.assertEqual(
            norm_whitespace(changes['modelwithimage__image'].diff),
            norm_whitespace(u'<img src="/media/tmp/test1.jpg"> '
                            u'<img style="margin-left: 10px;" '
                            u'src="/media/tmp/test2.jpg">'))

    def test_excluded_fields_should_be_excluded_from_changes(self):
        self.profile.description = 'New description'
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        self.profile = UserProfile.objects.get(user__username='moderator')

        changes = get_changes_between_models(
            moderated_object.changed_object,
            self.profile, excludes=['description'])

        self.assertEqual(unicode(changes),
                         u"{u'userprofile__url': Change object: "\
                         u"http://www.google.com - http://www.google.com, "\
                         u"u'userprofile__user': Change object: 1 - 1}")


class DiffTestCase(unittest.TestCase):

    def test_html_to_list(self):
        html = u'<p id="test">text</p><b>some long text \n\t\r text</b>'\
               u'<div class="test">text</div>'
        html_list = [u'<p id="test">',
                     u'text',
                     u'</p>',
                     u'<b>',
                     u'some ',
                     u'long ',
                     u'text ',
                     u'\n\t\r ',
                     u'text',
                     u'</b>',
                     u'<div class="test">',
                     u'text',
                     u'</div>',
                     ]

        self.assertEqual(html_to_list(html), html_list)

    def test_html_to_list_non_ascii(self):
        html = u'<p id="test">text</p><b>Las demás lenguas españolas'\
               u' serán también</b><div class="test">text</div>'

        self.assertEqual(html_to_list(html), ['<p id="test">',
                                              'text',
                                              '</p>',
                                              '<b>',
                                              u'Las ',
                                              u'dem\xe1s ',
                                              u'lenguas ',
                                              u'espa\xf1olas ',
                                              u'ser\xe1n ',
                                              u'tambi\xe9n',
                                              '</b>',
                                              '<div class="test">',
                                              'text',
                                              '</div>',
                                              ])


class DateFieldTestCase(SettingsTestCase):
    fixtures = ['test_users.json']
    test_settings = 'moderation.tests.settings.generic'

    def setUp(self):
        self.obj1 = ModelWIthDateField()
        self.obj2 = ModelWIthDateField()

        self.obj1.save()
        self.obj2.save()

    def test_date_field_in_model_object_should_be_unicode(self):
        '''Test if when model field value is not unicode, then when getting 
           changes between models, all changes should be unicode.
        '''
        changes = get_changes_between_models(self.obj1, self.obj2)

        date_change = changes['modelwithdatefield__date']

        self.assertTrue(isinstance(date_change.change[0], unicode))
        self.assertTrue(isinstance(date_change.change[1], unicode))

    def test_html_to_list_should_return_list(self):
        '''Test if changes dict generated from model that has non unicode field
           is properly used by html_to_list function
        '''
        changes = get_changes_between_models(self.obj1, self.obj2)

        date_change = changes['modelwithdatefield__date']

        changes_list1 = html_to_list(date_change.change[0])
        changes_list2 = html_to_list(date_change.change[1])

        self.assertTrue(isinstance(changes_list1, list))
        self.assertTrue(isinstance(changes_list2, list))
