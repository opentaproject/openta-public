# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json

from course.models import Course
from invitations.adapters import get_invitations_adapter
from invitations.app_settings import app_settings
from invitations.exceptions import AlreadyAccepted, AlreadyInvited, UserRegisteredEmail
from invitations.forms import CleanEmailMixin
from invitations.signals import invite_accepted
from invitations.utils import get_invitation_model, get_invite_form
from users.models import OpenTAUser
from utils import get_subdomain_and_db

from backend.views import csrf_failure
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, View
from django.views.generic.detail import SingleObjectMixin

Invitation = get_invitation_model()
InviteForm = get_invite_form()
import logging

logger = logging.getLogger(__name__)


def _send_many_invites_logic(request, emails, role="1"):
    results = {"invited": [], "skipped": [], "errors": []}
    subdomain, db = get_subdomain_and_db(request)
    existing_invites = set(Invitation.objects.using(db).all().values_list("email", flat=True))
    existing_users = set(User.objects.using(db).all().values_list("email", flat=True))

    for email in emails:
        try:
            validate_email(email)
        except ValidationError:
            results["errors"].append({email: "invalid email"})
            continue

        if email in existing_users:
            results["skipped"].append({email: "user exists"})
            continue
        if email in existing_invites:
            results["skipped"].append({email: "invite exists"})
            continue

        try:
            params = {"email": email, "inviter": request.user}
            instance = Invitation.create(**params)
            from django.utils.crypto import get_random_string
            key = f"{role}{get_random_string(5).lower()}"
            instance.key = key
            instance.save()
            instance.send_invitation(request)
            results["invited"].append({email: "sent"})
        except Exception as e:
            logger.error(f"INVITE_SEND_FAILED {type(e).__name__} {str(e)} for {email}")
            results["errors"].append({email: "send failed"})
    return results


