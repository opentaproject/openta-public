# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import re

from django.template.loader import render_to_string
from django.utils.deprecation import MiddlewareMixin
import logging

from hijack.conf import settings
logger = logging.getLogger(__name__)


__all__ = ["HijackUserMiddleware"]

_HTML_TYPES = ("text/html", "application/xhtml+xml")


class HijackUserMiddleware(MiddlewareMixin):
    """Set `is_hijacked` attribute; render and inject notification."""

    def process_request(self, request):
        """Set `is_hijacked` and override REMOTE_USER header."""
        try :
            if request.session.is_empty():
                return
            request.user.is_hijacked = bool(request.session.get("hijack_history", []))
            if "REMOTE_USER" in request.META and request.user.is_hijacked:
                logger.error(f"HIJACK REQUESTED {request.user}")
                request.META["REMOTE_USER"] = request.user.get_username()
        except Exception as e:
            print(f"HIJACK ERROR {str(e)}")
            #request.META["REMOTE_USER"] = request.user
            return



    def process_response(self, request, response):
        """Render hijack notification and inject into HTML response."""
        #logger.error(f"HIJACK PROCESSED {request.user}")
        if request.session.is_empty():
            # do not touch empty sessions to avoid unnecessary vary on cookie header
            return response

        insert_before = settings.HIJACK_INSERT_BEFORE
        if not getattr(request.user, "is_hijacked", False) or insert_before is None:
            return response

        # Check for responses where the toolbar can't be inserted.
        content_encoding = response.get("Content-Encoding", "")
        content_type = response.get("Content-Type", "").split(";")[0]
        if getattr(response, "streaming", False) or "gzip" in content_encoding or content_type not in _HTML_TYPES:
            return response

        rendered = render_to_string(
            "hijack/notification.html",
            {"request": request, "csrf_token": request.META["CSRF_COOKIE"]},
        )

        # Insert the toolbar in the response.
        # content = response.content.decode(response.charset)
        # pattern = re.escape(insert_before)
        # bits = re.split(pattern, content, flags=re.IGNORECASE)
        # if len(bits) > 1:
        #    bits[-2] += rendered
        #    response.content = insert_before.join(bits)
        #    if "Content-Length" in response:
        response["Content-Length"] = len(response.content)
        return response
