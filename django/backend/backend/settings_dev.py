"""Development settings."""

from backend.settings_subpath import *

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ALLOWED_HOSTS = ['*']

TIME_ZONE = 'Europe/Copenhagen'
