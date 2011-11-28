from django.contrib import admin
from django.forms.models import ModelForm
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
import django

from moderation.models import ModeratedObject, MODERATION_DRAFT_STATE,\
    MODERATION_STATUS_PENDING, MODERATION_STATUS_REJECTED,\
    MODERATION_STATUS_APPROVED

from django.utils.translation import ugettext as _
from moderation.forms import BaseModeratedObjectForm
from moderation.helpers import automoderate
from moderation.diff import get_changes_between_models


def approve_objects(modeladmin, request, queryset):
    for obj in queryset:
        obj.approve(moderated_by=request.user)

approve_objects.short_description = "Approve selected moderated objects"


def reject_objects(modeladmin, request, queryset):
    for obj in queryset:
        obj.reject(moderated_by=request.user)

reject_objects.short_description = "Reject selected moderated objects"


def set_objects_as_pending(modeladmin, request, queryset):
    queryset.update(moderation_status=MODERATION_STATUS_PENDING)

set_objects_as_pending.short_description = "Set selected moderated objects "\
                                           "as Pending"


class ModerationAdmin(admin.ModelAdmin):
    admin_integration_enabled = True

    def get_form(self, request, obj=None):
        if obj and self.admin_integration_enabled:
            return self.get_moderated_object_form(obj.__class__)

        return super(ModerationAdmin, self).get_form(request, obj)

    def change_view(self, request, object_id, extra_context=None):
        if self.admin_integration_enabled:
            self.send_message(request, object_id)

        return super(ModerationAdmin, self).change_view(request, object_id)

    def send_message(self, request, object_id):
        try:
            obj = self.model.unmoderated_objects.get(pk=object_id)
            moderated_obj = ModeratedObject.objects.get_for_instance(obj)
            moderator = moderated_obj.moderator
            msg = self.get_moderation_message(moderated_obj.moderation_status,
                                              moderated_obj.moderation_reason,
                                              moderator.visible_until_rejected)
        except ModeratedObject.DoesNotExist:
            msg = self.get_moderation_message()

        self.message_user(request, msg)

    def save_model(self, request, obj, form, change):
        obj.save()
        automoderate(obj, request.user)

    def get_moderation_message(self, moderation_status=None, reason=None,
                               visible_until_rejected=False):
        if moderation_status == MODERATION_STATUS_PENDING:
            if visible_until_rejected:
                return _(u"Object is viewable on site, "\
                         "it will be removed if moderator rejects it")
            else:
                return _(u"Object is not viewable on site, "\
                         "it will be visible if moderator accepts it")
        elif moderation_status == MODERATION_STATUS_REJECTED:
            return _(u"Object has been rejected by moderator, "\
                     "reason: %s" % reason)
        elif moderation_status == MODERATION_STATUS_APPROVED:
            return _(u"Object has been approved by moderator "\
                     "and is visible on site")
        elif moderation_status is None:
            return _("This object is not registered with "\
                     "the moderation system.")

    def get_moderated_object_form(self, model_class):

        class ModeratedObjectForm(BaseModeratedObjectForm):

            class Meta:
                model = model_class

        return ModeratedObjectForm


class ModeratedObjectAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    list_display = ('content_object', 'content_type', 'date_created',
                    'moderation_status', 'moderated_by', 'moderation_date')
    list_filter = ['content_type', 'moderation_status']
    change_form_template = 'moderation/moderate_object.html'
    change_list_template = 'moderation/moderated_objects_list.html'
    actions = [reject_objects, approve_objects, set_objects_as_pending]
    fieldsets = (
            ('Object moderation', {'fields': ('moderation_reason',)}),
        )

    def get_actions(self, request):
        actions = super(ModeratedObjectAdmin, self).get_actions(request)
        # Remove the delete_selected action if it exists
        try:
            del actions['delete_selected']
        except KeyError:
            pass
        return actions

    def content_object(self, obj):
        return unicode(obj.changed_object)

    def queryset(self, request):
        qs = super(ModeratedObjectAdmin, self).queryset(request)

        return qs.exclude(moderation_state=MODERATION_DRAFT_STATE)

    def get_moderated_object_form(self, model_class):

        class ModeratedObjectForm(ModelForm):

            class Meta:
                model = model_class

        return ModeratedObjectForm

    def change_view(self, request, object_id, extra_context=None):
        from moderation import moderation

        moderated_object = ModeratedObject.objects.get(pk=object_id)

        changed_obj = moderated_object.changed_object

        moderator = moderation.get_moderator(changed_obj.__class__)

        if moderator.visible_until_rejected:
            old_object = changed_obj
            new_object = moderated_object.get_object_for_this_type()
        else:
            old_object = moderated_object.get_object_for_this_type()
            new_object = changed_obj

        changes = get_changes_between_models(
            old_object,
            new_object,
            moderator.fields_exclude).values()
        if request.POST:
            admin_form = self.get_form(request, moderated_object)(request.POST)

            if admin_form.is_valid():
                reason = admin_form.cleaned_data['moderation_reason']
                if 'approve' in request.POST:
                    moderated_object.approve(request.user, reason)
                elif 'reject' in request.POST:
                    moderated_object.reject(request.user, reason)

        content_type = ContentType.objects.get_for_model(changed_obj.__class__)
        try:
            object_admin_url = urlresolvers.reverse("admin:%s_%s_change" %
                                                    (content_type.app_label,
                                                     content_type.model),
                                                    args=(changed_obj.pk,))
        except urlresolvers.NoReverseMatch:
            object_admin_url = None

        extra_context = {'changes': changes,
                         'django_version': django.get_version()[:3],
                         'object_admin_url': object_admin_url}
        return super(ModeratedObjectAdmin, self).change_view(request,
                                                             object_id,
                                                             extra_context)


admin.site.register(ModeratedObject, ModeratedObjectAdmin)
