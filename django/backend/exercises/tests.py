from django.test import TestCase, LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random


class CourseListTest(TestCase):
    def setUp(self):
        self.selenium = webdriver.Firefox()
        self.selenium.implicitly_wait(0)
        super().setUp()

    def tearDown(self):
        self.selenium.quit()
        super().tearDown()

    def login(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 0)
        sel.get("http://localhost:8000")
        username = sel.find_element_by_css_selector('input[id=id_username]')
        password = sel.find_element_by_css_selector('input[id=id_password]')
        login = sel.find_element_by_css_selector('input[type=submit]')
        username.send_keys("student")
        password.send_keys('learning')
        login.click()
        wait.until(EC.text_to_be_present_in_element((By.ID, 'app'), "student"))
        assert "student" in sel.page_source

    def random_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 0)
        exercises = sel.find_elements_by_css_selector('li.course-exercise-item')
        exercise = random.choice(exercises)
        exercise.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.uk-article-title')))

    def back_to_course(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 0)
        back = sel.find_element_by_css_selector('ul.exercise-menu > li.uk-nav-header > a')
        back.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))

    def test_one(self):
        self.login()
        self.random_exercise()
        self.back_to_course()
        self.random_exercise()
        self.back_to_course()
