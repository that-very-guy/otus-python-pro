from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.files.images import get_image_dimensions

from .models import UserProfile


AUTH_USER = get_user_model()


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class RegisterUserForm(BootstrapMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = AUTH_USER
        fields = ('username', 'email')


class UpdateUserForm(BootstrapMixin, UserChangeForm):
    password = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True

    class Meta(UserChangeForm.Meta):
        fields = ('username', 'email',)


class UserProfileForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar',)

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']
        if avatar:
            try:
                w, h = get_image_dimensions(avatar)
                max_width = max_height = 1000
                if w > max_width or h > max_height:
                    raise forms.ValidationError(
                            u'Please use an image that is '
                            '%s x %s pixels or smaller.' % (max_width, max_height))
                main, sub = avatar.content_type.split('/')
                if not (main == 'image' and sub in ['jpg', 'jpeg', 'gif', 'png']):
                    raise forms.ValidationError(u'Please use a JPEG, '
                                                'GIF or PNG image.')
            except AttributeError:
                pass
        return avatar
