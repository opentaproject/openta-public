# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from backend.selenium_utils.utils import OpenTAStaticLiveServerTestCase
from django.conf import settings
from tempfile import TemporaryDirectory
import os

import exercises.paths as paths
from backend.selenium_utils.utils import create_exercise, create_database
from exercises.models import Exercise
from course.models import Course
from exercises.parsing import exercise_delete
import logging
import pytest

logger = logging.getLogger(__name__)

# FIXME: this test does not appear to do anything with Selenium. Should it be rewritten?
# Check with Hampus what the point of this is


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class ExerciseCrudTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        create_database()
        self.dir = TemporaryDirectory()
        self.dirname = f"{settings.VOLUME}/openta"
        super().setUp()
        # paths.EXERCISES_PATH = self.dirname

    def tearDown(self):
        super().tearDown()

    def test_add(self):
        course = Course.objects.first()
        create_exercise(course, self.dirname, "exercise1")
        for msg in Exercise.objects.sync_with_disc(course=course, i_am_sure=True):
            logger.debug(msg)

    def test_delete(self):
        course = Course.objects.first()
        exercise_path = create_exercise(course, self.dirname, "exercise1")
        for msg in Exercise.objects.sync_with_disc(course=course, i_am_sure=True):
            logger.debug(msg)
        exercise_delete(
            course.get_exercises_path(),
            os.path.join(course.get_exercises_path(), exercise_path),
        )
        trashed_exercises = os.listdir(
            os.path.join(
                self.dirname,
                "exercises",
                course.get_exercises_folder(),
                paths.TRASH_PATH,
            )
        )
        logger.debug("TRASHED = %s", trashed_exercises)
        self.assertIn("exercise1", trashed_exercises[0])
