# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings as django_settings

__all__ = ["settings"]


class LazySettings:
    HIJACK_PERMISSION_CHECK = "hijack.permissions.superusers_only"
    HIJACK_INSERT_BEFORE = "</body>"

    def __getattribute__(self, name):
        try:
            return getattr(django_settings, name)
        except AttributeError:
            return super().__getattribute__(name)


settings = LazySettings()
