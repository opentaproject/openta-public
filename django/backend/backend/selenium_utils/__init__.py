from selenium import webdriver
from django.conf import settings


def create_selenium(*args, **kwargs):
    options = webdriver.ChromeOptions()
    if getattr(settings, 'HEADLESS', False):
        options.add_argument('headless')
    options.add_argument('window-size=800x600')
    return webdriver.Chrome(chrome_options=options)
