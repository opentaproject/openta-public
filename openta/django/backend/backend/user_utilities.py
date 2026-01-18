# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import os

from utils import get_localized_template, send_email_object

from django.core.mail import EmailMessage
from django.core.signing import TimestampSigner
from django.shortcuts import reverse
from django.utils.translation import gettext as _
import importlib.util

logger = logging.getLogger(__name__)

def dynamic_import(module_name, file_path):
    # Check if the file exists
    if os.path.exists(file_path):
        # Load the module from the file path
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # Load the module
        return module
    else:
        print(f"File '{file_path}' does not exist.")
        return None
    





def create_activation_link(username, reverse_name="user-activation"):
    """Create an activation link for a user.

    Args:
        username:
        reverse_name: Which url to append the activation token to.
            - user-activation (default)
            - user-activation-and-reset (set password at activation)

    Returns:
        The activation url.

    """
    token = TimestampSigner().sign(username).split(":", 1)[1]
    return reverse(reverse_name, kwargs={"username": username, "token": token})


def send_activation_mail(course, username, email, reverse_name="user-activation"):
    """Sends an activation email after user registration.

    Args:
        course (Course): The course for which the activation mail should be sent.
        username:
        email:
        reverse_name: Which url to append the activation token to.
            - user-activation (default)
            - user-activation-and-reset (set password at activation)

    Returns:
        Activation url.

    """
    course_url = course.url if course.url is not None else "https://openta.se/" + course.course_name.lower()
    base_url = course.url if course.url is not None else "https://openta.se"
    # it needs to be stripped from one of them.
    template = get_localized_template("mail_activation")
    token = TimestampSigner().sign(username).split(":", 1)[1]
    course_email = course.email_reply_to.strip()
    activate_url = "%s%s/%s/%s/" % (base_url, "activateandreset", username, token)
    pcontext = {
        "course_name": "OpenTA",
        "course_url": course_url,
        "username": username,
        "activate_url": activate_url,
        "course_email": course_email,
    }
    sender = course_email
    subject = "OpenTA"

    if course is not None:
        sender = course.course_name.lower()
        subject = course.course_long_name
        pcontext.update(
            {
                "course_name": course.course_name,
                "course_long_name": course.course_long_name,
                "course_url": course_url,
            }
        )
    rendered_email = template.render(pcontext)

    from_email = sender + " <" + sender + "@openta.se>"
    from_email = "opentaproject@gmail.com"
    reply_to = "opentaproject@gmail.com"
    subject = subject + _(" account activation")
    logger.debug("SEND ACTIVATION_EMAIL")
    logger.debug("TO EMAIL = %s", email)
    logger.debug("SUBJECT = %s", subject)
    logger.debug("FROM_EMAIL = %s", from_email)
    logger.debug("REPLOY TO = %s", reply_to)
    logger.debug("RENDERED = %s", rendered_email)

    email_object = EmailMessage(
        subject=subject, body=rendered_email, from_email=from_email, to=[email], reply_to=[reply_to]
    )
    logger.debug("EMAIL MESSAGE = %s", email_object)
    logger.debug("ACTIVATE_URL = %s", activate_url)
    try:
        n_sent = send_email_object(email_object)
        logger.debug("Sent activation mail to email " + email + " (" + str(n_sent) + " delivered)")
    except Exception as e:
        logger.error("Activation email to " + email + " sending failed: " + str(e))
        raise e
    return activate_url
