# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from course.export_import import export_server

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("export_path", type=str)

    def handle(self, *args, **kwargs):
        """Export full server."""
        for task_result in export_server(kwargs["export_path"]):
            LOGGER.info("%s: %d %%", task_result.status, int(task_result.progress * 100))
