from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities    
from django.conf import settings
import logging 
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
seleniumLogger.setLevel(logging.WARNING)
from urllib3.connectionpool import log as urllibLogger

def create_selenium(*args, **kwargs):
    options = webdriver.ChromeOptions()
    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = { 'browser':'ALL' }
    urllibLogger.setLevel(logging.WARNING)
    if getattr(settings, 'HEADLESS', False):
        options.add_argument('headless')
    # options.add_argument("download.prompt_for_download=false")
    # options.add_argument("download.default_directory "/tmp")
    # options.add_argument("download.default_directory=/tmp/")
    options.add_argument('window-size=1900x1200')
    return webdriver.Chrome(chrome_options=options,desired_capabilities=d)
