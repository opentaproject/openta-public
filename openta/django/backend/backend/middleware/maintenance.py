# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
from django.shortcuts import render, redirect
from django.urls import reverse
from backend.settings import BASE_DIR
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import gettext as _


def MaintenanceMiddleware(get_response):
    """
    Disable access to site if a file named maintenance.lock is present in the root directory by redirecting to the login page. Shows any text in the file as a maintenance message.
    """
    lock_path = os.path.join(BASE_DIR, "maintenance.lock")

    def middleware(request):
        if os.path.isfile(lock_path) and request.user.is_authenticated and not request.user.is_staff:
            with open(lock_path, "r") as f:
                message = f.read()
                messages.add_message(request, messages.WARNING, _("Site is down for maintenance."))
                messages.add_message(request, messages.INFO, message)
                logout(request)
                return render(request, 'maintenance.html', { 'message': message })
        response = get_response(request)
        return response

    return middleware
