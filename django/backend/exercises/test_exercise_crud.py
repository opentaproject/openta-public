from django.test import TestCase, LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from tempfile import TemporaryDirectory
import time
import random
import os
import logging
import datetime

import exercises.paths as paths
from exercises.setup_tests import create_exercise, create_database
from .models import Exercise, ExerciseMeta, Question, Answer, ImageAnswer, AuditExercise
from .parsing import exercise_delete


class ExerciseCrudTest(StaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        self.dir = TemporaryDirectory()
        paths.EXERCISES_PATH = self.dir.name

    def test_add(self):
        exercise_path = create_exercise(self.dir, 'exercise1')
        for msg in Exercise.objects.sync_with_disc(True):
            print(msg)

    def test_delete(self):
        exercise_path = create_exercise(self.dir, 'exercise1')
        for msg in Exercise.objects.sync_with_disc(True):
            print(msg)
        exercise_delete(exercise_path)
        trashed_exercises = os.listdir(os.path.join(self.dir.name, paths.TRASH_PATH))
        self.assertIn("exercise1", trashed_exercises[0])
