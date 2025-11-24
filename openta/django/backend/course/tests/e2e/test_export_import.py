# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from backend.selenium_utils.utils import OpenTAStaticLiveServerTestCase
import pytest
import pandas as pd
from deepdiff import DeepDiff
import csv
from exercises.aggregation import student_statistics_exercises, students_results
from django.conf import settings
import uuid
import filecmp
from selenium import webdriver
from selenium.webdriver.common.by import By
from backend.selenium_utils import create_selenium
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from tempfile import TemporaryDirectory
import os
import logging
import datetime
import exercises.paths as paths
from backend.selenium_utils.utils import create_exercise, create_database, create_user
from backend.selenium_utils import create_selenium
from exercises.models import Exercise
from course.models import Course
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
import backend.settings_test
import django_rq
import json
import time
import pytest

logger = logging.getLogger(__name__)


LOGGER.setLevel(logging.WARNING)


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class ExportImportTest(OpenTAStaticLiveServerTestCase):
    def setup(self, course_name="Test course"):
        super().setUp()
        course_key = uuid.uuid4()
        self.dir = TemporaryDirectory()
        paths.BASEDIR = os.path.join(self.dir.name, "django", "backend")
        os.makedirs(paths.BASEDIR, exist_ok=True)
        create_database(password=settings.SUPERUSER_PASSWORD, course_key=course_key, course_name=course_name)
        # create_database(password="pw", course_key=None)
        course = Course.objects.first()
        exercises_path = course.get_exercises_path()
        create_exercise(course, f"{settings.VOLUME}/openta", "exercise1")
        for msg in Exercise.objects.sync_with_disc(course, True):
            logger.error(msg)
        queue = django_rq.get_queue("default")
        self.worker = django_rq.get_worker("default")

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

    def login(self, username="student1", pw=settings.SUPERUSER_PASSWORD, assert_role="student"):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000)
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.clear()
        input_username.send_keys(username)
        input_password.clear()
        input_password.send_keys(pw)
        login.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
        assert assert_role in sel.page_source

    def logout(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000)
        sel.find_element(By.XPATH, "//a[contains(@href,'logout')]").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//form[contains(@action, 'login')]")))

    def first_exercise(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
        self.wait_for_then_click(wait, "exercise-a")

    def answer(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000)
        wait.until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'figure.png')]")))
        input_box = sel.find_elements(By.CSS_SELECTOR, "textarea")[0]
        input_box.send_keys("sin(2)")
        self.wait_for_then_click(wait, "click-send")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "firstcorrect")))

    def upload_image(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000)
        input_image = sel.find_elements(By.XPATH, "//input[@type='file']")[0]
        input_image.send_keys(os.path.abspath("testdata/test_image.jpg"))
        wait.until(EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'imageanswerthumb')]")))

    def back_to_course(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 200000)
        back = sel.find_element(By.CSS_SELECTOR, "a.onBackToCourse")
        back.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))

    def wait(self):
        sel = self.selenium
        wait = WebDriverWait(sel, 500)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "wait_forever")))

    def wait_for(self, wait, _className):
        logger.error("WAIT FOR %s", _className)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, _className)))
        logger.error("FOUND %s", _className)
        return self.selenium.find_element_by_class_name(_className)

    def wait_for_then_click(self, wait, _className):
        logger.error("WAIT FOR %s", _className)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, _className)))
        logger.error("FOUND %s", _className)

        try:
            self.selenium.find_element_by_class_name(_className).click()
        except StaleElementReferenceException:
            self.selenium.find_element_by_class_name(_className).click()

        logger.error("CLICK %s", _className)

    def do_click_sequence(self, wait, _classNames):
        for _className in _classNames:
            self.wait_for_then_click(wait, _className)

    def check_export_course(self):
        """
        Publish an exercise and verify that a student can answer and upload an image.
        """
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        self.answer()
        self.upload_image()
        self.logout()
        self.login("super", settings.SUPERUSER_PASSWORD , "admin")
        sel = self.selenium
        queue = django_rq.get_queue("default")
        sel.worker = django_rq.get_worker("default")

        for course in Course.objects.all():
            LOGGER.error("Calculating for course {}".format(course.course_name))
            student_statistics_exercises(force=True, course=course)
            LOGGER.error("Statistics done, now doing results.")
            students_results(force=True, course=course)
            LOGGER.error("Finished calculating results and statistics")

        wait = WebDriverWait(sel, 200000)
        seq = ["Course", "Export", "CourseExport", "Home", "Results", "Download", "GenerateResults", "DownloadExcel"]
        self.do_click_sequence(wait, seq)
        time.sleep(1)
        os.replace("/tmp/results.xlsx", "/tmp/results_export.xlsx")
        logger.error("EXPORT DONE")
        self.logout()

    def wait_for_spinners(self, wait):
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "Spinner")))
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "Spinner")))

    def check_import_course(self):
        logger.error("NOW IMPORT")
        self.setup(course_name="code789")
        self.open_site()
        self.change_exercise_options()
        self.login()
        self.first_exercise()
        course = Course.objects.get(course_name="code789")
        student, created = Group.objects.get_or_create(name="Student")
        perm_log_answer = Permission.objects.get(codename="log_question")
        student.permissions.add(perm_log_answer)
        student.save()
        logger.error("A1")
        u3 = create_user("student3", "student3@chalmers.se", settings.SUPERUSER_PASSWORD , course=course)
        # student.user_set.add(u1)
        # student.user_set.add(u2)
        student.user_set.add(u3)
        self.answer()
        self.upload_image()
        self.logout()
        logger.error("A2")
        self.open_site()
        self.login("super", settings.SUPERUSER_PASSWORD , "admin")
        sel = self.selenium
        queue = django_rq.get_queue("default")
        sel.worker = django_rq.get_worker("default")
        logger.error("A3")
        logger.error("getworker = %s", sel.worker)

        wait = WebDriverWait(sel, 200000)
        for course in Course.objects.all():
            LOGGER.error("Calculating for course {}".format(course.course_name))
            student_statistics_exercises(force=True, course=course)
            LOGGER.error("Statistics done, now doing results.")
            students_results(force=True, course=course)
            LOGGER.error("Finished calculating results and statistics")

        logger.error("A4")
        self.do_click_sequence(wait, ["Server"])
        self.do_click_sequence(wait, ["Import"])
        element = self.wait_for(wait, "UploadCourseZip")
        logger.error("A5")
        element.send_keys("/tmp/server.zip")
        self.wait_for(wait, "Done")
        sel.refresh()
        self.do_click_sequence(wait, ["ChooseCourseToShow", "code123"])
        self.do_click_sequence(wait, ["Results"])
        self.do_click_sequence(wait, ["Download", "GenerateResults", "DownloadExcel"])
        logger.error("A5")
        time.sleep(2)
        os.replace("/tmp/results.xlsx", "/tmp/results_import.xlsx")
        self.logout()

    # LOGIC IS test1 actively creates a course code123 and dumps server.zip into /tmp
    # test2 creates another course code789 with junk
    # test2 then imports code123 created in test1 and makes
    # sure that the results are the same as that computed in test1
    @pytest.mark.skip(reason="no way of currently testing this")
    def test1(self):
        if os.path.exists("/tmp/results_export.xlsx"):
            os.remove("/tmp/results_export.xlsx")
        self.setup(course_name="code123")
        logger.error("COURSE 123 set up ")
        self.check_export_course()

    @pytest.mark.skip(reason="no way of currently testing this")
    def test2(self):
        if os.path.exists("/tmp/results_import.xlsx"):
            os.remove("/tmp/results_import.xlsx")
        time.sleep(2)
        self.check_import_course()  # NOW IMPORTING code123 from before
        df = pd.read_excel("/tmp/results_import.xlsx", header=0)
        df.to_csv("/tmp/results_import.csv", index=False, quotechar="'")
        df = pd.read_excel("/tmp/results_export.xlsx", header=0)
        df.to_csv("/tmp/results_export.csv", index=False, quotechar="'")
        assert filecmp.cmp("/tmp/results_export.csv", "/tmp/results_import.csv")

        os.remove("/tmp/results_import.xlsx")
        os.remove("/tmp/results_export.xlsx")
        self.tearDown()
