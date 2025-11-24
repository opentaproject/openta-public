# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import django

if django.VERSION < (3, 2):
    default_app_config = "hijack.apps.HijackConfig"
