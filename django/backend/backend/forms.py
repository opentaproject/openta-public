from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.urls import reverse
from django.forms import ModelForm


class UserCreateFormNoPassword(ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def create_activation_link(self, username):
        token = TimestampSigner().sign(username).split(':', 1)[1]
        print(token)
        return reverse('user-activation-and-reset', kwargs={'username': username, 'token': token})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        user.save()
        activate_url = self.create_activation_link(self.cleaned_data["username"])
        send_mail(
            'Account activation',
            activate_url,
            'openta@missopenta.dyndns.org',
            [self.cleaned_data["email"]],
            fail_silently=False,
        )
        return user


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def create_activation_link(self, username):
        token = TimestampSigner().sign(username).split(':', 1)[1]
        print(token)
        return reverse('user-activation', kwargs={'username': username, 'token': token})

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
        activate_url = self.create_activation_link(self.cleaned_data["username"])
        send_mail(
            'Account activation',
            activate_url,
            'openta@missopenta.dyndns.org',
            [self.cleaned_data["email"]],
            fail_silently=False,
        )
        return user
