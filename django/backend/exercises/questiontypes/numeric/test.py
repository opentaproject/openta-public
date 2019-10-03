from utils import OpenTAStaticLiveServerTestCase
import logging
import datetime
import time
from tempfile import TemporaryDirectory

from selenium import webdriver
from selenium.webdriver.common.by import By
from backend.selenium_utils import create_selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from django.utils import timezone

import exercises.paths as paths
from exercises.setup_tests import create_exercise, create_database
from backend.selenium_utils import create_selenium

from exercises.models import Exercise
from course.models import Course

LOGGER.setLevel(logging.WARNING)

CORRECT_VALUE = 0.314159
PRECISION = 0.001

NUMERIC_EXERCISE_XML = """
                <exercise>\n
                <exercisename>Numeric test </exercisename>\n
                <text>Test exercise text</text>\n
                <question type="Numeric" key="1" precision="0.001">\n
                <text>compareNumeric</text>\n
                <expression>0.314159</expression>\n
                </question>\n
                </exercise>\n
                """

class NumericTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        self.dir = TemporaryDirectory()
        course = Course.objects.first()
        create_exercise(course, self.dir.name, 'exercise1', content=NUMERIC_EXERCISE_XML)
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, True):
            print(msg)
        self.selenium = create_selenium()
        self.selenium.implicitly_wait(0)

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
        wait = WebDriverWait(sel, 2)
        input_username = sel.find_element_by_css_selector('input[id=id_username]')
        input_password = sel.find_element_by_css_selector('input[id=id_password]')
        login = sel.find_element_by_css_selector('input[type=submit]')
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))
        assert assert_role in sel.page_source

    def first_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        exercises = sel.find_elements_by_css_selector('li.course-exercise-item')
        exercise = exercises[0]
        exercise.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.uk-article-title')))

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        input_box = sel.find_elements_by_css_selector('textarea')[0]
        input_box.send_keys(str(CORRECT_VALUE * (1 + PRECISION * 0.99)))
        send_button = sel.find_elements_by_xpath('//a[.//i[contains(@class, \'uk-icon-send\')]]')[0]
        send_button.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "is correct"))

    def answer_incorrect(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        input_box = sel.find_elements_by_css_selector('textarea')[0]
        input_box.send_keys(str(CORRECT_VALUE * (1 + PRECISION * 1.01)))
        send_button = sel.find_elements_by_xpath('//a[.//i[contains(@class, \'uk-icon-send\')]]')[0]
        send_button.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "incorrect"))

    def test_1_student_answer(self):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer()

    def test_1_student_answer_incorrect(self):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer_incorrect()