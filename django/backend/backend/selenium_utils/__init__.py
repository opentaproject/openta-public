from selenium import webdriver
from django.conf import settings


def create_selenium(*args, **kwargs):
    options = webdriver.ChromeOptions()
    if getattr(settings, 'HEADLESS', False):
        options.add_argument('headless')
    options.add_argument('window-size=1280x1024')
    # options.add_argument("download.prompt_for_download=false")
    # options.add_argument("download.default_directory "/tmp")
    # options.add_argument("download.default_directory=/tmp/")
    return webdriver.Chrome(chrome_options=options)
