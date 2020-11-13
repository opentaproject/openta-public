"""Production settings."""

from backend.settings_base import *

SECRET_KEY = '$$uo0799i74g3oci-wy4_31mmly-nhlzj+qwi@cgr!@ynqmv=('

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
DEBUG = False

ALLOWED_HOSTS = ['*']

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Use this for local smtp
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 25

# Or this for custom smtp config through admin interface (per course)
# USE_CUSTOM_SMTP_EMAIL = True

# Redis information
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': 20 * 60,
        'ASYNC': True,
    }
}

# Fix same-site cookie
