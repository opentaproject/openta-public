# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
import logging
from tempfile import TemporaryDirectory

import exercises.paths as paths
import pytest
from course.models import Course
from exercises.models import Exercise
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from backend.selenium_utils.utils import (
    OpenTAStaticLiveServerTestCase,
    create_database,
    create_exercise,
    create_selenium,
)
from django.conf import settings
from django.utils import timezone

LOGGER.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

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
    <global> a = 1;  b = 2;  c = 9 ;
    <var><token>a</token><tex>A</tex></var>
    </global>
    <text> Pythagoras test </text>
    <question key='1' exposeglobals='True' type='devLinearAlgebra'>
     <variables>
         <blacklist><token>c</token></blacklist>
         <var><token>d</token><tex>D</tex><value>9 </value> </var>
      </variables>
         <text>test pythagoras</text>
         <expression> d sqrt(a^2 + b^2) </expression>
    </question>
    </exercise>
    """


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class SecondDevLinearAlgebraTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, "exercise3", content=EXERCISE_CODE)
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            logger.error(msg)

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
        logger.error("NOW WAIT FOR OpenHeader TO COME UP")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "OpenHeader")))
        logger.error("NOW WAIT FOR APP TEST_DEV2.PY TO COME UP")
        sel.find_element(By.CLASS_NAME, "OpenHeader").click()
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        assert assert_role in sel.page_source

    def logout(self):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        sel.find_element(By.XPATH, "//a[contains(@href,'logout')]").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//form[contains(@action, 'login')]")))

    def first_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        wait.until(EC.presence_of_element_located((By.XPATH, '//a[@id="course-exercise-item-button"]')))
        exercises = sel.find_elements(By.CSS_SELECTOR, "li.course-exercise-item")
        # logger.error("exercises = %s", exercises)
        exercise = exercises[0]
        self.click_exercise(exercise)
        logger.error("exercise = %s", exercise)
        elements = sel.find_elements(By.CSS_SELECTOR, "li")
        # wait
        logger.error("elements = %s", elements)
        for element in elements:
            logger.error("exercise elements = %s", element)
        wait.until(EC.presence_of_element_located((By.XPATH, "//article")))

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000 ) # settings.LONG_WAIT)

        wait.until(EC.presence_of_element_located((By.XPATH, "//textarea")))
        logger.error("TEXTAREA FOUND")
        #elem = sel.find_element(By.CSS_SELECTOR, "textarea.uk-textarea[qkey='1']")
        #print("DISPLAYED:", elem.is_displayed())
        #print("ENABLED:", elem.is_enabled())
        #print("RECT:", elem.rect)
        
        answerarea = wait.until( EC.visibility_of_element_located( (By.CSS_SELECTOR, "textarea.uk-textarea[qkey]")))
        
        #answerarea = sel.find_element(By.XPATH, "//textarea")
        logger.error("NOW SEND KEYS")
        answerarea.send_keys("c sqrt(a^2 + b^2 )")
        sendbutton = sel.find_element(By.XPATH, "//i[contains(@class, 'sendicon')]")
        WebDriverWait(sel, 200000)
        sendbutton.click()
        # sel.find_element(By.XPATH,'//div[contains(@class, \'mc-item\')]//span[contains(text(), \'c1\')]').click()
        # sel.find_element(By.XPATH,'//a//i[contains(@class, \'uk-icon-send\')]').click()
        # wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'uk-alert-danger')]")))
        # logger.error("FOUND DANGER")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'termsof')]")))
        logger.error("termsof found")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'termsof') and text()='a']")))
        logger.error("termsof a  found")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'termsof') and text()='b']")))
        logger.error("termsof b  found")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'termsof') and text()='d']")))
        logger.error("termsof d  found")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'mathit') and text()='D']")))
        logger.error("termsof d(D)  found")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'mathit') and text()='A']")))
        logger.error("termsof a(A)  found")
        ays = sel.find_elements(By.XPATH, "//span[contains(@class,'termsof') and text()='a']")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class,'mathit') and text()='A']")))
        logger.error(" size of ays %d", len(ays))
        assert len(ays) == 1
        #WebDriverWait(sel, 350000).until(EC.invisibility_of_element_located((By.XPATH, "//span[contains(@class,'terms') and text()='c']")));
        logger.error("Looking for forbidden c ")
        #WebDriverWait(sel,350000).until(EC.presence_of_element_located((By.CLASS_NAME, "uk-alert-warning") ))
        #WebDriverWait(sel,350000).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'uk-alert-warning') and text()='c']")))
        #WebDriverWait(sel,350000).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'uk-alert-warning') and text()[contains('c : not valid ')] ]")))
        #logger.error("not valid c  found")
        #logger.error("ALL OK")
        #WebDriverWait(sel, 3).until(EC.invisibility_of_element_located((By.XPATH, "//span[contains(@class,'termsof') and text()='c']")));
        WebDriverWait(sel, 350000).until(EC.presence_of_element_located((By.XPATH, "//div[contains(.,'Not valid')]")))
        logger.error("NOT VALID FOUND")
        # wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "Correct"))
        # wait.until(EC.presence_of_element_located((By.XPATH, '//i[contains(@class, \'uk-icon-check\')]')))
        # wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, \'uk-alert-danger\')]')))

    def test_1_dev_linear_algebra(self):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        logger.error("OPEN")
        self.open_site()
        logger.error("CHANGE_OPTION")
        self.change_exercise_options()
        logger.error("LOGIN")
        self.login()
        logger.error("FIRST")
        self.first_exercise()
        logger.error("ANSWER")
        self.answer()
        logger.error("LOGOUT")
        self.logout()
