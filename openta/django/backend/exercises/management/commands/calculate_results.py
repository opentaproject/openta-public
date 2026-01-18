# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.management.base import BaseCommand, CommandError
from backend.middleware import verify_or_create_database_connection
from exercises.aggregation import student_statistics_exercises, students_results
import logging
from django.conf import settings

from course.models import Course
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Calculates results and statistics and stores to cache"

    def add_arguments(self, parser):
        parser.add_argument("subdomain", nargs="+", type=str)

    def handle(self, *args, **options):
        subdomain = options["subdomain"][0]
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        print("SUBDOMAIN = %s " % subdomain)
        verify_or_create_database_connection(subdomain)

        for course in Course.objects.all():
            if True or course.published:
                published = course.published
                course.published = True
                logger.info("Calculating for course {}".format(course.course_name))
                student_statistics_exercises(force=True, course=course)
                logger.info("Statistics done, now doing results.")
                students_results(force=True, course=course)
                logger.info("Finished calculating results and statistics")
                course.published = published
            else:
                logger.info("Skip calculating results for unpublished course {}".format(course.course_name))
