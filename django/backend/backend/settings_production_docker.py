"""Production settings."""

from backend.settings_lti import *

SECRET_KEY = '$$uo0799i74g3oci-wy4_31mmly-nhlzj+qwi@cgr!@ynqmv=('

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
DEBUG = True
APPEND_SLASH = True

ALLOWED_HOSTS = ['*']
# USE_X_FORWARDED_HOST = True

EMAIL_HOST = 'smtp.gu.se'
EMAIL_PORT = 25

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Use this for local smtp
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 25

# Or this for custom smtp config through admin interface (per course)
# USE_CUSTOM_SMTP_EMAIL = True

# Redis information
RQ_QUEUES = {'default': {'HOST': 'localhost', 'PORT': 6379, 'DB': 0, 'DEFAULT_TIMEOUT': 20 * 60 }}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'localhost',
        'PORT': 5432,
    }
}

FILE_UPLOAD_PERMISSIONS = 0o644

_subpath = os.environ.get('OPENTA_SUBPATH')

if _subpath is not None:
    SUBPATH = _subpath + '/'

    LOGIN_URL = '/' + SUBPATH + 'login/'
    LOGIN_REDIRECT_URL = '/' + SUBPATH

    STATIC_TAG = 'static'
    STATIC_URL = '/' + SUBPATH + STATIC_TAG + '/'
    # STATICFILES_DIRS = (os.path.join(BASE_DIR, STATIC_TAG),)
    # STATIC_ROOT = os.path.join(BASE_DIR, "deploystatic")

    CSRF_COOKIE_NAME = 'csrftoken' + _subpath
    SESSION_COOKIE_NAME = 'sessionid' + _subpath

# Fix same-site cookie
