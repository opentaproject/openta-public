# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings
import datetime
import logging
from tempfile import TemporaryDirectory

import pytest
from backend.selenium_utils import create_selenium
from backend.selenium_utils.utils import OpenTAStaticLiveServerTestCase, create_database, create_exercise
from course.models import Course
from django.utils import timezone
from exercises.models import Exercise
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

LOGGER.setLevel(logging.WARNING)

EXERCISE_CODE = """
                <exercise>
                <exercisename>MC test</exercisename>
                <question type="multipleChoice" key="0">
                <text>Pick the correct alternatives below.</text>
                <choice key="0"><text>c1</text></choice>
                <choice key="1" correct="true"><text>c2</text></choice>
                <choice key="2"><text>c3</text></choice>
                <choice key="3" correct="true"><text>c4</text></choice>
                </question>
                </exercise>
                """


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class MCTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, "exercise1", content=EXERCISE_CODE)
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            logger.debug(msg)

    def change_exercise_options(self):
        exercise = Exercise.objects.all()[0]
        exercise.meta.published = True
        exercise.meta.required = True
        exercise.meta.image = True
        exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
        exercise.meta.save()

    def open_site(self):
        sel = self.selenium
        sel.get(self.live_server_url)

    def login(self, username="student1", pw="pw", assert_role="student"):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        logger.debug("NOW WAIT FOR OpenHeader TO COME UP")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "OpenHeader")))
        logger.debug("NOW WAIT FOR TEST MC TO COME UP")
        # sel.find_element_by_class_name("OpenHeader").click()
        # wait.until(EC.text_to_be_present_in_element((By.ID, "app"), assert_role))
        assert assert_role in sel.page_source

    def logout(self):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        sel.find_element(By.XPATH, "//a[contains(@href,'logout')]").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//form[contains(@action, 'login')]")))

    def first_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
        exercises = sel.find_elements(By.CSS_SELECTOR, "li.course-exercise-item")
        exercise = exercises[0]
        self.click_exercise(exercise)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.uk-article-title")))

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 1000)
        sel.find_element(By.XPATH, "//div[contains(@class, 'mc-item')]//span[contains(text(), 'c1')]").click()
        sel.find_element(By.XPATH, "//a//i[contains(@class, 'uk-icon-send')]").click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "form"), "Not correct"))

        sel.find_element(By.XPATH, "//div[contains(@class, 'mc-item')]//span[contains(text(), 'c1')]").click()
        sel.find_element(By.XPATH, "//div[contains(@class, 'mc-item')]//span[contains(text(), 'c2')]").click()
        sel.find_element(By.XPATH, "//div[contains(@class, 'mc-item')]//span[contains(text(), 'c4')]").click()
        sel.find_element(By.XPATH, "//a//i[contains(@class, 'uk-icon-send')]").click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "form"), "Correct"))
        wait.until(EC.presence_of_element_located((By.XPATH, "//i[contains(@class, 'uk-icon-check')]")))

    def test_1_multiple_choice(self):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer()
        self.logout()
