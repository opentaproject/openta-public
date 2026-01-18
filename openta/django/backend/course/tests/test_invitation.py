# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from tempfile import TemporaryDirectory

import exercises.paths as paths
import pytest
from course.models import Course
from exercises.models import Exercise
from invitations.models import Invitation
from myinvitations.views import create_user_with_email_password
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
        create_database()
        course = Course.objects.first()
        self.dir = TemporaryDirectory()
        create_exercise(course, self.dir.name, "exercise3")
        paths.EXERCISES_PATH = self.dir.name
        for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
            logger.error(msg)

    def open_site(self):
        sel = self.selenium
        sel.get(self.live_server_url)

    def login(self, username="admin1", pw="pw", assert_role="admin"):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.send_keys(username)
        input_password.send_keys(pw)
        login.click()
        logger.error("NOW WAIT PAGE TO COME UP")
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        assert assert_role in sel.page_source
        linkstring = '//*[contains(@qkey,"link-to-admin")]'
        wait.until(EC.presence_of_element_located((By.XPATH, linkstring)))
        link = sel.find_element(By.XPATH, linkstring).click()
        linkstring = '//*[text().contains("Invitations")]'
        linkstring = '//*[contains(@qkey,"dummy link-to-admin")]'
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Invitations")))
        print(f"CLICK Invitations")
        link = sel.find_element(By.LINK_TEXT, "Invitations").click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "addlink")))
        print(f"CLICK Add invitation")
        link = sel.find_element(By.CLASS_NAME, "addlink").click()
        wait.until(EC.presence_of_element_located((By.ID, "id_emails")))
        textarea = sel.find_element(By.ID, "id_emails")
        textarea.send_keys("a@b.com")
        # select = sel.find_element(By.XPATH,"//option[@value='7']")  # OK
        select = sel.find_element(By.XPATH, '//option[contains(text(),"admin1")]')  # OK TOO
        print(f"SELECT = {select}")
        select.click()
        link = sel.find_element(By.XPATH, "//input[@value='Save']")  # OK
        link.click()
        invitation = Invitation.objects.all()[0]
        key = invitation.key
        email = invitation.email
        course = Course.objects.first()
        invitation.accepted = True
        invitation.save()
        print(f" INVITATION = {invitation}")
        print(f" KEY = {key} ")
        print("WAITING FOR VIEW SITE")
        create_user_with_email_password("default", email, course, password=key, role="Student")

    @pytest.mark.skip(reason="this test is not working -- needs to be fixed")
    def test_invited_login4(self):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        logger.error("OPEN")
        self.open_site()
        logger.error("LOGIN")
        self.login()
        view_site = sel.find_element(By.XPATH, "//a[@href='/']")
        view_site.click()
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        bye = sel.find_element(By.XPATH, '//*[contains(@title,"Logga ut")]')
        bye.click()
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        invitation = Invitation.objects.all()[0]
        input_username.send_keys(invitation.email)
        input_password.send_keys(invitation.key)
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        login.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "uk-alert-warning")))
        sel.find_element(By.ID, "id_new_password1").send_keys("abcdefg")
        sel.find_element(By.ID, "id_new_password2").send_keys("abcdefg")
        sel.find_element(By.CSS_SELECTOR, "button[value=save]").click()
        try:
            sel.switch_to.alert.dismiss()
        except Exception:
            print("No alert present")
        wait.until(EC.presence_of_element_located((By.ID, "app")))
        self.logout()

        # logger.error("LOGOUT")
        # self.logout()
