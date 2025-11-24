# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from course.export_import import import_course_exercises
from course.models import Course


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("course_pk", type=str)
        parser.add_argument("--zip-path", type=str)

    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        course = Course.objects.get(pk=kwargs["course_pk"])
        import_course_exercises(course, kwargs["zip_path"])
