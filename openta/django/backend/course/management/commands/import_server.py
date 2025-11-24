# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from course.export_import import import_server


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("import_path", type=str)
        parser.add_argument("--merge", action="store_true", default=False)

    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        import_server(kwargs["import_path"], merge=kwargs["merge"])
