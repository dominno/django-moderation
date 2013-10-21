from django import VERSION

from moderation import moderation
from example_project.example_app.models import ExampleUserProfile


from moderation.moderator import GenericModerator


class UserProfileModerator(GenericModerator):
    notify_user = False
    auto_approve_for_superusers = False
    auto_approve_for_staff = False


moderation.register(ExampleUserProfile)

if VERSION[:2] >= (1, 5):
    from example_project.example_app.models import UserProfileWithCustomUser
    moderation.register(UserProfileWithCustomUser, UserProfileModerator)
