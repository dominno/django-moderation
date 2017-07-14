from django.contrib import admin
from django import VERSION

from example_project.example_app.models import ExampleUserProfile

from moderation.admin import ModerationAdmin


class ExampleUserProfileAdmin(ModerationAdmin):
    pass


class UserProfileWithCustomUserAdmin(ModerationAdmin):
    pass


admin.site.register(ExampleUserProfile, ExampleUserProfileAdmin)

if VERSION[:2] >= (1, 5):
    from example_project.example_app.models import UserProfileWithCustomUser, \
        CustomUser

    admin.site.register(UserProfileWithCustomUser,
                        UserProfileWithCustomUserAdmin)

    from django import forms
    from django.contrib import admin
    from django.contrib.auth.admin import UserAdmin
    from django.contrib.auth.forms import ReadOnlyPasswordHashField

    class CustomUserCreationForm(forms.ModelForm):
        """A form for creating new users. Includes all the required
        fields, plus a repeated password."""
        password1 = forms.CharField(label='Password',
                                    widget=forms.PasswordInput)
        password2 = forms.CharField(label='Password confirmation',
                                    widget=forms.PasswordInput)

        class Meta:
            model = CustomUser
            fields = ('username', 'email', 'date_of_birth', )

        def clean_password2(self):
            # Check that the two password entries match
            password1 = self.cleaned_data.get("password1")
            password2 = self.cleaned_data.get("password2")
            if password1 and password2 and password1 != password2:
                raise forms.ValidationError("Passwords don't match")
            return password2

        def save(self, commit=True):
            # Save the provided password in hashed format
            user = super(CustomUserCreationForm, self).save(commit=False)
            user.set_password(self.cleaned_data["password1"])
            if commit:
                user.save()
            return user

    class UserChangeForm(forms.ModelForm):
        """A form for updating users. Includes all the fields on
        the user, but replaces the password field with admin's
        password hash display field.
        """
        password = ReadOnlyPasswordHashField()

        class Meta:
            model = CustomUser
            fields = '__all__'

        def clean_password(self):
            # Regardless of what the user provides, return the initial value.
            # This is done here, rather than on the field, because the
            # field does not have access to the initial value
            return self.initial["password"]

    class MyUserAdmin(UserAdmin):
        # The forms to add and change user instances
        form = UserChangeForm
        add_form = CustomUserCreationForm

        # The fields to be used in displaying the User model.
        # These override the definitions on the base UserAdmin
        # that reference specific fields on auth.User.
        list_display = ('username', 'email', 'date_of_birth', 'is_staff')
        list_filter = ('is_staff',)
        fieldsets = (
            (None, {'fields': ('username', 'email', 'password')}),
            ('Personal info', {'fields': ('date_of_birth',)}),
            ('Permissions', {'fields': ('is_staff',)}),
            ('Important dates', {'fields': ('last_login',)}),
        )
        # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
        # overrides get_fieldsets to use this attribute when creating a user.
        add_fieldsets = (
            (None, {'classes': ('wide',), 'fields': (
                'username', 'email', 'date_of_birth', 'password1', 'password2'
            )}
            ),
        )
        search_fields = ('email',)
        ordering = ('email',)
        filter_horizontal = ()

    # Now register the new UserAdmin...
    admin.site.register(CustomUser, MyUserAdmin)
