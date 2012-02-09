# -*- coding: utf-8 -*-

import re
import difflib

from django.db.models import fields
from django.utils.html import escape


class BaseChange(object):

    def __repr__(self):
        value1, value2 = self.change
        return u'Change object: %s - %s' % (value1, value2)

    def __init__(self, verbose_name, field, change):
        self.verbose_name = verbose_name
        self.field = field
        self.change = change

    def render_diff(self, template, context):
        from django.template.loader import render_to_string

        return render_to_string(template, context)


class TextChange(BaseChange):

    @property
    def diff(self):
        value1, value2 = escape(self.change[0]), escape(self.change[1])
        if value1 == value2:
            return value1

        return self.render_diff(
            'moderation/html_diff.html',
                {'diff_operations': get_diff_operations(*self.change)})


class ImageChange(BaseChange):

    @property
    def diff(self):
        left_image, right_image = self.change
        return self.render_diff(
            'moderation/image_diff.html',
                {'left_image': left_image,
                 'right_image': right_image})


def get_change(model1, model2, field):
    try:
        value1 = getattr(model1, "get_%s_display" % field.name)()
        value2 = getattr(model2, "get_%s_display" % field.name)()
    except AttributeError:
        value1 = field.value_from_object(model1)
        value2 = field.value_from_object(model2)

    change = get_change_for_type(
        field.verbose_name,
            (value1, value2),
        field,
        )

    return change


def get_changes_between_models(model1, model2, excludes=[]):
    changes = {}

    for field in model1._meta.fields:
        if not (isinstance(field, (fields.AutoField,))):
            if field.name in excludes:
                continue

            name = u"%s__%s" % (model1.__class__.__name__.lower(), field.name)

            changes[name] = get_change(model1, model2, field)

    return changes


def get_diff_operations(a, b):
    operations = []
    a_words = re.split('(\W+)', a)
    b_words = re.split('(\W+)', b)
    sequence_matcher = difflib.SequenceMatcher(None, a_words, b_words)
    for opcode in sequence_matcher.get_opcodes():
        operation, start_a, end_a, start_b, end_b = opcode

        deleted = ''.join(a_words[start_a:end_a])
        inserted = ''.join(b_words[start_b:end_b])

        operations.append({'operation': operation,
                           'deleted': deleted,
                           'inserted': inserted})
    return operations


def html_to_list(html):
    pattern = re.compile(r'&.*?;|(?:<[^<]*?>)|'\
                         '(?:\w[\w-]*[ ]*)|(?:<[^<]*?>)|'\
                         '(?:\s*[,\.\?]*)', re.UNICODE)

    return [''.join(element) for element in filter(None,
                                                   pattern.findall(html))]


def get_change_for_type(verbose_name, change, field):
    if isinstance(field, fields.files.ImageField):
        change = ImageChange(
            u"Current %(verbose_name)s / "\
            u"New %(verbose_name)s" % {'verbose_name': verbose_name},
            field,
            change)
    else:
        value1, value2 = change
        change = TextChange(verbose_name,
                            field,
                (unicode(value1), unicode(value2)),
                            )

    return change
