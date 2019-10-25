from django.db import models

from moderation.db import ModeratedModel


class MyTestModel(ModeratedModel):
    name = models.CharField(max_length=20)

    class Moderator:
        notify_user = False
        made_up_value = 'made_up'


class MyTestModelWithoutModerator(ModeratedModel):
    name = models.CharField(max_length=20)
