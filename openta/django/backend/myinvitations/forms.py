# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django import forms
from utils import get_subdomain, get_subdomain_and_db
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from django.utils.crypto import get_random_string


from invitations.adapters import get_invitations_adapter
from invitations.base_invitation import AbstractBaseInvitation
from invitations.exceptions import AlreadyAccepted, AlreadyInvited, UserRegisteredEmail
from invitations.utils import get_invitation_model
from invitations.models import Invitation
import random
import logging

logger = logging.getLogger(__name__)

# Invitation = get_invitation_model()

# def mymethod(self, cls, email, inviter=None, **kwargs):
#        logger.debug(f"MYMETHOD")
#        key = get_random_string(64).lower()
#        instance = cls._default_manager.create(
#            email=email,
#            key=key,
#            inviter=inviter,
#            **kwargs)
#        return instance
#
# def amethod(self ):
#    logger.debug(f"AMETHOD")
#    pass
##
# Invitation.create = amethod


class MultiEmailField(forms.Field):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        return [item.strip() for item in value.split(",")]

    def validate(self, value):
        """Check if value consists only of valid emails."""
        # Use the parent's handling of required fields, etc.
        super().validate(value)
        for email in value:
            # logger.debug(f" CHECK EMAIL {email}")
            validate_email(email)


class CleanEmailMixin(object):
    def validate_invitation(self, email):
        if Invitation.objects.all_valid().filter(email__iexact=email, accepted=False):
            raise AlreadyInvited
        elif Invitation.objects.filter(email__iexact=email, accepted=True):
            raise AlreadyAccepted
        elif get_user_model().objects.filter(email__iexact=email):
            raise UserRegisteredEmail
        else:
            return True

    def clean_email(self):
        email = self.cleaned_data["email"]
        email = get_invitations_adapter().clean_email(email)

        errors = {
            "already_invited": _("This e-mail address has already been" " invited."),
            "already_accepted": _("This e-mail address has already" " accepted an invite."),
            "email_in_use": _("An active user is using this e-mail address"),
        }
        try:
            self.validate_invitation(email)
        except (AlreadyInvited):
            raise forms.ValidationError(errors["already_invited"])
        except (AlreadyAccepted):
            raise forms.ValidationError(errors["already_accepted"])
        except (UserRegisteredEmail):
            raise forms.ValidationError(errors["email_in_use"])
        return email


class InviteForm(forms.Form, CleanEmailMixin):

    email = forms.EmailField(
        label=_("E-mail"), required=True, widget=forms.TextInput(attrs={"type": "email", "size": "30"}), initial=""
    )

    def save(self, email):
        return Invitation.create(email=email)


class HtmlWidget(forms.widgets.Widget):
    """A widget to display HTML in admin fields."""

    input_type = None  # Subclasses must define this.

    def render(self, name, value, attrs=None):
        if value is None:
            value = ""
        return mark_safe("%s" % value)


class InvitationAdminAddForm(forms.ModelForm, CleanEmailMixin):
    email = forms.EmailField(
        label=_("E-mail"), required=True, widget=forms.TextInput(attrs={"type": "email", "size": "30"})
    )

    def save(self, *args, **kwargs):
        cleaned_data = super(InvitationAdminAddForm, self).clean()
        email = cleaned_data.get("email")
        params = {"email": email}
        if cleaned_data.get("inviter"):
            params["inviter"] = cleaned_data.get("inviter")
        instance = Invitation.create(**params)
        instance.save()
        instance.send_invitation(self.request)
        super(InvitationAdminAddForm, self).save(*args, **kwargs)
        return instance

    class Meta:
        model = Invitation
        fields = ("email", "inviter")


class InvitationAdminAddManyForm(forms.ModelForm, CleanEmailMixin):
    class Meta:
        model = Invitation
        fields = (
            "emails",
            "inviter",
            "role",
        )

    def __init__(self, *args, **kwargs):
        super(InvitationAdminAddManyForm, self).__init__(*args, **kwargs)

    # emails = forms.CharField(
    #    label= "List of emails",
    #    required=True,
    #    widget=forms.Textarea(attrs={"rows": 4, "cols": 10 })
    #    )

    # https://docs.djangoproject.com/en/4.0/ref/forms/validation/

    emails = MultiEmailField(
        label="emails",
        widget=forms.Textarea(attrs={"rows": 4, "cols": 40}),
        help_text="<h3> Enter a  comma separated list emails </h3> <h3> Make sure use_email is enabled and and that emails are really working.</h3>",
    )
    CHOICES = [("1", "Student"), ("2", "View"), ("3", "Author"), ("4", "Admin")]
    role = forms.ChoiceField(
        label="roles", initial=1, widget=forms.RadioSelect, choices=CHOICES, help_text="The role in the invitation"
    )

    def save_m2m(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        # logger.debug(f"SAVE ADD MANY ")
        # cleaned_data = super(InvitationAdminAddManyForm, self).clean()
        emails = self.cleaned_data.get("emails")
        role = self.cleaned_data.get("role")
        print(f"ROLE = {role}")
        request = self.request
        subdomain, db = get_subdomain_and_db(request)
        qs = list(Invitation.objects.using(db).all().values_list("email", flat=True))
        qt = list(User.objects.using(db).all().values_list("email", flat=True))
        all_emails = qs + qt
        instance = None
        for email in emails:
            email = email.strip()
            # if cleaned_data.get("inviter"):
            #    params['inviter'] = cleaned_data.get("inviter")
            params = {"email": email, "inviter": self.request.user}
            try:
                key = get_random_string(5).lower()  # + '_' + str( random.randint(100,999) )
                key = f"{role}{key}"
                url = f"https://{settings.SUBDOMAIN}.{settings.SERVER}/invitations/accept-invite/{key}"
                print(f"TRY email={email}")
                if not email in all_emails:
                    print(f"NEW")
                    instance = Invitation.create(**params)
                    # instance.key = get_random_string(3).upper() + '-' + get_random_string(3).upper()
                    instance.key = key
                    # print(f" REQUEST {self.request}")
                    instance.send_invitation(self.request)
                    super(InvitationAdminAddManyForm, self).save(*args, **kwargs)
                    messages.success(request, f" invite to {email} sent {url} ")
                else:
                    if email in qs:
                        messages.warning(request, f" invite to {email} already exists and was not sent ")
                        instance = Invitation.objects.get(email=email).save(*args, **kwargs)
                    else:
                        messages.warning(request, f" user with {email} already exists and invite was not  sent")
            except Exception as e:
                messages.error(request, f" invite to {email} failed  {url} ")
                logger.debug(f"BORKED on {params} {type(e).__name__ } {str(e)} ")
        if instance:
            return instance
        else:
            return self.instance


class InvitationAdminChangeForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = "__all__"


class SendManyInvitesForm(forms.Form):
    emails = MultiEmailField(
        label="emails",
        widget=forms.Textarea(attrs={"rows": 4, "cols": 40}),
        help_text="Enter a comma-separated list of emails.",
    )
    CHOICES = [("1", "Student"), ("2", "View"), ("3", "Author"), ("4", "Admin")]
    role = forms.ChoiceField(label="roles", initial="1", widget=forms.RadioSelect, choices=CHOICES)
