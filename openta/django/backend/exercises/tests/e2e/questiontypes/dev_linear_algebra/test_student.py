# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import collections
import datetime
import logging
import os

import pytest
from exercises.models import Exercise
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from backend.selenium_utils.utils import OpenTAStaticLiveServerTestCase
from django.utils import timezone

logger = logging.getLogger(__name__)

LOGGER.setLevel(logging.WARNING)


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class DevLinearAlgebraTest(OpenTAStaticLiveServerTestCase):
    databases = {"default", "openta"}

    def setUp(self):
        dirname = os.path.dirname(os.path.abspath(__file__)) + "/testdir"
        print("DIRLIST = %s " % os.listdir(dirname))
        super().setUp(dirname)

    def change_exercise_options(self, exercise):
        exercise.meta.published = True
        exercise.meta.required = True
        # exercise.meta.student_assets = True
        exercise.meta.feedback = False
        exercise.meta.image = True
        exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
        exercise.meta.save()

    @pytest.mark.django_db(databases=["default", "openta"])
    def test_1_dev_linear_algebra(self):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        wait = WebDriverWait(self.selenium, 20000)
        print("OPEN SITE")
        self.open_site()
        print("CHANGE EXERCISE OPTIONS")
        # print(f"{settings.DATABASES}")
        exercises = Exercise.objects.using("default").all()
        print("EXERCISES = %s " % exercises)
        answerdicts = {}
        answerdicts["exercise1"] = collections.OrderedDict([("1", "sqrt(a^2 +  b^2)")])
        for exercise in exercises:
            self.change_exercise_options(exercise)
        for exercise in exercises:
            print("DO EXERCISE in TEST_ADMIN ")
            self.change_exercise_options(exercise)
            self.login(username="student1", pw="pw", assert_role="student")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
            self.click_exercise(exercise)
            exercise.exercise_key

            logger.error(f"EXERCISE PATH = {exercise.path}")
            logger.error("ANSWER FIRST EXERCISE")
            logger.error(f"ANSWERDICTS = {answerdicts}")
            [tot, yescorrects, unchecked, nocorrects, syntaxerrors] = self.answerall(
                exercise, answerdicts[exercise.path]
            )
            print("TRIPLE1 = %s", [tot, yescorrects, unchecked, nocorrects, syntaxerrors])
            print("LOGOUT")
            self.logout()
