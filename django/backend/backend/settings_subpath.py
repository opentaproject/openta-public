"""Settings for automatic discovery of URL subpath based on server installation folder."""

from backend.settings_base import *

_basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_subpath = str((os.path.split(os.path.split(os.path.split(_basedir)[0])[0])[1]))
SUBPATH = _subpath + '/'

LOGIN_URL = '/' + SUBPATH + 'login/'
LOGIN_REDIRECT_URL = '/' + SUBPATH

STATIC_TAG = 'static'
STATIC_URL = '/' + SUBPATH + STATIC_TAG + '/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, STATIC_TAG),)
STATIC_ROOT = os.path.join(BASE_DIR, "deploystatic")
