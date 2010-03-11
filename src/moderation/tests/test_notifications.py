import unittest
from moderation.notifications import BaseModerationNotification
from moderation.models import ModeratedObject
from django.contrib.auth.models import User
from django.core import mail
from moderation.tests.utils.testsettingsmanager import SettingsTestCase


class BaseModerationNotificationTestCase(SettingsTestCase):
    fixtures = ['test_users.json', 'test_moderation.json']
    urls = 'moderation.tests.test_urls'
    test_settings = 'moderation.tests.test_settings'
        
    def setUp(self):
        self.user = User.objects.get(username='admin')
        object = ModeratedObject(content_object=self.user)
        self.notification = BaseModerationNotification(moderated_object=object)
        
    def test_BaseModerationNotification(self):
        self.assertEqual(isinstance(self.notification,
                                    BaseModerationNotification), True)
        
    def test_non_moderated_object(self):
        class Test(object):
            pass
        test = Test()
        
        self.assertRaises(AttributeError, BaseModerationNotification,
                          moderated_object=test)
        
    def test_send_notification(self):
        self.notification.send(
            subject_template='moderation/notification_subject_moderator.txt',
            message_template='moderation/notification_message_moderator.txt',
            recipient_list=['test@eample.com'])
        
        self.assertEqual(len(mail.outbox), 1)
        
    def test_inform_moderator(self):
        self.notification.inform_moderator()

        self.assertEqual(len(mail.outbox), 1)
        
    def test_inform_user(self):
        self.notification.inform_user(self.user)
        self.assertEqual(len(mail.outbox), 1)
