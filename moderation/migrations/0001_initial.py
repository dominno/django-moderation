# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import moderation.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModeratedObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_pk', models.PositiveIntegerField(null=True, editable=False, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(default=datetime.datetime.now, auto_now=True)),
                ('moderation_state', models.SmallIntegerField(default=1, editable=False, choices=[(0, 'Ready for moderation'), (1, 'Draft')])),
                ('moderation_status', models.SmallIntegerField(default=2, editable=False, choices=[(1, 'Approved'), (2, 'Pending'), (0, 'Rejected')])),
                ('moderation_date', models.DateTimeField(null=True, editable=False, blank=True)),
                ('moderation_reason', models.TextField(null=True, blank=True)),
                ('changed_object', moderation.fields.SerializedObjectField(editable=False)),
                ('changed_by', models.ForeignKey(related_name='changed_by_set', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('content_type', models.ForeignKey(blank=True, editable=False, to='contenttypes.ContentType', null=True)),
                ('moderated_by', models.ForeignKey(related_name='moderated_by_set', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['moderation_status', 'date_created'],
            },
            bases=(models.Model,),
        ),
    ]
