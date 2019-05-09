from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.remote_connection import LOGGER
from django.conf import settings


def create_selenium(*args, **kwargs):
    options = webdriver.ChromeOptions()
    if hasattr(settings, 'HEADLESS') and settings.get('HEADLESS', False):
        options.add_argument('headless')
    options.add_argument('window-size=800x600')
    return webdriver.Chrome(chrome_options=options )

