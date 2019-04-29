"""Test settings."""

from backend.settings_base import *

ALLOWED_HOSTS = ['*']
RUNNING_DEVSERVER = True

DEBUG = True

#MIDDLEWARE = MIDDLEWARE + [
#    'django.middleware.security.SecurityMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.locale.LocaleMiddleware',
#    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
#    'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'backend.simulate_slow.simulate_slow'
#]

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

HEADLESS = False
