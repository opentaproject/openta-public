# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from users.models import OpenTAUser
from django import forms
from django.conf import settings


class OpenTAUserForm(forms.ModelForm):
    class Meta:
        model = OpenTAUser
        exclude = ["courses"]
