from utils import OpenTAStaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from backend.selenium_utils import create_selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from tempfile import TemporaryDirectory
import os
import logging
import datetime
import exercises.paths as paths
from exercises.setup_tests import create_exercise, create_database
from backend.selenium_utils import create_selenium
from .models import Exercise
from course.models import Course
from django.utils import timezone
from django.conf import settings

LOGGER.setLevel(logging.WARNING)


class AuditTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        self.dir = TemporaryDirectory()
        course = Course.objects.first()
        create_exercise(course, self.dir.name, 'exercise1')
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, True):
            print(msg)
        self.selenium = create_selenium()
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
        wait = WebDriverWait(sel, 2)
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
        wait = WebDriverWait(sel, 2)
        input_box = sel.find_elements_by_css_selector('textarea')[0]
        input_box.send_keys('sin(2)')
        send_button = sel.find_elements_by_xpath('//a[.//i[contains(@class, \'uk-icon-send\')]]')[0]
        send_button.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "korrekt"))

    def upload_image(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        input_image = sel.find_elements_by_xpath('//input[@type=\'file\']')[0]
        input_image.send_keys(os.path.abspath('testdata/test_image.jpg'))
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//img[contains(@src, \'imageanswerthumb\')]')
            )
        )

    def back_to_course(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        back = sel.find_element_by_css_selector('ul.exercise-menu > li.uk-nav-header > a')
        back.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))

    def wait(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 500)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'wait_forever')))

    def audit_goto_my_audits(self):
        sel = self.selenium
        sel.find_element_by_xpath('//a[contains(text(), \'Audit\')]').click()
        sel.find_element_by_xpath('//a[contains(text(), \'My audits\')]').click()

    def audit_unaudited_exists(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//span[text()[contains(., \'1\')] and text()[contains(.,\'Ready for audit\')]]',
                )
            )
        )

    def audit_add_audit(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        sel.find_element_by_xpath('//button[contains(text(), \'Add student\')]').click()
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@id="unfinished-audits"]/a[text()[contains(., \'1\')]]')
            )
        )
        (
            sel.find_element_by_xpath(
                '//div[@id="unfinished-audits"]/a[text()[contains(., \'1\')]]'
            ).click()
        )
        wait.until(EC.presence_of_element_located((By.XPATH, '//textarea[@id="audit-message"]')))

    def audit_add_message(self):
        sel = self.selenium
        input_box = sel.find_elements_by_xpath('//textarea[@id="audit-message"]')[0]
        input_box.send_keys('test message')

    def audit_revision_needed(self):
        sel = self.selenium
        sel.find_element_by_xpath('//a[@id="revision-needed"]').click()

    def audit_publish(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        sel.find_element_by_xpath('//a[@id="publish-single"]').click()
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@id="published-audits"]/a[text()[contains(., \'1\')]]')
            )
        )

    def audit_check_student_revision_needed(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="revision-needed"]')))
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@id="audit-message" and text()[contains(., \'test message\')]]')
            )
        )

    def audit_check_student_revision_not_needed(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="revision-not-needed"]')))
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@id="audit-message" and text()[contains(., \'test message\')]]')
            )
        )

    def audit_submit_revision(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        sel.find_element_by_xpath('//a[@id="revision-update"]').click()
        wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="revision-updated"]')))

    def audit_goto_published(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        (
            sel.find_element_by_xpath(
                '//div[@id="published-audits"]/a[text()[contains(., \'1\')]]'
            ).click()
        )
        wait.until(EC.presence_of_element_located((By.XPATH, '//textarea[@id="audit-message"]')))

    def audit_check_updated(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="audit-updated"]')))

    def audit_revision_not_needed(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 2)
        sel.find_element_by_xpath('//a[@id="revision-not-needed"]').click()
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//i[@id="revision-not-needed-done"]'))
        )

    def test_1_student_answer_and_upload_image(self):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer()
        self.upload_image()
        self.logout()

        self.open_site()
        self.login('super', 'pw', 'admin')
        self.first_exercise()
        self.audit_goto_my_audits()
        self.audit_unaudited_exists()
        self.audit_add_audit()
        self.audit_add_message()
        self.audit_revision_needed()
        self.audit_publish()

        self.logout()
        self.open_site()
        self.login()
        self.first_exercise()
        self.audit_check_student_revision_needed()
        self.audit_submit_revision()
        self.logout()

        self.open_site()
        self.login('super', 'pw', 'admin')
        self.first_exercise()
        self.audit_goto_my_audits()
        self.audit_goto_published()
        self.audit_check_updated()
        self.audit_revision_not_needed()
        self.logout()

        self.open_site()
        self.login()
        self.first_exercise()
        self.audit_check_student_revision_not_needed()
        self.logout()
