# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings
import collections
import logging
import os
from unittest.mock import patch
from django.utils import timezone
import time

import pytest
import datetime
from backend.selenium_utils.utils import OpenTAStaticLiveServerTestCase
from django.conf import settings
from exercises.models import Exercise
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOGGER.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class MacrosTest(OpenTAStaticLiveServerTestCase):
    databases = {"default", "openta"}

    def setUp(self):
        dirname = os.path.dirname(os.path.abspath(__file__)) + "/testdir"
        logger.error("DIRLIST = %s " % os.listdir( dirname) )
        super().setUp(dirname)

    def change_exercise_options(self, exercise):
        exercise.meta.published = True
        exercise.meta.required = True
        exercise.meta.feedback = True
        exercise.meta.feedback = True
        exercise.meta.image = False
        exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
        exercise.meta.save()
        # super().change_exercise_options(exercise)

    @patch("exercises.question.get_seed")
    def test_1_symbolic_with_hints_and_macros(self, get_seed=None):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        logger.error("TEST_1")
        sel = self.selenium
        wait = WebDriverWait(sel, 200000 )
        logger.error("OPEN SITE")
        self.open_site()
        logger.error("CHANGE EXERCISE OPTIONS")
        exercises = Exercise.objects.all()
        logger.error("EXERCISES = %s " % exercises )
        answerdicts = {}
        answerdicts["levela"] = collections.OrderedDict(
            [("1", "-6 i  -2 j - 11 k "), ("2", "[-6,-2,-11]"), ("3", " sqrt( 23/30 )")]
        )

        answerdicts["level0-42146"] = collections.OrderedDict(
            [("1", "[-6,-2,-11]"), ("2", "-6 i - 2 j - 11 k "), ("3", "sqrt( 23/30 )")]
        )

        answerdicts["antiderivative"] = collections.OrderedDict(
            [("5", "1/3 x^3 + x^2 + x ")  ]
        )
        get_seed.return_value = "45801"

        for exercise in exercises:
            self.change_exercise_options(exercise)


        for exercise in exercises:
            logger.error("NOW DO EXERCISE_PATH: %s", exercise.path)
            self.login(username="student1", pw="pw", assert_role="student")
            logger.error("WAIT FOR li.course-exercise-item")
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li.course-exercise-item")))
            logger.error("NOW CLICK EXERCISE")
            self.click_exercise(exercise)
            [tot, yescorrects, unchecked, nocorrects, syntaxerrors] = self.answerall( exercise, answerdicts[exercise.path])
            logger.error("TRIPLE1 = %s", [tot, yescorrects, unchecked, nocorrects, syntaxerrors])
            logger.error("LOGOUT")
            self.logout()

