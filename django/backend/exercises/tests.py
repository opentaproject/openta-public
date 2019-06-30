from utils import OpenTAStaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from tempfile import TemporaryDirectory
from backend.selenium_utils import create_selenium
import random
import logging
import exercises.paths as paths
from exercises.setup_tests import create_exercise, create_database
from .models import Exercise
from course.models import Course
from django.conf import settings

LOGGER.setLevel(logging.WARNING)


class CourseListTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, 'exercise1')
        paths.EXERCISES_PATH = self.dir.name
        Exercise.objects.add_exercise('/exercise1', course=course)
        self.selenium = create_selenium()
        self.selenium.implicitly_wait(10)

        super().setUp()

    def tearDown(self):
        self.selenium.quit()
        super().tearDown()

    def change_exercise_options(self):
        exercise = Exercise.objects.all()[0]
        exercise.meta.published = True
        exercise.meta.save()

    def login(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 100)
        sel.get(self.live_server_url)
        username = sel.find_element_by_css_selector('input[id=id_username]')
        password = sel.find_element_by_css_selector('input[id=id_password]')
        login = sel.find_element_by_css_selector('input[type=submit]')
        username.send_keys("student1")
        password.send_keys('pw')
        login.click()
        wait.until(EC.text_to_be_present_in_element((By.ID, 'app'), "student"))
        assert "student" in sel.page_source

    def random_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        exercises = sel.find_elements_by_css_selector('li.course-exercise-item')
        exercise = random.choice(exercises)
        exercise.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.uk-article-title')))

    def back_to_course(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        back = sel.find_element_by_css_selector('a.onHome')
        back.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))

    def test_one(self):
        '''
        Publish an exercise and verify that students can see and enter exercise.
        '''
        self.change_exercise_options()
        self.login()
        self.random_exercise()
        self.back_to_course()
        self.random_exercise()
        self.back_to_course()
