from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from tempfile import TemporaryDirectory
import os
import logging
import datetime
import exercises.paths as paths
from exercises.setup_tests import create_exercise, create_database
from exercises.models import Exercise
from course.models import Course
from django.utils import timezone
from django.conf import settings

LOGGER.setLevel(logging.WARNING)

EXERCISE_CODE = """
                <exercise>
                <exercisename>MC test</exercisename>
                <question type="multipleChoice" key="0">
                <text>Pick the correct alternatives below.</text>
                <choice key="0">c1</choice>
                <choice key="1" correct="true">c2</choice>
                <choice key="2">c3</choice>
                <choice key="3" correct="true">c4</choice>
                </question>
                </exercise>
                """


class MCTest(StaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, 'exercise1', content=EXERCISE_CODE)
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            print(msg)
        self.selenium = webdriver.Chrome()
        self.selenium.implicitly_wait(0)

    def tearDown(self):
        self.selenium.quit()
        super().tearDown()

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
        wait = WebDriverWait(sel, 2000)
        input_username = sel.find_element_by_css_selector('input[id=id_username]')
        input_password = sel.find_element_by_css_selector('input[id=id_password]')
        login = sel.find_element_by_css_selector('input[type=submit]')
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        wait.until(EC.text_to_be_present_in_element((By.ID, 'app'), assert_role))
        assert assert_role in sel.page_source

    def logout(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        sel.find_element_by_xpath('//a[contains(@href,\'logout\')]').click()
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//form[contains(@action, \'login\')]'))
        )

    def first_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        exercises = sel.find_elements_by_css_selector('li.course-exercise-item')
        exercise = exercises[0]
        exercise.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.uk-article-title')))

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 1000)
        sel.find_element_by_xpath(
            '//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c1\')]'
        ).click()
        sel.find_element_by_xpath('//a//i[contains(@class, \'uk-icon-send\')]').click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "Not correct"))

        sel.find_element_by_xpath(
            '//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c1\')]'
        ).click()
        sel.find_element_by_xpath(
            '//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c2\')]'
        ).click()
        sel.find_element_by_xpath(
            '//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c4\')]'
        ).click()
        sel.find_element_by_xpath('//a//i[contains(@class, \'uk-icon-send\')]').click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "Correct"))
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//i[contains(@class, \'uk-icon-check\')]'))
        )

    def test_1_multiple_choice(self):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer()
        self.logout()
