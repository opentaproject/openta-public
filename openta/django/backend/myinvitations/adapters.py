# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings
from django.contrib.auth.models import User, Group

from utils import send_email_object
from django.contrib import messages
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

from invitations.app_settings import app_settings
from invitations.utils import import_attribute

# try:
#    from django.utils.encoding import force_text
# except ImportError:
#    from django.utils.encoding import force_unicode as force_text

from invitations.adapters import BaseInvitationsAdapter as OldBaseInvitationsAdapter


class BaseInvitationsAdapter(OldBaseInvitationsAdapter):
    def send_mail(self, template_prefix, email, context):
        # print(f"LOCAL SEND EMAIL ADAPTER {vars(self)} ")
        site = f"{settings.SUBDOMAIN}.{settings.OPENTA_SERVER}"
        context["site_name"] = site
        # print(f" CONTEXT = {context}")
        msg = self.render_mail(template_prefix, email, context)
        msg.subject = f"Invitation to join  {site}"
        from_email = context["inviter"].email
        msg.from_email = from_email
        print(f"MSG = {msg} {vars(msg)} ")
        username = email.split('@')[0]
        msg.body = msg.body.replace('USERNAME',username)
        # print(f"from_email = {from_email}")
        # print(f"SUBJECT = {msg.subject}")
        # print(f"FROM = {msg.from_email}")
        # print(f"MSG = {msg} {msg.__dict__} {vars(msg)}")
        if settings.USE_GMAIL:
            send_email_object(msg)
        else:
            msg.send()
