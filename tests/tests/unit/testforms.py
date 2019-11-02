from django.contrib.auth.models import User
from django.db.models.fields.files import ImageFieldFile
from django.forms import CharField
from django.test.testcases import TestCase

from moderation.forms import BaseModeratedObjectForm
from tests.models import ModelWithImage, UserProfile
from tests.utils import setup_moderation, teardown_moderation


class FormsTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        self.user = User.objects.get(username='moderator')

        class ModeratedObjectForm(BaseModeratedObjectForm):
            extra = CharField(required=False)

            class Meta:
                model = UserProfile
                fields = '__all__'

        self.ModeratedObjectForm = ModeratedObjectForm
        self.moderation = setup_moderation([UserProfile, ModelWithImage])

    def tearDown(self):
        teardown_moderation()

    def test_create_form_class(self):
        form = self.ModeratedObjectForm()
        self.assertEqual(form._meta.model.__name__, 'UserProfile')

    def test_if_form_is_initialized_new_object(self):
        profile = UserProfile(description='New description',
                              url='http://test.com',
                              user=self.user)
        profile.save()

        form = self.ModeratedObjectForm(instance=profile)
        self.assertEqual(form.initial['description'], 'New description')

    def test_if_form_is_initialized_existing_object(self):
        profile = UserProfile(description='old description',
                              url='http://test.com',
                              user=self.user)
        profile.save()

        profile.moderated_object.approve(by=self.user)

        profile.description = 'Changed description'
        profile.save()

        form = self.ModeratedObjectForm(instance=profile)

        profile = UserProfile.objects.get(id=1)

        self.assertEqual(profile.description, 'old description')
        self.assertEqual(form.initial['description'], 'Changed description')

    def test_if_form_has_image_field_instance_of_image_field_file(self):
        object = ModelWithImage(image='my_image.jpg')
        object.save()

        object = ModelWithImage.unmoderated_objects.get(id=1)
        form = self.ModeratedObjectForm(instance=object)
        self.assertTrue(isinstance(form.initial['image'], ImageFieldFile),
                        'image in form.initial is instance of ImageField File')

    def test_form_when_obj_has_no_moderated_obj(self):
        self.moderation.unregister(UserProfile)
        profile = UserProfile(description='old description',
                              url='http://test.com',
                              user=self.user)
        profile.save()
        self.moderation.register(UserProfile)

        form = self.ModeratedObjectForm(instance=profile)

        self.assertEqual(form.initial['description'], 'old description')

    def test_if_form_is_initialized_new_object_with_initial(self):
        profile = UserProfile(description='New description',
                              url='http://test.com',
                              user=self.user)
        profile.save()

        form = self.ModeratedObjectForm(initial={'extra': 'value'},
                                        instance=profile)

        self.assertEqual(form.initial['description'], 'New description')
        self.assertEqual(form.initial['extra'], 'value')
