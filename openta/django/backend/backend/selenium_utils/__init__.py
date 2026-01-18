# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
from selenium import webdriver
#from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from django.conf import settings
import logging
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger

seleniumLogger.setLevel(logging.DEBUG)
from urllib3.connectionpool import log as urllibLogger


def create_selenium(*args, **kwargs):
    options = webdriver.ChromeOptions()
    #d = DesiredCapabilities.CHROME
    #d["loggingPrefs"] = {"browser": "ALL"}
    #urllibLogger.setLevel(logging.ERROR)

    if settings.HEADLESS :
        options.add_argument("--headless=new")
    options.add_argument("download.prompt_for_download=false")
    options.add_argument("download.default_directory=/tmp/")
    options.add_argument("window-size=1280,1024")
    ##options.add_argument('start-maximized')
    options.add_argument("--dns-prefetch-disable")
    options.add_argument("--disable-search-engine-choice-screen")
    for path in ['/usr/bin','/usr/local/bin/' ] :
        testpath =  os.path.join( path, 'chromium-browser') 
        if os.path.exists( testpath ):
            options.binary_location = testpath
    #
    # USE THIS LINE FOR SPECIFIC BINARY
    # MAKE SURE SELENIUM IS COMPATIBLE
    # options.binary_location = "/Applications/Google-Chrome-109.app/Contents/MacOS/Google Chrome"
    #
    #
    return webdriver.Chrome(options=options ) # , desired_capabilities=d)
