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


class PythonicTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database(password='pw', course_key='b1fd69bd-05b8-42a0-ab61-e8dcb9e30d99')
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
        # exercise.meta.student_assets = True
        exercise.meta.image = True
        exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
        exercise.meta.save()

    def open_site(self):
        sel = self.selenium
        sel.get(self.live_server_url)

    def login(self, username="student1", pw="pw", assert_role="student"):
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
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
        print("CLICK EXERCISE_KEY = ", exercise_key)
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'li.course-exercise-item[id=' + str(exercise_key) + ']')
            )
        )
        exercise = sel.find_element_by_css_selector(
            'li.course-exercise-item[id=' + str(exercise_key) + ']'
        )
        exercise.click()
        xp = '//article[contains(@id,\'' + str(exercise_key) + '\')]'
        wait.until(EC.presence_of_element_located((By.XPATH, xp)))

    def answerall(self, answerdict):
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
        # for questionkey, ans in answerdict.items():
        #    # answerarea = sel.find_element_by_xpath('//textarea[contains(@id,\"' + questionkey + '\")]')
        #    answerarea = sel.find_element_by_xpath(
        #        '//div[contains(@id,\"' + questionkey + '\")]//textarea'
        #    )
        #    for c in ans:
        #            answerarea.send_keys(c )
        #    #answerarea.send_keys(ans)
        buttons = sel.find_elements_by_xpath('//a//i[contains(@class, \'uk-icon-send\')]')
        questions = sel.find_elements_by_xpath('//div[contains(@class, \'question\')]')
        print("NUMBER OF BUTTONS = ", len(buttons))
        print("NUMBER OF QUESTIONS = ", len(questions))
        buttonkeys = []
        for question in questions:
            buttonkeys = buttonkeys + [question.get_attribute("id")]
            print("QUESTION =  ", question.get_attribute("id"))
        print("BUTTONKEYS = ", buttonkeys)
        for buttonkey in buttonkeys:
            print("DO BUTTONKEY = ", buttonkey)
            self.selenium.implicitly_wait(0)
            xpbutton = (
                '//div[contains(@id,\"'
                + buttonkey
                + '\")]//a//i[contains(@class, \'uk-icon-send\')]'
            )
            if buttonkey == '0':
                xpbutton = (
                    '//div[contains(@id,\"'
                    + buttonkey
                    + '\")]//a//i[contains(@class, \'uk-icon-send\')]'
                )
            print("XP = ", xpbutton)
            wait.until(EC.presence_of_element_located((By.XPATH, xpbutton)))
            answerareas = sel.find_elements_by_xpath(
                '//div[contains(@id,\"' + buttonkey + '\")]//textarea'
            )
            if len(answerareas) == 1:
                answerarea = answerareas[0]
                ans = answerdict[buttonkey]
                for c in ans:
                    answerarea.send_keys(c)
            button = sel.find_element_by_xpath(xpbutton)
            print("BUTTON TEXT", button.text)
            button.click()
            xpready = '//div[contains(@id,\"' + buttonkey + '\") and contains(@class, \'ready\')]'
            print("XPREADY ", xpready)
            for entry in sel.get_log('browser'):
                print(str(entry))
            wait.until(EC.presence_of_element_located((By.XPATH, xpready)))
            corrects = sel.find_elements_by_xpath('//div[contains(@class, \'yescorrect\')]')
            unchecked = sel.find_elements_by_xpath('//div[contains(@class, \'unchecked\')]')
            print("SUCCESS")
        # corrects =  sel.find_elements_by_xpath(  '//div[contains(@class, \'uk-alert-success\')]' )
        wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, \'ready\')]')))
        corrects = sel.find_elements_by_xpath('//div[contains(@class, \'yescorrect\')]')
        unchecked = sel.find_elements_by_xpath('//div[contains(@class, \'unchecked\')]')
        notcorrects = sel.find_elements_by_xpath('//div[contains(@class, \'notcorrect\')]')
        print("CORRECTS = ", len(corrects))
        print("NOTCORRECTS = ", len(notcorrects))
        print("UNCHECKED = ", len(unchecked))
        print("BUTTONS = ", len(buttons))
        print("CORRECTS = ", len(corrects))
        print("UNCHECKED = ", len(unchecked))
        print("BUTTONS = ", len(buttons))
        assert len(corrects) + len(unchecked) + len(notcorrects) == len(buttons)

    def test_1_pythonic(self):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        sel = self.selenium
        wait = WebDriverWait(sel, 200)
        print("OPEN SITE")
        self.open_site()
        print("CHANGE EXERCISE OPTIONS")
        exercises = Exercise.objects.all()
        answerdicts = {}
        answerdicts['pythonic'] = collections.OrderedDict(
            [('3', 'sqrt(a^2 +  b^2)'), ('4', '[[1,0],[0,1]]'), ('5', '[[0,0],[0,0]]')]
        )
        answerdicts['standard'] = collections.OrderedDict(
            [('0', '   sqrt(  a * a  +  b *   b )  ')]
        )
        answerdicts['standard2'] = collections.OrderedDict(
            [('0', '   sqrt(  a * a  +  b *   b )  ')]
        )

        for exercise in exercises:
            self.change_exercise_options(exercise)

        self.login()
        for exercise in exercises:
            print("DO EXERCISE")
            self.click_exercise(exercise)
            print("EXERCISE PATH = ", exercise.path)
            print("ANSWER FIRST EXERCISE")
            self.answerall(answerdicts[exercise.path])
            mainbutton = sel.find_element_by_xpath('//a[contains(@class, \'uk-navbar-brand\')]')
            mainbutton.click()
            print("LOGOUT")
        self.logout()
