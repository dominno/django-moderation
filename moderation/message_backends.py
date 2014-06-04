from __future__ import unicode_literals
from django.conf import settings
from django.core.mail import send_mail


class BaseMessageBackend(object):

    def send(self, **kwargs):
        raise NotImplementedError


class SyncMessageBackend(BaseMessageBackend):
    """Synchronous backend"""


class AsyncMessageBackend(BaseMessageBackend):
    """Asynchronous backend"""


class EmailMessageBackend(SyncMessageBackend):
    """
    Send the message through an email on the main thread
    """

    def send(self, **kwargs):
        subject = kwargs.get('subject', None)
        message = kwargs.get('message', None)
        recipient_list = kwargs.get('recipient_list', None)

        send_mail(subject=subject,
                  message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=recipient_list,
                  fail_silently=True)
