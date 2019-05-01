"""Development settings."""

from backend.settings_lti import *

TIME_ZONE = 'Europe/Copenhagen'
INSTALLED_APPS = INSTALLED_APPS + ['autotranslate'] + ['translations']
RUNNING_DEVSERVER = len(sys.argv) > 1 and sys.argv[1] == 'runserver'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ALLOWED_HOSTS = ['*']

TIME_ZONE = 'Europe/Copenhagen'
