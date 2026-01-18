# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Test export and import functionality"""
import pytest
from django.test import TestCase
from django.contrib.auth.models import User, Group
import datetime
from django.utils import timezone
import tempfile
import zipfile
import os
import shutil
import logging

from exercises.models import Exercise
import exercises.paths as paths
from exercises.tests.test_utils import create_course, create_question, set_meta
from backend.selenium_utils.utils import (
    create_user,
    create_exercise,
    DEFAULT_EXERCISE_TEMPLATE,
    DEFAULT_EXERCISE_NAME,
    DEFAULT_EXERCISE,
)

from course.export_import import (
    export_course_exercises,
    import_course_exercises,
    export_server,
    import_server,
)
from course.export_import import SERVER_EXPORT_FILENAME

logger = logging.getLogger(__name__)

DEADLINE_HOUR = 8
DEADLINE_MINUTE = 0
DEADLINE_SECOND = 0
DEADLINE = timezone.make_aware(
    datetime.datetime(
        year=2005,
        month=5,
        day=1,
        hour=DEADLINE_HOUR,
        minute=DEADLINE_MINUTE,
        second=DEADLINE_SECOND,
    )
)

# TODO
# The current calculate_students_results require an image uploaded for all required
# and bonus exercises to count correct/deadline/image_deadline


class BasicCourse(TestCase):
    databases = "__all__"
    """Basic course test case.

    - 1 course
    - 1 student
    - 1 exercise with 1 question

    """

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        logger.debug("SETUP EXERCISE PATH %s ", paths.EXERCISES_PATH)

        # Create course
        self._course = create_course("A course", datetime.time(DEADLINE_HOUR, DEADLINE_MINUTE, DEADLINE_SECOND))

        # Create student group
        student_group = Group(name="Student")
        student_group.save()

        # Create student and add to group
        self._student = create_user("student1", "student@test.se", "pw1", self._course)
        student_group.user_set.add(self._student)

    def test_export_course_exercises(self):
        """Test export course exercises."""
        # Create exercise
        directory = self._dir.name
        create_exercise(course=self._course, directory=directory, name="r1")
        for msg in Exercise.objects.sync_with_disc(course=self._course, i_am_sure=True):
            pass
        self._exercise = Exercise.objects.first()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_filename = None
            for filename, _ in export_course_exercises(self._course, tmpdir):
                logger.info("FILENAME = %s " % filename)
                output_filename = filename
            logger.info("OUTPUT FILENAME = %s " % output_filename)
            zip_file = zipfile.ZipFile(output_filename)
            self.assertIn("r1/exercise.xml", zip_file.namelist())
            self.assertFalse( "r1/exercisekey" in  zip_file.namelist()) # Make sure exercisekey is no longer exported for exercises_export

    def test_import_course_exercises(self):
        """Test export course exercises."""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            zip_file = zipfile.ZipFile(tmpfile, "w")
            zip_file.writestr("e1/exercise.xml", data=DEFAULT_EXERCISE)
            zip_file.close()

            import_course_exercises(self._course, tmpfile)
            self.assertTrue(Exercise.objects.filter(name=DEFAULT_EXERCISE_NAME).exists())

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_server_export(self):
        """Test server export."""

        # Create exercise
        create_exercise(course=self._course, directory=paths.EXERCISES_PATH, name="r1")
        for msg in Exercise.objects.sync_with_disc(course=self._course, i_am_sure=True):
            pass
        self._exercise = Exercise.objects.first()

        with tempfile.TemporaryDirectory() as tmpdir:
            for _ in export_server(tmpdir):
                pass
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, SERVER_EXPORT_FILENAME)))

    @pytest.mark.skip(reason="TODO test_server test not update")
    def test_server_import(self):
        """Test server import."""

        # Create exercise
        logger.debug(f"paths.EXERCISES_PATH = {paths.EXERCISES_PATH}")
        create_exercise(
            course=self._course,
            directory=paths.EXERCISES_PATH,
            name="r1",
            content=DEFAULT_EXERCISE_TEMPLATE.format(name="r1"),
        )
        for _ in Exercise.objects.sync_with_disc(course=self._course, i_am_sure=True):
            pass
        self._exercise = Exercise.objects.first()
        self._exercise.meta.published = True
        self._exercise.meta.save()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Export server
            for _ in export_server(tmpdir):
                pass
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, SERVER_EXPORT_FILENAME)))

            # Remove exercises from disk
            shutil.rmtree(paths.EXERCISES_PATH)
            os.makedirs(paths.EXERCISES_PATH)

            # Remove exercises from database
            Exercise.objects.all().delete()

            # Import server
            for _ in import_server(os.path.join(tmpdir, SERVER_EXPORT_FILENAME)):
                pass

            # Verify exercise
            exercise = Exercise.objects.first()
            self.assertTrue(exercise.meta.published)
            self.assertEqual(exercise.name, "r1")
