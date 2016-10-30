from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.urls import reverse
from django.forms import ModelForm
from django.utils.translation import ugettext as _
from .user_utilities import create_activation_link, send_activation_mail


class UserCreateFormNoPassword(ModelForm):
    """
    Form used for user registration where the password is set after the activation mail is sent.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        user.save()
        send_activation_mail(
            self.cleaned_data["username"], self.cleaned_data["email"], 'user-activation-and-reset'
        )
        return user


class UserCreateForm(UserCreationForm):
    """
    Form used for user registration where a password is supplied at registration time.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
        send_activation_mail(self.cleaned_data["username"], self.cleaned_data["email"])
        return user


class RegisterWithPasswordForm(forms.Form):
    """
    Form for supplying the password to enter user registration.
    """

    password = forms.CharField(label=_('Registration password'), widget=forms.PasswordInput())


class BatchAddUsersForm(forms.Form):
    """
    Form to upload CSV file for batch user registration.
    """

    batch_file = forms.FileField(label=_("Batch CSV file"), required=False)
