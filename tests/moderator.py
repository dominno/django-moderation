from __future__ import unicode_literals
from moderation import moderation
from .models import Book


moderation.register(Book)
