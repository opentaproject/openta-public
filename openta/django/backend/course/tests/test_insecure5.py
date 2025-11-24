# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

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

LOGGER.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@pytest.mark.end_to_end
@pytest.mark.enable_signals
class SecondDevLinearAlgebraTest(OpenTAStaticLiveServerTestCase):
    def setUp(self):
        super().setUp()
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, "exercise3")
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            print(msg)

    def open_site(self):
        sel = self.selenium
        sel.get(self.live_server_url)

    def login(self, username="admin5", pw="admin5@test.se", assert_role="admin"):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        print("NOW WAIT FOR insecure TO COME UP")
        # wait.until(EC.presence_of_element_located((By.XPATH, '//*[text().contains(" insecure ")]')));
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "uk-alert-warning")))
        print("SUCCESSFULLY FOUND INSECURE")
        #sel.implicitly_wait(10)
        print("WAIT DONE")
        wait.until(EC.presence_of_element_located((By.ID, "id_new_password1")))
        sel.find_element(By.ID, "id_new_password1").send_keys("akasasdf890asdf")
        sel.find_element(By.ID, "id_new_password2").send_keys("akasasdf890asdf")
        sel.find_element(By.CSS_SELECTOR, "button[value=save]").click()
        try:
            wait.until(EC.alert_is_present())
            sel.switch_to.alert.dismiss()
        except Exception as e:
            print("No alert present")
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        assert assert_role in sel.page_source

    def test_insecure_admin4(self):
        print("OPEN")
        self.open_site()
        print("LOGIN")
        self.login()
        print("LOGOUT")
        self.logout()
