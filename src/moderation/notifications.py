from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

from moderation.models import ModeratedObject


class BaseModerationNotification(object):
    
    def __init__(self, moderated_object, *arg, **kwargs):
        if not isinstance(moderated_object, ModeratedObject):
            raise AttributeError("moderated_object should be instance "\
                                 "of ModeratedObject class")
        self.moderated_object = moderated_object

    def send(self, subject_template, message_template,
                           recipient_list, extra_context=None):
        context = {'moderated_object': self.moderated_object,
                   'site': Site.objects.get_current(),
                   'content_type': self.moderated_object.content_type}

        if extra_context:
            context.update(extra_context)

        message = render_to_string(message_template, context)
        subject = render_to_string(subject_template, context)

        send_mail(subject=subject,
                  message=message,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=recipient_list)

    def inform_moderator(self,
            subject_template='moderation/notification_subject_moderator.txt',
            message_template='moderation/notification_message_moderator.txt',
            extra_context=None):
        '''Send notification to moderator'''
        from moderation.conf.settings import MODERATORS
        self.send(subject_template=subject_template,
                  message_template=message_template,
                  recipient_list=MODERATORS)

    def inform_user(self, user,
                subject_template='moderation/notification_subject_user.txt',
                message_template='moderation/notification_message_user.txt',
                extra_context=None):
        '''Send notification to user when object is approved or rejected'''
        if extra_context:
            extra_context.update({'user': user})
        else:
            extra_context = {'user': user}
        self.send(subject_template=subject_template,
                  message_template=message_template,
                  recipient_list=[user.email],
                   extra_context=extra_context)
