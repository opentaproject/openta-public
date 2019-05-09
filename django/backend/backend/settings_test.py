"""Test settings."""

from backend.settings_lti import *

ALLOWED_HOSTS = ['*']
RUNNING_DEVSERVER = True

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'dbtest.sqlite3'),
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
