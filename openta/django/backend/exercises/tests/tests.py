# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from backend.selenium_utils.utils import OpenTAStaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from tempfile import TemporaryDirectory
from backend.selenium_utils import create_selenium
import random
import exercises.paths as paths
from backend.selenium_utils.utils import create_exercise, create_database
from exercises.models import Exercise
from course.models import Course
from django.conf import settings
import pytest
import logging

logger = logging.getLogger(__name__)

LOGGER.setLevel(logging.WARNING)


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class CourseListTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, "exercise1")
        paths.EXERCISES_PATH = self.dir.name
        Exercise.objects.add_exercise("/exercise1", course=course)
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            logger.debug(msg)

    def change_exercise_options(self):
        exercise = Exercise.objects.all()[0]
        exercise.meta.published = True
        exercise.meta.save()

    # def login(self):
    #    sel = self.selenium
    #    wait = WebDriverWait(sel, 100)
    #    sel.get(self.live_server_url)
    #    username = sel.find_element(By.CSS_SELECTOR,'input[id=id_username]')
    #    password = sel.find_element(By.CSS_SELECTOR,'input[id=id_password]')
    #    login = sel.find_element(By.CSS_SELECTOR,'input[type=submit]')
    #    username.send_keys("student1")
    #    password.send_keys('pw')
    #    login.click()
    #    wait.until(EC.text_to_be_present_in_element((By.ID, 'app'), "student"))
    #    assert "student" in sel.page_source

    def random_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 20000)
        print(f"WAIT1")
        exercises = sel.find_elements(By.CSS_SELECTOR, "li.course-exercise-item")
        exercise = random.choice(exercises)
        self.click_exercise(exercise)
        print(f"WAIT2")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.uk-article-title")))
        print(f"WAIT3")

    def back_to_course(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000)
        print(f"WAIT4")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[class*='onHome']")) )
        print(f"WAIT5")
        back = sel.find_element(By.CSS_SELECTOR, "button[class*='onHome']")
        back.click()
        print(f"WAIT6")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))

    def test_one(self):
        """
        Publish an exercise and verify that students can see and enter exercise.
        """
        self.open_site()
        self.change_exercise_options()
        self.login("student1", "pw", "student")
        self.random_exercise()
        self.back_to_course()
        self.random_exercise()
        self.back_to_course()