class SendInvite(FormView):
    template_name = "invitations/forms/_invite.html"
    form_class = InviteForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        # print(f" SEND INVITE REQUEST = {request} args={args} kwargs={kwargs}")
        return super(SendInvite, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        username = email.split('@')[0];

        try:
            invite = form.save(email)
            invite.inviter = self.request.user
            invite.username = username
            invite.save()
            invite.send_invitation(self.request)
        except Exception:
            return self.form_invalid(form)
        return self.render_to_response(
            self.get_context_data(success_message=_("%(email)s has been invited") % {"email": email})
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class SendJSONInvite(View):
    http_method_names = ["post"]

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if app_settings.ALLOW_JSON_INVITES:
            return super(SendJSONInvite, self).dispatch(request, *args, **kwargs)
        else:
            raise Http404

    def post(self, request, *args, **kwargs):
        status_code = 400
        invitees = json.loads(request.body.decode())
        response = {"valid": [], "invalid": []}
        if isinstance(invitees, list):
            for invitee in invitees:
                try:
                    validate_email(invitee)
                    CleanEmailMixin().validate_invitation(invitee)
                    invite = Invitation.create(invitee)
                except (ValueError, KeyError):
                    pass
                except ValidationError:
                    response["invalid"].append({invitee: "invalid email"})
                except AlreadyAccepted:
                    response["invalid"].append({invitee: "already accepted"})
                except AlreadyInvited:
                    response["invalid"].append({invitee: "pending invite"})
                except UserRegisteredEmail:
                    response["invalid"].append({invitee: "user registered email"})
                else:
                    invite.send_invitation(request)
                    response["valid"].append({invitee: "invited"})

        if response["valid"]:
            status_code = 201

        return HttpResponse(json.dumps(response), status=status_code, content_type="application/json")


class SendManyInvites(View):
    http_method_names = ["post"]

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SendManyInvites, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode()) if request.body else {}
        except Exception:
            payload = {}

        # Accept either a comma-separated string or a list under "emails".
        emails_raw = payload.get("emails", request.POST.get("emails", ""))
        role = str(payload.get("role", request.POST.get("role", "1")))

        if isinstance(emails_raw, list):
            emails = emails_raw
        elif isinstance(emails_raw, str):
            emails = [e.strip() for e in emails_raw.split(",") if e.strip()]
        else:
            emails = []

        # Map role digit to label is handled downstream; we only prefix key with role digit here.
        results = _send_many_invites_logic(request, emails, role)

        status_code = 201 if results["invited"] else 400
        return HttpResponse(json.dumps(results), status=status_code, content_type="application/json")


from .forms import SendManyInvitesForm


class SendManyInvitesPage(FormView):
    template_name = "invitations/send_many.html"
    form_class = SendManyInvitesForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SendManyInvitesPage, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        emails = form.cleaned_data["emails"]
        role = form.cleaned_data["role"]
        results = _send_many_invites_logic(self.request, emails, role)
        return self.render_to_response(self.get_context_data(form=form, results=results))


def create_user_with_email_password(db, email, course, password=None, role="Student"):
    username = email.split('@')[0]
    if password == None:
        password = username
    user = User(username=username, email=email)
    user.save()
    user.set_password(password)
    user.save()
    opentauser = OpenTAUser(user=user)
    opentauser.save()
    course = list(Course.objects.using(db).all())[0]
    opentauser.courses.add(course)
    opentauser.save()
    user.save()
    user.opentauser = opentauser
    user.save()
    groupname = role
    group = Group.objects.using(db).get(name=groupname)
    if groupname in ["Admin", "Author"]:
        user.is_staff = True
    user.groups.add(group)
    if groupname == "Admin" : # ASSIGN AUTHOR TO ADMIN
        group = Group.objects.using(db).get(name="Author")
        user.groups.add(group)

    user.save()
    return user


class AcceptInvite(SingleObjectMixin, View):
    form_class = InviteForm

    def get_signup_redirect(self):
        logger.debug(f"CUSTOM GET_SIGNUP_REDIRECT")
        db, subdomain = get_subdomain_and_db(self.request)
        invitation = self.get_object()
        password = str(invitation.key)
        email = invitation.email
        key = invitation.key
        rolekey = key[0]
        CHOICES = {"1": "Student", "2": "View", "3": "Author", "4": "Admin"}
        role = CHOICES[rolekey]
        course = list(Course.objects.using(db).all())[0]
        logger.debug(f"CUSTOM CREATE email = {email}  key={password}")
        user = create_user_with_email_password(db, email, course, password=password, role=role)
        logger.debug(f" NOW RETURN SIGNUP REDIRECT to /")
        return "/"
        # return app_settings.SIGNUP_REDIRECT

    def get(self, *args, **kwargs):
        logger.debug(f"CUSTOM INVITE GET {args} {kwargs}")
        try:
            if app_settings.CONFIRM_INVITE_ON_GET:
                return self.post(*args, **kwargs)
            else:
                raise Http404
        except:
            return HttpResponse("what now")
            return csrf_failure(self.request, reason="You already have an account; ask for password reset")

    def post(self, *args, **kwargs):
        logger.error(f"CUSTOM INVITE POST {args} {kwargs}")
        self.object = invitation = self.get_object()

        # Compatibility with older versions: return an HTTP 410 GONE if there
        # is an error. # Error conditions are: no key, expired key or
        # previously accepted key.
        if settings.GONE_ON_ACCEPT_ERROR and (
            not invitation or (invitation and (invitation.accepted or invitation.key_expired()))
        ):
            return HttpResponse(status=410)

        # No invitation was found.
        if not invitation:
            # Newer behavior: show an error message and redirect.
            get_invitations_adapter().add_message(
                self.request, messages.ERROR, "invitations/messages/invite_invalid.txt"
            )
            return redirect(app_settings.LOGIN_REDIRECT)

        # The invitation was previously accepted, redirect to the login
        # view.
        if invitation.accepted:
            get_invitations_adapter().add_message(
                self.request,
                messages.ERROR,
                "invitations/messages/invite_already_accepted.txt",
                {"email": invitation.email},
            )
            # Redirect to login since there's hopefully an account already.
            return redirect(app_settings.LOGIN_REDIRECT)

        # The key was expired.
        if invitation.key_expired():
            get_invitations_adapter().add_message(
                self.request, messages.ERROR, "invitations/messages/invite_expired.txt", {"email": invitation.email}
            )
            # Redirect to sign-up since they might be able to register anyway.
            return redirect(self.get_signup_redirect())

        # The invitation is valid.
        # Mark it as accepted now if ACCEPT_INVITE_AFTER_SIGNUP is False.
        if not app_settings.ACCEPT_INVITE_AFTER_SIGNUP:
            accept_invitation(invitation=invitation, request=self.request, signal_sender=self.__class__)

        get_invitations_adapter().stash_verified_email(self.request, invitation.email)

        return redirect(self.get_signup_redirect())

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        try:
            return queryset.get(key=self.kwargs["key"].lower())
        except Invitation.DoesNotExist:
            return None

    def get_queryset(self):
        return Invitation.objects.all()


def accept_invitation(invitation, request, signal_sender):
    invitation.accepted = True
    invitation.save()

    invite_accepted.send(sender=signal_sender, email=invitation.email)

    get_invitations_adapter().add_message(
        request, messages.SUCCESS, "invitations/messages/invite_accepted.txt", {"email": invitation.email}
    )


def accept_invite_after_signup(sender, request, user, **kwargs):
    invitation = Invitation.objects.filter(email__iexact=user.email).first()
    if invitation:
        accept_invitation(invitation=invitation, request=request, signal_sender=Invitation)


if app_settings.ACCEPT_INVITE_AFTER_SIGNUP:
    signed_up_signal = get_invitations_adapter().get_user_signed_up_signal()
    signed_up_signal.connect(accept_invite_after_signup)
