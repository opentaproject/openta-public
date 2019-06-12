"""Test settings."""

from backend.settings_lti import *


ALLOWED_HOSTS = ['*']
DEBUG = True

ASYNC = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST' : {
        'NAME': os.path.join(BASE_DIR, 'dbtest.sqlite3'),
        }
    }
}

LANGUAGE_CODE = 'sv'
TIME_ZONE = 'Europe/Stockholm'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

import warnings

warnings.filterwarnings(
    'error',
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r'django\.db\.models\.fields',
)


RQ_QUEUES = {
    'default': {'HOST': 'localhost', 'PORT': 6379, 'DB': 5, 'DEFAULT_TIMEOUT': 360, 'ASYNC': ASYNC}
}
CSRF_FAILURE_VIEW = 'backend.views.csrf_failure'
HELP_URL = 'https://opentaserver.com/'

UNITTESTS = True


HEADLESS = False
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
EXERCISES_PATH = 'media/exercise'
RUNNING_DEVSERVER = True
