from django.contrib import admin
from example_project.example_app.models import ExampleUserProfile
from moderation.admin import ModerationAdmin


class ExampleUserProfileAdmin(admin.ModelAdmin):
    pass
    
    
admin.site.register(ExampleUserProfile, ExampleUserProfileAdmin)

