from django.db import models
from moderation.db import ModeratedModel


class MyTestModel(ModeratedModel):
    name = models.CharField(max_length=20)
