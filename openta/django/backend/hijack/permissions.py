# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

def superusers_only(*, hijacker, hijacked):
    """Superusers may hijack any other user."""
    return hijacked.is_active and hijacker.is_superuser


def superusers_and_staff(*, hijacker, hijacked):
    """
    Superusers and staff members may hijack other users.

    A superuser may hijack any other user.
    A staff member may hijack any user, except another staff member or superuser.
    """
    if not hijacked.is_active:
        return False

    if hijacker.is_superuser:
        return True

    return hijacker.is_staff and not (hijacked.is_staff or hijacked.is_superuser)
