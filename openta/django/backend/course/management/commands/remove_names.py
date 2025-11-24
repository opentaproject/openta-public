# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        n_affected = User.objects.update(first_name="", last_name="")
        logging.info("Removed %d names", n_affected)
