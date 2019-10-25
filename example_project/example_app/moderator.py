from example_project.example_app.models import ExampleUserProfile
from example_project.example_app.models import UserProfileWithCustomUser
from moderation import moderation
from moderation.moderator import GenericModerator


class UserProfileModerator(GenericModerator):
    notify_user = False
    auto_approve_for_superusers = False
    auto_approve_for_staff = False


moderation.register(ExampleUserProfile)
moderation.register(UserProfileWithCustomUser, UserProfileModerator)
