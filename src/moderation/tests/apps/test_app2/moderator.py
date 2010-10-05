from moderation import moderation
from moderation.tests.apps.test_app2.models import Book


moderation.register(Book)
