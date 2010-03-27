# -*- coding: utf-8 -*-

import re
import difflib


def get_changes_between_models(model1, model2, excludes=[]):
    from django.db.models import fields
    changes = {}
    for field in model1._meta.fields:
        if not (isinstance(field, (fields.AutoField,
                                   fields.related.RelatedField))
                or field.name in excludes):
            value2 = unicode(field.value_from_object(model2))
            value1 = unicode(field.value_from_object(model1))
            if value1 != value2:
                changes[field.verbose_name] = (value1, value2)
    return changes


def get_diff(a, b):
    out = []
    sequence_matcher = difflib.SequenceMatcher(None, a, b)
    for opcode in sequence_matcher.get_opcodes():

        operation, start_a, end_a, start_b, end_b = opcode

        deleted = ''.join(a[start_a:end_a])
        inserted = ''.join(b[start_b:end_b])
        
        if operation == "replace":
            out.append('<del class="diff modified">%s</del>'\
                       '<ins class="diff modified">%s</ins>' % (deleted,
                                                                inserted))
        elif operation == "delete":
            out.append('<del class="diff">%s</del>' % deleted)
        elif operation == "insert":
            out.append('<ins class="diff">%s</ins>' % inserted)
        elif operation == "equal":
            out.append(inserted)

    return out


def html_diff(a, b):
    """Takes in strings a and b and returns a human-readable HTML diff."""

    a, b = html_to_list(a), html_to_list(b)
    diff = get_diff(a, b)

    return u"".join(diff)


def html_to_list(html):
    pattern = re.compile(r'&.*?;|(?:<[^<]*?>)|'\
                         '(?:\w[\w-]*[ ]*)|(?:<[^<]*?>)|'\
                         '(?:\s*[,\.\?]*)', re.UNICODE)

    return [''.join(element) for element in filter(None,
                                                   pattern.findall(html))]


def generate_diff(instance1, instance2):
    from django.db.models import fields
    
    changes = get_changes_between_models(instance1, instance2, excludes=['ID'])
    
    fields_diff = []

    for field in instance1._meta.fields:
        if (isinstance(field, (fields.AutoField,
                                   fields.related.RelatedField))):
            continue
        
        field_changes = changes.get(field.verbose_name, None)
        if field_changes:
            change1, change2 = field_changes
            diff = {'verbose_name': field.verbose_name,
                    'diff': html_diff(change1, change2)}
            fields_diff.append(diff)
        else:
            diff = {'verbose_name': field.verbose_name,
                    'diff': field.value_from_object(instance1)}
            fields_diff.append(diff)

    return fields_diff
