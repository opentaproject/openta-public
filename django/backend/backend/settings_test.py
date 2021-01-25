"""Test settings."""

from backend.settings_lti import *


ALLOWED_HOSTS = ['*']
DEBUG = True

ASYNC = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
	'OPTIONS': { 'timeout': 20,  },
        'TEST' : {
        'NAME': os.path.join(BASE_DIR, 'dbtest.sqlite3'),
		'OPTIONS': { 'timeout': 20,  }
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
FORCE_ROLE_TO_STUDENT = False
EXERCISES_PATH = 'media/exercise'
RUNNING_DEVSERVER = True
DO_CACHE = True
CHECK_AGGREGATIONS = False
RUNTESTS = True
CACHE_LIFETIME = 0
DEBUG = True
IGNORE_NO_FEEDBACK = True
REFRESH_SEED_ON_CORRECT_ANSWER = False
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

VALID_ROLES = ['ContentDeveloper', 'Learner', 'Student', 'Instructor', 'Observer']
FORCE_ROLE_TO_STUDENT = False
VOLUME = '/srv/multicourse/'
STATIC_URL = '/static/'
