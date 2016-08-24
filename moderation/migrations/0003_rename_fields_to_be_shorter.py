# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-24 14:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('moderation', '0002_auto_20150515_1057'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='moderatedobject',
            options={
                'ordering': [
                    'status',
                    'created'
                ],
                'verbose_name': 'Moderated Object',
                'verbose_name_plural': 'Moderated Objects'
            },
        ),
        migrations.RenameField(
            model_name='moderatedobject',
            old_name='date_created',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='moderatedobject',
            old_name='moderation_date',
            new_name='on',
        ),
        migrations.RenameField(
            model_name='moderatedobject',
            old_name='moderation_reason',
            new_name='reason',
        ),
        migrations.RenameField(
            model_name='moderatedobject',
            old_name='moderation_state',
            new_name='state',
        ),
        migrations.RenameField(
            model_name='moderatedobject',
            old_name='date_updated',
            new_name='updated',
        ),
        migrations.RenameField(
            model_name='moderatedobject',
            old_name='moderated_by',
            new_name='by',
        ),
        migrations.RenameField(
            model_name='moderatedobject',
            old_name='moderation_status',
            new_name='status',
        ),
    ]