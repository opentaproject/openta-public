# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
import logging
from tempfile import TemporaryDirectory
from django.conf import settings

import pytest
from backend.selenium_utils.utils import (
    OpenTAStaticLiveServerTestCase,
    create_database,
    create_exercise,
    create_selenium,
)
from course.models import Course
from django.utils import timezone
from exercises.models import Exercise
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

LOGGER.setLevel(logging.WARNING)

CORRECT_VALUE = 3.14159
PRECISION = 0.01

NUMERIC_EXERCISE_XML = """
                <exercise>\n
                <exercisename>Numeric test </exercisename>\n
                <text>Test exercise text</text>\n
                <question type="Numeric" key="1" precision=".01">\n
                <text>compareNumeric</text>\n
                <expression>3.14159</expression>\n
                </question>\n
                </exercise>\n
                """


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class NumericTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        self.dir = TemporaryDirectory()
        course = Course.objects.first()
        create_exercise(course, self.dir.name, "exercise1", content=NUMERIC_EXERCISE_XML)
        # paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, True):
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
        input_username.clear()
        input_password.clear()
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
        assert assert_role in sel.page_source

    def first_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.WAIT)
        exercises = sel.find_elements(By.CSS_SELECTOR, "li.course-exercise-item")
        exercise = exercises[0]
        self.click_exercise(exercise)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.uk-article-title")))

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200 * settings.LONG_WAIT)
        print(f"WAIT1")
        input_box = sel.find_elements(By.CSS_SELECTOR, "textarea")[0]
        print(f"WAIT2")
        #input_box = wait.until( EC.visibility_of_element_located( (By.CSS_SELECTOR, "textarea")))
        input_box = wait.until( EC.visibility_of_element_located( (By.CSS_SELECTOR, "textarea.uk-textarea[qkey]")))
        print(f"WAIT3")
        okvalue = str( CORRECT_VALUE + PRECISION * 0.99 )
        print(f"OKVALUE = {okvalue}")
        input_box.clear()
        input_box.send_keys(okvalue) 
        sendbutton = sel.find_element(By.XPATH, "//i[contains(@class, 'sendicon')]")
        sendbutton.click()
        logger.error("WAITING FOR IS CORRECT1")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "yescorrect")))
        logger.error("WAIT FOR TEXTAREA")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea")))
        #input_box = sel.find_elements(By.CSS_SELECTOR, "textarea")[0]
        #input_box = wait.until( EC.visibility_of_element_located( (By.CSS_SELECTOR, "textarea")))
        input_box = wait.until( EC.visibility_of_element_located( (By.CSS_SELECTOR, "textarea.uk-textarea[qkey]")))
        print(f"INPUT_BOX = {input_box}")
        okvalue = str( CORRECT_VALUE + PRECISION * 1.01 )
        print(f"OKVALUE = {okvalue}")
        input_box.clear()
        input_box.send_keys(okvalue) 
        wait.until(EC.presence_of_element_located((By.XPATH, "//i[contains(@class, 'sendicon')]")))
        sendbutton = sel.find_element(By.XPATH, "//i[contains(@class, 'sendicon')]")
        sendbutton.click()
        logger.error("WAITING FOR IS NOCORRECT")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nocorrect")))
        # wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "form"), "is correct"))


    def noanswer_incorrect(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200 * settings.LONG_WAIT)
        input_box = sel.find_elements(By.CSS_SELECTOR, "textarea")[0]
        input_box.clear()
        okvalue = str( CORRECT_VALUE + PRECISION * 0.99 )
        print(f"OKVALUE = {okvalue}")
        input_box.send_keys(okvalue) 
        sendbutton = sel.find_element(By.XPATH, "//i[contains(@class, 'sendicon')]")
        sendbutton.click()
        logger.error("WAITING FOR IS CORRECT1")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "yescorrect")))
        logger.error("GOT YESCORRET")
        input_box = sel.find_elements(By.CSS_SELECTOR, "textarea")[0]
        input_box.clear()
        okvalue = str( CORRECT_VALUE + PRECISION * 0.99 )
        print(f"OKVALUE = {okvalue}")
        input_box.send_keys(okvalue) 
        sendbutton = sel.find_element(By.XPATH, "//i[contains(@class, 'sendicon')]")
        sendbutton.click()
        logger.error("WAITING FOR IS CORRECT1")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "yescorrect")))
        logger.error("GOT YESCORRET")

        # wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "form"), "is correct"))



    def test_1_student_answer(self):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        logger.debug("TEST_1 ANSWSER CORRECT")
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer()

    def notest_1_student_answer_incorrect(self):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        logger.debug("TEST_1 ANSWSER INCORRECT")
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer_incorrect()
