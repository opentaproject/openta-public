from django import forms
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.forms import ModelForm
from django.template import loader
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy
from django.core.exceptions import ValidationError

from backend.user_utilities import send_activation_mail
from course.models import Course
from users.models import OpenTAUser
from utils import send_email_object


class UserCreateFormNoPassword(ModelForm):
    """Form used for user registration where the password is set after the activation mail is sent."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        self._course_pk = kwargs.pop('course_pk')
        self._request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        course = Course.objects.get(pk=self._course_pk)
        try:
            user = User.objects.get(email=self.cleaned_data['email'])
            user.opentauser.courses.add(course)
            messages.add_message(
                self._request,
                messages.SUCCESS,
                ugettext('User already exists, added you to the course.'),
            )
            return user
        except User.DoesNotExist:
            user = super().save(commit=False)
            user.username = self.cleaned_data["email"]
            user.is_active = False
            user.save()
            openta_user, _ = OpenTAUser.objects.get_or_create(user=user)
            openta_user.courses.add(course)
            send_activation_mail(
                course, user.username, self.cleaned_data["email"], 'user-activation-and-reset'
            )
            messages.add_message(
                self._request,
                messages.SUCCESS,
                ugettext(
                    'Registration complete, check inbox for '
                    'activation mail (possibly spam folder).'
                ),
            )
            return user


class UserCreateFormDomain(ModelForm):
    """Form used for user registration where the password is set after the activation mail is sent."""

    email = forms.EmailField(required=True)
    # first_name = forms.CharField(required=True, label=ugettext_lazy('First name'))
    # last_name = forms.CharField(required=True, label=ugettext_lazy('Last name'))

    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        self._course_pk = kwargs.pop('course_pk')
        self._request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def clean_email(self):
        # Check for a valid email domain
        course = Course.objects.get(pk=self._course_pk)
        domains = course.get_registration_domains()
        user_domain = self.cleaned_data["email"].split('@')[-1]
        if domains is not None:
            if user_domain not in domains:
                raise forms.ValidationError(
                    ugettext("Email domain must be ") + " or ".join(domains)
                )
        return self.cleaned_data["email"]

    def save(self, commit=True):
        course = Course.objects.get(pk=self._course_pk)
        try:
            user = User.objects.get(email=self.cleaned_data['email'])
            user.opentauser.courses.add(course)
            messages.add_message(
                self._request,
                messages.SUCCESS,
                ugettext('User already exists, added you to the course.'),
            )
            return user
        except User.DoesNotExist:
            user = super().save(commit=False)
            user.username = self.cleaned_data["email"]
            user.is_active = False
            user.save()
            openta_user, _ = OpenTAUser.objects.get_or_create(user=user)
            openta_user.courses.add(course)
            send_activation_mail(
                course, user.username, self.cleaned_data["email"], 'user-activation-and-reset'
            )
            messages.add_message(
                self._request,
                messages.SUCCESS,
                ugettext(
                    'Registration complete, check inbox for '
                    'activation mail (possibly spam folder).'
                ),
            )
            return user


class RegisterWithPasswordForm(forms.Form):
    """Form for supplying the password to enter user registration."""

    password = forms.CharField(
        label=ugettext('Registration password'), widget=forms.PasswordInput()
    )


class EmailUsersForm(forms.Form):
    """Email multiple users."""

    subject = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 60}))
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self, request, users):
        sender = request.user.email
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
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email is not registered")
        if User.objects.filter(email__iexact=email, is_active=False).exists():
            raise ValidationError("Account not activated, please look for your activation mail.")
        return email

    def send_mail(
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

        email_message = EmailMessage(subject, body, from_email, [to_email])

        send_email_object(email_message)
