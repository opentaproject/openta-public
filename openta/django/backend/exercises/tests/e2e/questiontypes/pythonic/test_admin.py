# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings

import collections
import datetime
import logging
import os

import pytest
from backend.selenium_utils.utils import OpenTAStaticLiveServerTestCase
from django.utils import timezone
from exercises.models import Exercise
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOGGER.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class PythonicTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        dirname = os.path.dirname(os.path.abspath(__file__)) + "/testdir"
        logger.error(f"DIRNAME = {dirname}")
        super().setUp(dirname=dirname)

    def change_exercise_options(self, exercise):
        exercise.meta.published = True
        exercise.meta.required = True
        exercise.meta.student_assets = True
        exercise.meta.image = True
        exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
        exercise.meta.save()


    def test_1_pythonic(self):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        logger.error("OPEN SITE")
        self.open_site()
        logger.error("CHANGE EXERCISE OPTIONS")
        exercises = Exercise.objects.all()
        answerdicts = {}
        answerdicts["pythonic"] = collections.OrderedDict(
            [("3", "sqrt(a^2 +  b^2)"), ("4", "[[1,0],[0,1]]"), ("5", "[[0,0],[0,0]]")]
        )
        answerdicts["standard"] = collections.OrderedDict([("0", "   sqrt(  a * a  +  b *   b )  ")])
        answerdicts["standard2"] = collections.OrderedDict([("0", "   sqrt(  a * a  +  b *   b )  ")])

        for exercise in exercises:
            self.change_exercise_options(exercise)

        for exercise in exercises:
            logger.error("DO EXERCISE in TEST_ADMIN ")
            self.login(username="admin3", pw="pw", assert_role="admin")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
            self.click_exercise(exercise)
            exercise.exercise_key

            logger.error(f"EXERCISE PATH = {exercise.path}")
            logger.error("ANSWER FIRST EXERCISE")
            logger.error(f"ANSWERDICTS = {answerdicts}")
            [tot, yescorrects, unchecked, nocorrects, syntaxerrors] = self.answerall(
                exercise, answerdicts[exercise.path]
            )
            logger.error("TRIPLE1 = %s", [tot, yescorrects, unchecked, nocorrects, syntaxerrors])
            logger.error("LOGOUT")
            self.logout()
