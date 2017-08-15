from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.urls import reverse
from django.forms import ModelForm
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from .user_utilities import create_activation_link, send_activation_mail
from course.models import Course


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


class UserCreateFormDomain(ModelForm):
    """
    Form used for user registration where the password is set after the activation mail is sent.
    """

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label=ugettext_lazy('First name'))
    last_name = forms.CharField(required=True, label=ugettext_lazy('Last name'))

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_email(self):
        domains = Course.objects.registration_domains()
        user_domain = self.cleaned_data["email"].split('@')[-1]
        username = self.cleaned_data["email"].split('@')[0]
        if domains is not None:
            if user_domain not in domains:
                raise forms.ValidationError(_("Email domain must be ") + " or ".join(domains))
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "{} {} already exists!".format(_("A user with username"), username)
            )
        return self.cleaned_data["email"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].split("@")[0]
        user.is_active = False
        user.save()
        send_activation_mail(user.username, self.cleaned_data["email"], 'user-activation-and-reset')
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


class EmailUsersForm(forms.Form):
    subject = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 60}))
    message = forms.CharField(widget=forms.Textarea)
