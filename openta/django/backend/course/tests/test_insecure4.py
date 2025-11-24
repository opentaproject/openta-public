# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from tempfile import TemporaryDirectory

import exercises.paths as paths
import pytest
import uuid
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

LOGGER.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class testadmin4Test(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database(course_key=uuid.uuid4())
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, "exercise3")
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            logger.error(msg)

    def open_site(self):
        sel = self.selenium
        sel.get(self.live_server_url)

    def login(self, username="admin4", pw="admin4@test.se", assert_role="admin"):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        logger.error("NOW WAIT FOR insecure TO COME UP")
        # wait.until(EC.presence_of_element_located((By.XPATH, '//*[text().contains(" insecure ")]')));
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "uk-alert-warning")))
        logger.error("SUCCESSFULLY FOUND INSECURE")
        sel.find_element(By.ID, "id_new_password1").send_keys("abcdefg")
        sel.find_element(By.ID, "id_new_password2").send_keys("abcdefg")
        sel.find_element(By.CSS_SELECTOR, "button[value=save]").click()
        try:
            wait.until(EC.alert_is_present())
            sel.switch_to.alert.dismiss()
        except Exception as e:
            logger.error("No alert present")
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        assert assert_role in sel.page_source

    def test_insecure_admin4(self):
        logger.error("OPEN")
        self.open_site()
        logger.error("LOGIN")
        self.login()
        logger.error("LOGOUT")
        self.logout()
