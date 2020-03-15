from utils import OpenTAStaticLiveServerTestCase
from unittest.mock import patch
import time
from selenium import webdriver
from backend.selenium_utils import create_selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from tempfile import TemporaryDirectory
import os
import logging
import datetime
import exercises.paths as paths
from exercises.setup_tests import (
    create_exercise,
    create_database,
    create_exercise_from_dir,
    create_exercises_from_dir,
)
from exercises.models import Exercise
from course.models import Course
from django.utils import timezone
from django.conf import settings
import collections


LOGGER.setLevel(logging.WARNING)


class MacrosTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database(password='pw', course_key='c8b0c351-bda3-43a7-b5f5-2fce1807d2a9')
        course = Course.objects.first()
        dirname = os.path.dirname(os.path.abspath(__file__)) + '/testdir'
        exercises = create_exercises_from_dir(course, dirname)
        paths.EXERCISES_PATH = dirname
        paths.STUDENT_ASSETS_PATH = dirname + "/studentassets"
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            print(msg)
        self.selenium = create_selenium()
        self.selenium.implicitly_wait(0)

    def tearDown(self):
        self.selenium.quit()
        super().tearDown()

    def change_exercise_options(self, exercise):
        exercise.meta.published = True
        exercise.meta.required = True
        exercise.meta.feedback = True
        # exercise.meta.student_assets = True
        exercise.meta.feedback = True
        exercise.meta.image = True
        exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
        exercise.meta.save()

    def open_site(self):
        sel = self.selenium
        sel.get(self.live_server_url)

    def login(self, username="admin3", pw="pw", assert_role="admin"):
        sel = self.selenium
        wait = WebDriverWait(sel, 2000)
        input_username = sel.find_element_by_css_selector('input[id=id_username]')
        input_password = sel.find_element_by_css_selector('input[id=id_password]')
        login = sel.find_element_by_css_selector('input[type=submit]')
        input_username.send_keys(username)
        input_password.send_keys(pw)
        print("CLICK LOGIN")
        login.click()
        print("NOW WAIT FOR APP TO COME UP")
        wait.until(EC.text_to_be_present_in_element((By.ID, 'app'), assert_role))
        print("ASSERT_ROLE", assert_role)
        assert assert_role in sel.page_source

    def logout(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        sel.find_element_by_xpath('//a[contains(@href,\'logout\')]').click()
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//form[contains(@action, \'login\')]'))
        )

    def click_exercise(self, exercise):
        exercise_key = exercise.exercise_key
        sel = self.selenium
        wait = WebDriverWait(sel, 2000)
        exercise = sel.find_element_by_css_selector(
            'li.course-exercise-item[id=' + str(exercise_key) + ']'
        )
        exercise.click()
        wait.until(EC.presence_of_element_located((By.XPATH, '//article')))

    def answerall(self, answerdict):
        sel = self.selenium
        wait = WebDriverWait(sel, 2000)
        for questionkey, ans in answerdict.items():
            answerarea = sel.find_element_by_xpath(
                '//textarea[contains(@id,\"' + questionkey + '\")]'
            )
            i = 0;
            while i < 30 :
                 i += 1
                 answerarea.send_keys( Keys.BACK_SPACE )
            answerarea.send_keys(ans)
        buttons = sel.find_elements_by_xpath('//a//i[contains(@class, \'uk-icon-send\')]')
        print("NUMBER OF BUTTONS = ", len(buttons))
        for button in buttons:
            print("BUTTON = ", button.text)
            button.click()
            time.sleep(1)
            #corrects = sel.find_elements_by_xpath('//div[contains(@class, \'yescorrect\')]')
            #unchecked = sel.find_elements_by_xpath('//div[contains(@class, \'unchecked\')]')
            #print(" NUMBER CORRECTS = ", len(corrects))
            #print(" NUMBER UNCHECKED = ", len(unchecked))
            #print("SUCCESS")
        print("WAITING FOR READY")
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, \'ready\')]')))
        corrects = sel.find_elements_by_xpath('//div[contains(@class, \'yescorrect\')]')
        unchecked = sel.find_elements_by_xpath('//div[contains(@class, \'unchecked\')]')
        notcorrects = sel.find_elements_by_xpath('//div[contains(@class, \'notcorrect\')]')
        print("CORRECTS = ", len(corrects))
        print("NOTCORRECTS = ", len(notcorrects))
        print("UNCHECKED = ", len(unchecked))
        print("BUTTONS = ", len(buttons))
        return [len( corrects), len( unchecked) ,len( notcorrects) ]

    @patch("exercises.question.get_seed")
    def test_1_symbolic_with_hints_and_macros(self,get_seed=None):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        
        sel = self.selenium
        wait = WebDriverWait(sel, 2000)
        print("OPEN SITE")
        self.open_site()
        print("CHANGE EXERCISE OPTIONS")
        exercises = Exercise.objects.all()
        answerdicts = {}
        answerdicts['LEVEL0'] = collections.OrderedDict([('1', '-6 i  -2 j - 11 k '),
                ('2','[-6,-2,-11]' ) ,
                ('3',' sqrt( 23/31 )'  ) ] )
        get_seed.return_value = '45801'
        for exercise in exercises:
            print("NOW DO EXERCISE_PATH ", exercise.path)
            print("HANDLE EXERCISE_KEY = ", exercise.exercise_key)
            self.change_exercise_options(exercise)
            print("LOGIN")
            self.login()
            print("DO FIRST EXERCISE")
            self.click_exercise(exercise)
            print("EXERCISE PATH = ", exercise.path)
            print("ANSWER FIRST EXERCISE")
            [corrects,unchecked,notcorrects] = self.answerall(answerdicts[exercise.path])
            print("TRIPLE1 = ",  [corrects,unchecked,notcorrects] )
            assert notcorrects == 3 
            print("LOGOUT")

        #wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, \'nnready\')]')))
        sel = self.selenium
        answerdicts2 = {}
        answerdicts2['LEVEL0'] = collections.OrderedDict([('1', '[-6,-2,-11]'),
                ('2','-6 i - 2 j - 11 k ' ) ,
                ('3','sqrt( 23/30 )'  ) ] )
        for exercise in exercises:
            print("NOW DO EXERCISE_PATH ", exercise.path)
            print("HANDLE EXERCISE_KEY = ", exercise.exercise_key)
            #self.change_exercise_options(exercise)
            print("LOGIN")
            #self.login()
            print("DO FIRST EXERCISE")
            #self.click_exercise(exercise)
            print("EXERCISE PATH = ", exercise.path)
            print("ANSWER FIRST EXERCISE")
            [corrects,unchecked,notcorrects] = self.answerall(answerdicts2[exercise.path])
            print("TRIPLE2 = ",  [corrects,unchecked,notcorrects] )
            #wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, \'nnready\')]')))
            assert corrects == 3 
            print("LOGOUT")
        self.logout()
        self.tearDown()
