# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import base64
import json
import os
import logging
import time
from selenium.webdriver.support.ui import WebDriverWait
from io import BytesIO
from typing import List
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class PdfGenerator:
    """
     Simple use case:
        pdf_file = PdfGenerator(['https://google.com']).main()
        with open('new_pdf.pdf', "wb") as outfile:
            outfile.write(pdf_file[0].getbuffer())
    """
    driver = webdriver 
    # https://chromedevtools.github.io/devtools-protocol/tot/Page#method-printToPDF
    print_options = {
        'landscape': False,
        'displayHeaderFooter': False,
        'printBackground': True,
        'preferCSSPageSize': True,
        'paperWidth': 6.97,
        'paperHeight': 16.5,
    }

    def create_selenium(*args, **kwargs):
        options = webdriver.ChromeOptions()
        d = DesiredCapabilities.CHROME
        d["loggingPrefs"] = {"browser": "ALL"}
        options.add_argument("headless")
        options.add_argument("download.prompt_for_download=false")
        options.add_argument("download.default_directory=/tmp/")
        options.add_argument("window-size=1280,1024")
        #options.add_argument('start-maximized')
        options.add_argument("--dns-prefetch-disable")
        return webdriver.Chrome(options=options, desired_capabilities=d)

    def login(self, username=None, pw=None):
        pw = os.environ.get('PASSWORD' )
        username = os.environ.get('USERNAME' )
        self.username = username
        sel = self.driver
        wait = WebDriverWait(sel, 50000)
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.clear()
        input_username.send_keys(username)
        input_password.clear()
        input_password.send_keys(pw)
        logger.error("CLICK LOGIN")
        login.click()
        logger.error("NOW WAIT FOR OpenHeader TO COME UP")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "OpenHeader")))
        logger.error("NOW WAIT FOR APP TEST_STUDENT.PY TO COME UP")
        sel.find_element(By.CLASS_NAME, "OpenHeader").click()
        logger.error("NOW WAIT FOR APP TO COME UP")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
        button = sel.find_element(By.ID,'736a2212-05aa-40ca-b4ec-a97df806b706')
        print(f"NOW CLICK BUTTON")
        button.click()


    def __init__(self, urls: List[str]):
        self.urls = urls

    def _get_pdf_from_url(self, url, *args, **kwargs):
        self.create_selenium()
        u = self.driver.get(url)
        self.login()
        print(f"U = {u}")
        time.sleep(0.3)  # allow the page to load, increase if needed

        print_options = self.print_options.copy()
        result = self._send_devtools(self.driver, "Page.printToPDF", print_options)
        return base64.b64decode(result['data'])

    @staticmethod
    def _send_devtools(driver, cmd, params):
        """
        Works only with chromedriver.
        Method uses cromedriver's api to pass various commands to it.
        """
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        print(f"PARAMS = {params}")
        body = json.dumps({'cmd': cmd, 'params': params})
        print(f"BODY = {body}")
        response = driver.command_executor._request('POST', url, body)
        return response.get('value')

    def _generate_pdfs(self):
        pdf_files = []

        for url in self.urls:
            result = self._get_pdf_from_url(url)
            file = BytesIO()
            file.write(result)
            pdf_files.append(file)

        return pdf_files

    def main(self) -> List[BytesIO]:
        webdriver_options = ChromeOptions()
        webdriver_options.add_argument('--headless')
        webdriver_options.add_argument('--disable-gpu')

        try:
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=webdriver_options
            )
            result = self._generate_pdfs()
        finally:
            self.driver.close()

        return result

# https://medium.com/@nikitatonkoshkur25/create-pdf-from-webpage-in-python-1e9603d6a430
pdf_file = PdfGenerator(['http://canary.localhost:8000']).main()
# save pdf to file
with open('google_site.pdf', "wb") as outfile:
    outfile.write(pdf_file[0].getbuffer())
