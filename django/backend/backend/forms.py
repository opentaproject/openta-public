from django import forms
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.forms import ModelForm
from django.template import loader
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.core.exceptions import ValidationError

from backend.user_utilities import send_activation_mail
from course.models import Course
from utils import send_email_object


class UserCreateFormNoPassword(ModelForm):
    """Form used for user registration where the password is set after the activation mail is sent."""

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
    """Form used for user registration where the password is set after the activation mail is sent."""

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
            message = (
                "{} {} already exists! \n If it is not you, "
                "contact admin to register another username on your email email"
            )
            formatted = message.format(_("A user with username"), username)
            raise forms.ValidationError(formatted)
        return self.cleaned_data["email"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].split("@")[0]
        user.is_active = False
        user.save()
        send_activation_mail(user.username, self.cleaned_data["email"], 'user-activation-and-reset')
        return user


class UserCreateForm(UserCreationForm):
    """Form used for user registration where a password is supplied at registration time."""

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
    """Form for supplying the password to enter user registration."""

    password = forms.CharField(label=_('Registration password'), widget=forms.PasswordInput())


class BatchAddUsersForm(forms.Form):
    """Form to upload CSV file for batch user registration."""

    batch_file = forms.FileField(label=_("Batch CSV file"), required=False)


class EmailUsersForm(forms.Form):
    """Email multiple users."""

    subject = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 60}))
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self, request, users):
        course = Course.objects.first()
        sender = Course.objects.course_email()
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['message']
        for user in users:
            if user.email:
                email_object = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=sender,
                    to=[user.email],
                    reply_to=[sender],
                )
                send_email_object(email_object)
                messages.add_message(request, messages.SUCCESS, "Email sent to " + user.username)


class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError("Email not registered (or the account is not activated).")
        return email

    def send_email(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        send_email_object(email_message)
