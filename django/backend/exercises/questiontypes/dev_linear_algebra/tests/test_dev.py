from utils import OpenTAStaticLiveServerTestCase
from selenium import webdriver
from backend.selenium_utils import create_selenium
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

from ..linear_algebra import linear_algebra_compare_expressions
from ..linear_algebra import linear_algebra_check_if_true
from ..string_formatting import insert_implicit_multiply as iim
from ..string_formatting import ascii_to_sympy


LOGGER.setLevel(logging.WARNING)

# EXERCISE_CODE = """
#                <exercise>
#                <exercisename>MC test</exercisename>
#                <question type="multipleChoice" key="0" showerrors='True'>
#                <text>Pick the correct alternatives below.</text>
#                <choice key="0">c1</choice>
#                <choice key="1" correct="true">c2</choice>
#                <choice key="2">c3</choice>
#                <choice key="3" correct="true">c4</choice>
#                </question>
#                </exercise>
#                """
EXERCISE_CODE = """
    <exercise>
    <exercisename key="27">DevLinearAlgebraTest </exercisename>
    <global> a = 1;  b = 2;  c = 3; 
        <var><token>a</token><tex>A</tex></var> 
    </global>
    <text> Pythagoras test </text>
    <question key='1' exposeglobals='True' type='devLinearAlgebra'>
         <blacklist><token>c</token></blacklist>
         <variables> <var><token>d</token><tex>DD</tex><value>9 </value> </var></variables>
         <text>test pythagoras</text>
         <expression> sqrt(a^2 + b^2) </expression>
    </question>
    </exercise>
    """


class SecondDevLinearAlgebraTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, 'exercise1', content=EXERCISE_CODE)
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            print(msg)
        self.selenium = create_selenium()
        self.selenium.implicitly_wait(0)

    def tearDown(self):
        self.selenium.quit()
        super().tearDown()

    def change_exercise_options(self):
        exercise = Exercise.objects.all()[0]
        exercise.meta.published = True
        # exercise.meta.required = True
        # exercise.meta.image = True
        # exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
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
        wait = WebDriverWait(sel, 200)
        # elements = sel.find_elements_by_css_selector('li')
        elements = sel.find_elements_by_xpath('//button')
        for element in elements:
            print("exercise elements = ", element.text)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))
        exercises = sel.find_elements_by_css_selector('li.course-exercise-item')
        # print("exercises = ", exercises)
        exercise = exercises[0]
        exercise.click()
        print("exercise = ", exercise)
        # elements  = sel.find_elements_by_css_selector('li')
        # print("elements = ", elements)
        # for element in elements :
        #    print("exercise elements = ", print( element ) )
        wait.until(EC.presence_of_element_located((By.XPATH, '//article')))
        print("ARTCILE APPEARED")

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200)
        print("NOW WAIT UNTIL TEXTAREA APPEARS")
        wait.until(EC.presence_of_element_located((By.XPATH, '//textarea')))
        print("A")
        answerarea = sel.find_element_by_xpath('//textarea')
        print("B")
        answerarea.send_keys('sqrt(a^2 + b^2 )')
        print("C")
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//i[contains(@class, \'uk-icon-send\')]'))
        )
        print("success")
        sendbutton = sel.find_element_by_xpath('//i[contains(@class, \'uk-icon-send\')]')
        WebDriverWait(sel, 10000)
        sendbutton.click()
        # sel.find_element_by_xpath('//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c1\')]').click()
        # sel.find_element_by_xpath('//a//i[contains(@class, \'uk-icon-send\')]').click()
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[contains(@class, \'uk-alert-success\')]')
            )
        )
        print("success")
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//span[contains(@class,\'termsof\')]'))
        )
        print("termsof found")
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//span[contains(@class,\'termsof\') and text()=\'a\']')
            )
        )
        print("termsof a  found")
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//span[contains(@class,\'termsof\') and text()=\'b\']')
            )
        )
        print("termsof b  found")
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//span[contains(@class,\'termsof\') and text()=\'d\']')
            )
        )
        print("termsof d  found")
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//span[contains(@class,\'mathit\') and text()=\'A\']')
            )
        )
        print("termsof a(A)  found")
        ays = sel.find_elements_by_xpath('//span[contains(@class,\'termsof\') and text()=\'a\']')
        print(" size of ays ", len(ays))
        assert len(ays) == 1
        cys = sel.find_elements_by_xpath('//span[contains(@class,\'termsof\') and text()=\'c\']')
        assert len(cys) == 0
        print("ALL OK")
        # sel.find_element_by_xpath('//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c2\')]').click()
        # sel.find_element_by_xpath('//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c4\')]').click()
        # sel.find_element_by_xpath('//a//i[contains(@class, \'uk-icon-send\')]').click()
        # wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, \'correct\')]')))
        # wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "Correct"))
        # wait.until(EC.presence_of_element_located((By.XPATH, '//i[contains(@class, \'uk-icon-check\')]')))
        # wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, \'uk-alert-danger\')]')))

    def test_1_dev_linear_algebra(self):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer()
        self.logout()
