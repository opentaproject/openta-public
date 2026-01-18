# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings
import sys


def dprint(s, *args):
    if settings.SHOW_TIMING:
        caller = sys._getframe().f_back.f_code.co_name
        print(f" {s}                                {caller} ")
    return
