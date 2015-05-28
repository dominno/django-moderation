# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
try:
    from django.contrib.auth import get_user_model
except ImportError: # django < 1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()

USER_MODEL = "%s.%s" % (User._meta.app_label, User._meta.object_name)


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'ModeratedObject'
        db.create_table('moderation_moderatedobject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_pk', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('moderation_state', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),  # draft state
            ('moderation_status', self.gf('django.db.models.fields.SmallIntegerField')(default=2)),
            ('moderated_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='moderated_by_set', null=True, to=orm[USER_MODEL])),
            ('moderation_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('moderation_reason', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('changed_object', self.gf('moderation.fields.SerializedObjectField')()),
            ('changed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='changed_by_set', null=True, to=orm[USER_MODEL])),
        ))
        db.send_create_signal('moderation', ['ModeratedObject'])

    def backwards(self, orm):

        # Deleting model 'ModeratedObject'
        db.delete_table('moderation_moderatedobject')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        # this should replace "auth.user"
        "%s.%s" % (User._meta.app_label, User._meta.module_name): {
        'Meta': {'object_name': User.__name__},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'moderation.moderatedobject': {
            'Meta': {'ordering': "['moderation_status', 'date_created']", 'object_name': 'ModeratedObject'},
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'changed_by_set'", 'null': 'True', 'to': "orm['%s']" % USER_MODEL}),
            'changed_object': ('moderation.fields.SerializedObjectField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderated_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'moderated_by_set'", 'null': 'True', 'to': "orm['%s']" % USER_MODEL}),
            'moderation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'moderation_reason': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'moderation_state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'moderation_status': ('django.db.models.fields.SmallIntegerField', [], {'default': '2'}),
            'object_pk': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['moderation']

