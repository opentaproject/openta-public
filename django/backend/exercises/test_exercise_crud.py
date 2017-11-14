from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from tempfile import TemporaryDirectory
import os

import exercises.paths as paths
from exercises.setup_tests import create_exercise, create_database
from .models import Exercise
from .parsing import exercise_delete


class ExerciseCrudTest(StaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        self.dir = TemporaryDirectory()
        paths.EXERCISES_PATH = self.dir.name

    def test_add(self):
        create_exercise(self.dir, 'exercise1')
        for msg in Exercise.objects.sync_with_disc(True):
            print(msg)

    def test_delete(self):
        exercise_path = create_exercise(self.dir, 'exercise1')
        for msg in Exercise.objects.sync_with_disc(True):
            print(msg)
        exercise_delete(exercise_path)
        trashed_exercises = os.listdir(os.path.join(self.dir.name, paths.TRASH_PATH))
        self.assertIn("exercise1", trashed_exercises[0])
