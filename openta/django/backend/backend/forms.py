# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django import forms
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.forms import ModelForm
from django.template import loader
from django.utils.translation import gettext, gettext_lazy
from django.core.exceptions import ValidationError
import logging

from backend.user_utilities import send_activation_mail
from course.models import Course
from users.models import OpenTAUser
from utils import send_email_object, send_email_objects
import re

logger = logging.getLogger(__name__)


class UserCreateFormNoPassword(ModelForm):
    """Form used for user registration where the password is set after the activation mail is sent."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        self._course_pk = kwargs.pop("course_pk")
        self._request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        course = Course.objects.get(pk=self._course_pk)
        try:
            user = User.objects.get(email=self.cleaned_data["email"])
            user.opentauser.courses.add(course)
            messages.add_message(
                self._request,
                messages.SUCCESS,
                gettext("User already exists, added you to the course."),
            )
            return user
        except User.DoesNotExist:
            user = super().save(commit=False)
            user.username = self.cleaned_data["email"]
            user.is_active = False
            user.save()
            openta_user, _ = OpenTAUser.objects.get_or_create(user=user)
            openta_user.courses.add(course)
            send_activation_mail(course, user.username, self.cleaned_data["email"], "user-activation-and-reset")
            msg_body = (
                "Registration is almost complete. Check your inbox at %s  (or spam folder) for activation mail in order to set a password)."
                % user.username
            )

            messages.add_message(
                self._request,
                messages.SUCCESS,
                gettext(msg_body),
            )
            return user


class UserCreateFormDomain(ModelForm):
    """Form used for user registration where the password is set after the activation mail is sent."""

    email = forms.EmailField(required=True)
    # first_name = forms.CharField(required=True, label=gettext_lazy('First name'))
    # last_name = forms.CharField(required=True, label=gettext_lazy('Last name'))

    class Meta:
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs):
        # print("KWARGS IN UserCreateFormDomain" , kwargs)
        self._course_pk = kwargs.pop("course_pk")
        self._anonymoususer = kwargs.pop("anonymoususer", None)
        self._request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def clean_email(self):
        # Check for a valid email domain
        course = Course.objects.get(pk=self._course_pk)
        domains = course.get_registration_domains()
        user_domain = self.cleaned_data["email"].split("@")[-1]
        # print(f"USER_CREATE_FORM_DOMAIN {self._anonymoususer}")
        if (
            domains is not None and not domains == "*"
        ):  # and not ( self._anonymoususer is None ) : ### COMMENTED_OUT_TO_PASS_TESTS
            matched = False
            for domain in domains:
                if re.match(r"%s" % domain, user_domain):
                    matched = True
            if not matched:
                raise forms.ValidationError(gettext("Email domain must be ") + " or ".join(domains))
        return self.cleaned_data["email"]

    def save(self, commit=True):
        # print("USER_CREATE_FORM_DOMAIN COURSE PK %s " % self._course_pk)
        # print("USER_CREATE_FORM_DOMAIN_anonymoususer %s " % self._anonymoususer)
        email = self.cleaned_data["email"]
        course = Course.objects.get(pk=self._course_pk)
        if course.get_registration_domains():
            msg_body = (
                f" Check your inbox at {email}  (or spam folder) for activation mail in order to set a password. "
            )
        else:
            msg_body = (
                "DO NOT LOG OUT!  Registration is almost complete. Check your inbox at %s (or spam folder) for activation mail in order to set a password. You can click OK and keep working; it may take ten minutes or so for mail to arrive;  do not log out until you have have received the activation mail and from there successfully set your password)."
                % email
            )
        try:
            user = User.objects.get(username=self._anonymoususer)
            user.email = self.cleaned_data["email"]
            user.save()
            openta_user, _ = OpenTAUser.objects.get_or_create(user=user)
            openta_user.courses.add(course)
            send_activation_mail(course, user.username, self.cleaned_data["email"], "user-activation-and-reset")
            messages.add_message(
                self._request,
                messages.ERROR,
                gettext(msg_body),
            )
            return user
        except:
            pass

        try:
            user = User.objects.get(email=self.cleaned_data["email"])
            user.opentauser.courses.add(course)
            messages.add_message(
                self._request,
                messages.SUCCESS,
                gettext("User already exists, added you to the course."),
            )
            return user
        except User.DoesNotExist:
            user = super().save(commit=False)
            user.email = self.cleaned_data["email"]
            user.username = user.email
            user.is_active = False
            user.save()
            openta_user, _ = OpenTAUser.objects.get_or_create(user=user)
            openta_user.courses.add(course)
            send_activation_mail(course, user.username, self.cleaned_data["email"], "user-activation-and-reset")
            messages.add_message(
                self._request,
                messages.ERROR,
                gettext(msg_body),
            )
            return user


class RegisterWithPasswordForm(forms.Form):
    """Form for supplying the password to enter user registration."""

    password = forms.CharField(label=gettext("Registration password"), widget=forms.PasswordInput())


class EmailUsersForm(forms.Form):
    """Email multiple users."""

    subject = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"size": 60}))
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self, request, users):
        sender = request.user.email
        if not sender:
            sender = settings.DEFAULT_FROM_EMAIL
        subject = self.cleaned_data["subject"]
        body = self.cleaned_data["message"]
        emails = []
        usernames = []
        for user in users:
            if user.email:
                usernames = usernames + [user.username]
                email_object = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=sender,
                    to=[user.email],
                    reply_to=[sender],
                )
                emails = emails + [ email_object ]
        send_email_objects(emails)
        messages.add_message(request, messages.SUCCESS, f"Email sent to  + {usernames}")


class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        logger.info("CLEAN EMAIL")
        email = self.cleaned_data["email"]
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
        logger.info("CustomPassworResetForm ")
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        context["host"] = f"{settings.SUBDOMAIN}.{settings.OPENTA_SERVER}"
        # print(f"self = {self} {vars(self)} {self.__dict__} ")
        # print(f"DATA = {self.data}")
        body = loader.render_to_string(email_template_name, context)
        email_message = EmailMessage(subject, body, from_email, [to_email])

        send_email_object(email_message)
