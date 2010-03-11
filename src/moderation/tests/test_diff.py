# -*- coding: utf-8 -*-

import unittest
from moderation.diff import get_changes_between_models, html_ta_list,\
    html_diff, generate_diff
from django.test.testcases import TestCase
from moderation.tests.utils.testsettingsmanager import SettingsTestCase
from django.core import management
from django.contrib.auth.models import User
from moderation.tests.test_app.models import UserProfile
from moderation.models import ModeratedObject
import re


class DiffModeratedObjectTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    test_settings = 'moderation.tests.test_settings'

    def setUp(self):
        self.profile = UserProfile.objects.get(user__username='moderator')
        
    def test_get_changes_between_models(self):
        self.profile.description = 'New description'
        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()
        
        self.profile = UserProfile.objects.get(user__username='moderator')
        
        diff = get_changes_between_models(moderated_object.changed_object,
                                   self.profile)

        self.assertEqual(diff, {'description': ('New description',
                                                u'Profile description')})
        
    def test_generate_diff(self):
        self.profile.description = 'New description'
        self.profile.url = 'http://new_url.com'

        moderated_object = ModeratedObject(content_object=self.profile)
        moderated_object.save()

        self.profile = UserProfile.objects.get(user__username='moderator')
        self.profile.description = 'Old description'
        self.profile.url = 'http://old_url.com'
       
        fields_diff = generate_diff(self.profile,
                                    moderated_object.changed_object)

        description_diff = u'<del class="diff modified">Old </del>'\
                           u'<ins class="diff modified">New </ins>description'
        url_diff = u'http<del class="diff modified">old_url</del>'\
                   u'<ins class="diff modified">new_url</ins>.com'
 
        self.assertEqual(fields_diff, [
                                        {
                                         'verbose_name':'description',
                                         'diff': description_diff},
                                        {
                                         'verbose_name':'url',
                                         'diff': url_diff}])


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

        self.assertEqual(html_ta_list(html), html_list)

    def test_html_to_list_non_ascii(self):
        html = u'<p id="test">text</p><b>Las demás lenguas españolas'\
        u' serán también</b><div class="test">text</div>'
        
        self.assertEqual(html_ta_list(html), ['<p id="test">',
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

    def test_html_diff(self):
        text_a = '<p>Lorem ipsum dolor <b>sit</b> amet, consectetur\n'\
                 'adipiscing elit. Curabitur consequat <h1>risus</h1> '\
                 'a nisl commodo interdum.</p>'

        text_b = '<p>Lorem ipsum dolor <b>lorem</b> amet, consectetur\n'\
                 'adipiscing elit. Curabitur tellus consequat <h1>risus</h1>'\
                 ' a nisl commodo.</p>'

        diff_html = '<p>Lorem ipsum dolor <b><del class="diff modified">sit'\
                    '</del><ins class="diff modified">lorem</ins></b> amet,'\
                    ' consectetur\nadipiscing elit. Curabitur '\
                    '<ins class="diff">tellus </ins>consequat <h1>risus</h1>'\
                    ' a nisl <del class="diff modified">commodo '\
                    'interdum</del><ins class="diff modified">'\
                    'commodo</ins>.</p>'

        self.assertEqual(html_diff(text_a, text_b), diff_html)
