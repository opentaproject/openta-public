from utils import OpenTAStaticLiveServerTestCase
from exercises.aggregation import student_statistics_exercises, students_results
import uuid
import filecmp
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
from .setup_tests import create_exercise, create_database, create_user
from backend.selenium_utils import create_selenium
from exercises.models import Exercise
from course.models import Course
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
from django.conf import settings
import django_rq

LOGGER.setLevel(logging.WARNING)


class ExportImportTest(OpenTAStaticLiveServerTestCase):
    def setup(self, course_name='Test course'):
        # super().setUp()
        course_key = uuid.uuid4()
        self.dir = TemporaryDirectory()
        paths.BASEDIR = os.path.join(self.dir.name, 'django', 'backend')
        os.makedirs(paths.BASEDIR, exist_ok=True)
        create_database(password="learning", course_key=course_key, course_name=course_name)
        course = Course.objects.first()
        exercises_path = course.get_exercises_path()
        print("COURSE EXERCISES_PATH = ", exercises_path)
        create_exercise(course, exercises_path, 'exercise1')
        for msg in Exercise.objects.sync_with_disc(course, True):
            print(msg)
        self.selenium = create_selenium()
        self.selenium.implicitly_wait(20)
        queue = django_rq.get_queue('default')
        print("queue = ", queue)
        self.worker = django_rq.get_worker('default')
        print("getworker = ", self.worker)

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

    def login(self, username="student1", pw="learning", assert_role="student"):
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
        input_username = sel.find_element_by_css_selector('input[id=id_username]')
        input_password = sel.find_element_by_css_selector('input[id=id_password]')
        login = sel.find_element_by_css_selector('input[type=submit]')
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'uk-thumbnail-exercise')))
        assert assert_role in sel.page_source

    def logout(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
        sel.find_element_by_xpath('//a[contains(@href,\'logout\')]').click()
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//form[contains(@action, \'login\')]'))
        )

    def first_exercise(self):
        print("ZZZZZZZZZ 01")
        sel = self.selenium
        print("ZZZZZZZZZ 02")
        wait = WebDriverWait(sel, 20)
        print("ZZZZZZZZZ 03")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))
        print("ZZZZZZZZZ 04")
        self.wait_for_then_click(wait, 'exercise-a')
        # _className = 'exercise-a'
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, _className)))
        # print("FOUND ", _className)
        # exercise = self.selenium.find_element_by_class_name(_className)
        # exercise = sel.find_elements_by_css_selector('li.course-exercise-item')
        print("ZZZZZZZZZ 05")
        # exercise = exercises[0]
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'forever')))
        # print("ZZZZZZZZZ 06")
        # exercise.click()
        print("ZZZZZZZZZ 07")
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea.uk-width-1-1')))
        print("ZZZZZZZZZ 08")

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//img[contains(@src, \'figure.png\')]'))
        )
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'extarea.uk-width-1-1')))
        input_box = sel.find_elements_by_css_selector('textarea')[0]
        input_box.send_keys('sin(2)')
        self.wait_for_then_click(wait, 'uk-button-success')
        # send_button = sel.find_elements_by_xpath('//a[.//i[contains(@class, \'uk-icon-send\')]]')[0]
        # send_button.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'form'), "korrekt"))

    def upload_image(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
        input_image = sel.find_elements_by_xpath('//input[@type=\'file\']')[0]
        input_image.send_keys(os.path.abspath('testdata/test_image.jpg'))
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//img[contains(@src, \'imageanswerthumb\')]')
            )
        )

    def back_to_course(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 20)
        back = sel.find_element_by_css_selector('a.onBackToCourse')
        back.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.course-exercise-item')))

    def wait(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 500)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'wait_forever')))

    def wait_for(self, wait, _className):
        print("WAIT FOR ", _className)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, _className)))
        print("FOUND ", _className)
        return self.selenium.find_element_by_class_name(_className)

    def wait_for_then_click(self, wait, _className):
        print("WAIT FOR ", _className)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, _className)))
        print("FOUND ", _className)
        self.selenium.find_element_by_class_name(_className).click()

    def do_click_sequence(self, wait, _classNames):
        for _className in _classNames:
            self.wait_for_then_click(wait, _className)

    def check_export_course(self):
        '''
        Publish an exercise and verify that a student can answer and upload an image.
        '''
        print("YYYYYYYYYYYYYYYYYYYYY 11")
        self.open_site()
        print("YYYYYYYYYYYYYYYYYYYYY 12")
        self.change_exercise_options()
        print("YYYYYYYYYYYYYYYYYYYYY 13")
        self.login()
        print("YYYYYYYYYYYYYYYYYYYYY 14")
        self.first_exercise()
        print("YYYYYYYYYYYYYYYYYYYYY 15")
        self.answer()
        print("YYYYYYYYYYYYYYYYYYYYY 16")
        self.upload_image()
        print("YYYYYYYYYYYYYYYYYYYYY 21")
        self.logout()
        self.login('super', 'learning', 'admin')
        sel = self.selenium
        queue = django_rq.get_queue('default')
        print("queue = ", queue)
        sel.worker = django_rq.get_worker('default')
        print("getworker = ", sel.worker)

        print("YYYYYYYYYYYYYYYYYYYYY 31")

        for course in Course.objects.all():
            LOGGER.info("Calculating for course {}".format(course.course_name))
            student_statistics_exercises(force=True, course=course)
            LOGGER.info('Statistics done, now doing results.')
            students_results(force=True, course=course)
            LOGGER.info('Finished calculating results and statistics')

        print("YYYYYYYYYYYYYYYYYYYYY 41")

        wait = WebDriverWait(sel, 20)
        seq = ['Course', 'Export', 'CourseExport', 'Home', 'Results', 'Download', 'DownloadExcel']
        self.do_click_sequence(wait, seq)
        print("YYYYYYYYYYYYYYYYYYYYY 51")
        os.replace("/tmp/results.txt", "/tmp/results_export.txt")
        self.logout()

    def wait_for_spinners(self, wait):
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Spinner')))
        print("FOUND ELEMENT Spinner")
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'Spinner')))
        print("Spinner dispappeared")

    def check_import_course(self):
        print("XXXXXXXXXXXXXXXXXXx 6")
        self.setup(course_name='code789')
        print("XXXXXXXXXXXXXXXXXXx 7")
        self.open_site()
        print("XXXXXXXXXXXXXXXXXXx 8")
        self.change_exercise_options()
        print("XXXXXXXXXXXXXXXXXXx 9")
        self.login()
        print("XXXXXXXXXXXXXXXXXXx 10")
        self.first_exercise()
        print("XXXXXXXXXXXXXXXXXXx 11")
        course = Course.objects.get(course_name="code789")
        print("XXXXXXXXXXXXXXXXXXx 12")
        student, created = Group.objects.get_or_create(name="Student")
        print("XXXXXXXXXXXXXXXXXXx 13 ")
        perm_log_answer = Permission.objects.get(codename="log_question")
        student.permissions.add(perm_log_answer)
        student.save()
        # u1 = create_user('student1', 'student1@test.se', 'learning', course=course)
        # u2 = create_user('student2', 'student2@test.se', 'learning', course=course)
        u3 = create_user('student3', 'student3@chalmers.se', 'learning', course=course)
        # student.user_set.add(u1)
        # student.user_set.add(u2)
        student.user_set.add(u3)
        self.answer()
        self.upload_image()
        self.logout()
        self.open_site()
        self.login('super', 'learning', 'admin')
        print("XXXXXXXXXXXXXXXXXXx 16")
        sel = self.selenium
        queue = django_rq.get_queue('default')
        print("queue = ", queue)
        sel.worker = django_rq.get_worker('default')
        print("getworker = ", sel.worker)

        wait = WebDriverWait(sel, 2000)
        for course in Course.objects.all():
            LOGGER.info("Calculating for course {}".format(course.course_name))
            student_statistics_exercises(force=True, course=course)
            LOGGER.info('Statistics done, now doing results.')
            students_results(force=True, course=course)
            LOGGER.info('Finished calculating results and statistics')

        print("XXXXXXXXXXXXXXXXXXx 26")
        self.do_click_sequence(wait, ['Server', 'Import'])
        # wait.until(EC.presence_of_element_located((By.XPATH, 'UploadCourseZip')))
        element = self.wait_for(wait, "UploadCourseZip")
        element.send_keys('/tmp/server.zip')
        print("SENT KEYS ")
        # self.do_click_sequence(wait, ['UploadCourseZip'])
        # print("CLICKED")
        # elt = '//div[contains(@class, \'Done\')]'
        # wait.until(EC.presence_of_element_located((By.XPATH, elt)))
        self.wait_for(wait, 'Done')
        sel.refresh()
        # self.wait_for_spinners(wait)
        # sel.refresh()
        # IF TESTING ANOTHER COURSE NAME AS IMPORT SO THERE ARE TWO COURSES
        # USE THE FOLLOWING
        self.do_click_sequence(wait, ['ChooseCourseToShow', 'code123'])
        self.do_click_sequence(wait, ['Results', 'Download', 'DownloadExcel'])
        os.replace("/tmp/results.txt", "/tmp/results_import.txt")
        # self.do_click_sequence(wait, ['Forever'])
        self.logout()

    # LOGIC IS test1 actively creates a course code123 and dumps server.zip into /tmp
    # test2 creates another course code789 with junk
    # test2 then imports code123 created in test1 and makes
    # sure that the results are the same as that computed in test1

    def test1(self):
        if os.path.exists("/tmp/results_export.txt"):
            os.remove("/tmp/results_export.txt")
        self.setup(course_name='code123')
        print("COURSE 123 set up ")
        self.check_export_course()

    def test2(self):
        if os.path.exists('/tmp/results_import.txt'):
            os.remove("/tmp/results_import.txt")
        self.check_import_course()  # NOW IMPORTING code123 from before
        assert filecmp.cmp('/tmp/results_export.txt', '/tmp/results_import.txt')
        os.remove("/tmp/results_import.txt")
        os.remove("/tmp/results_export.txt")
        self.tearDown()
