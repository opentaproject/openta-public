"""Production settings."""

from backend.settings_lti import *
from google.oauth2 import service_account

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
RQ_QUEUES = {'default': {'HOST': 'localhost', 'PORT': 6379, 'DB': 12, 'DEFAULT_TIMEOUT': 20 * 60 }}

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
VERSION_TAG = os.environ.get('VERSION_TAG')

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
try:
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file( 'backend/keyfile.json')
except:
    pass
STATIC_URL = 'https://storage.googleapis.com/openta-cdn-bucket/%s/' % VERSION_TAG
try:
        from backend.settings_sqlite3 import *
except:
        pass
