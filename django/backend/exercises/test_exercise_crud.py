from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from tempfile import TemporaryDirectory
import os

import exercises.paths as paths
from exercises.setup_tests import create_exercise, create_database
from .models import Exercise
from course.models import Course
from .parsing import exercise_delete


class ExerciseCrudTest(StaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        self.dir = TemporaryDirectory()
        paths.EXERCISES_PATH = self.dir.name

    def tearDown(self):
        super().tearDown()

    def test_add(self):
        course = Course.objects.first()
        create_exercise(course, self.dir.name, 'exercise1')
        for msg in Exercise.objects.sync_with_disc(course=course, i_am_sure=True):
            print(msg)

    def test_delete(self):
        course = Course.objects.first()
        exercise_path = create_exercise(course, self.dir.name, 'exercise1')
        for msg in Exercise.objects.sync_with_disc(course=course, i_am_sure=True):
            print(msg)
        exercise_delete(course.get_exercises_path(), exercise_path)
        trashed_exercises = os.listdir(
            os.path.join(self.dir.name, course.get_exercises_folder(), paths.TRASH_PATH)
        )
        self.assertIn("exercise1", trashed_exercises[0])
