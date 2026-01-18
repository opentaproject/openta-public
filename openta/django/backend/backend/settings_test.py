# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
import glob
import logging
import uuid

logger = logging.getLogger(__name__)
import platform
import subprocess

from backend.settings_static import *


ADMINURL = "administration"
ANSWER_DELAY = "0"
BLOCK_EMAIL_AUDITS = True
CACHES = {'default': {'BACKEND': 'django_redis.cache.RedisCache',
	 'LOCATION': ['redis://localhost:6379/1'],
	 'TIMEOUT': 40},
	 'aggregation': {'BACKEND': 'django_redis.cache.RedisCache',
	 'LOCATION': ['redis://localhost:6379/1'],
	 'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient',
	 'MAX_ENTRIES': '10000'},
	 'TIMEOUT': 40 ,
	 'KEY_PREFIX': 'aggregation'},
	 'imagekit': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
	 'LOCATION': '/subdomain-data/CACHE/imagekit',
	 'TIMEOUT': 40 ,
	 'OPTIONS': {'MAX_ENTRIES': 30000}},
	 'translations': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
	 'LOCATION': '/tmp/subdomain-data/translations_cache',
	 'TIMEOUT': 40 ,
	 'OPTIONS': {'MAX_ENTRIES': 30000}}}
CONN_MAX_AGE = 0
CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*', 'http://*.localhost:3000', 'http://localhost:8000', 'http://*.localhost:8000', 'http://localhost:*']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
	 'NAME': 'default',
	 'OPTIONS': {'timeout': 20},
	 'TEST': {'NAME': f'{BASE_DIR}/default.dbtest.sqlite3',
	 'OPTIONS': {'timeout': 20},
	 'ATOMIC_REQUESTS': False}},
	 'openta': {'ENGINE': 'django.db.backends.sqlite3',
	 'NAME': 'default',
	 'OPTIONS': {'timeout': 20},
	 'TEST': {'NAME': f'{BASE_DIR}/default.dbtest.sqlite3',
	 'OPTIONS': {'timeout': 20},
	 'ATOMIC_REQUESTS': False}},
	 'sites': {'ENGINE': 'django.db.backends.sqlite3',
	 'NAME': 'sites',
	 'OPTIONS': {'timeout': 20},
	 'TEST': {'NAME': f'{BASE_DIR}/sites.dbtest.sqlite3',
	 'OPTIONS': {'timeout': 20},
	 'ATOMIC_REQUESTS': False}},
	 'localhost': {'ENGINE': 'django.db.backends.sqlite3',
	 'NAME': f'{BASE_DIR}/db.sqlite3'},
	 'opentasites': {'ENGINE': 'django.db.backends.sqlite3',
	 'NAME': 'default',
	 'OPTIONS': {'timeout': 20},
	 'TEST': {'NAME': f'{BASE_DIR}/default.dbtest.sqlite3',
	 'OPTIONS': {'timeout': 20},
	 'ATOMIC_REQUESTS': False}}}
DB_NAME = "default"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
ENABLE_AUTO_TRANSLATE = False
EXERCISES_IMPORT_FILE_SIZE_LIMIT = 100000000.0
EXERCISES_PATH = "/tmp/subdomain-data/openta/exercises"
FIX_XML = False
INSTALLED_APPS = ['django.contrib.admin',
	 'django.contrib.auth',
	 'django.contrib.contenttypes',
	 'django.contrib.sessions',
	 'django.contrib.messages',
	 'django.contrib.staticfiles',
	 'django.contrib.sites',
	 'rest_framework',
	 'exercises.apps.ExercisesConfig',
	 'course.apps.CourseConfig',
	 'users.apps.UsersConfig',
	 'workqueue.apps.WorkqueueConfig',
	 'widget_tweaks',
	 'django_extensions',
	 'django_rq',
	 'imagekit',
	 'hijack',
	 'import_export',
	 'autotranslate',
	 'translations',
	 'aggregation',
	 'opentalti',
	 'invitations',
	 'myinvitations']
LEGACY_FILE_SERVE = False
LOCALE_PATHS = [f'{BASE_DIR}/locale']
MEDIA_ROOT = "/tmp/subdomain-data/openta/media"
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware',
	 'django.contrib.sessions.middleware.SessionMiddleware',
	 'django.middleware.locale.LocaleMiddleware',
	 'django.middleware.common.CommonMiddleware',
	 'django.middleware.csrf.CsrfViewMiddleware',
	 'django.contrib.auth.middleware.AuthenticationMiddleware',
	 'hijack.middleware.HijackUserMiddleware',
	 'django.contrib.auth.middleware.RemoteUserMiddleware',
	 'django.contrib.messages.middleware.MessageMiddleware',
	 'django.middleware.clickjacking.XFrameOptionsMiddleware']
MULTICOURSE = False
OPENTA_VERSION = "p1621-20-g3f4af7e1 3f4af7e1 2024-03-11"
PGPASSWORD = os.environ.get("PGPASSWORD", "postgres") 
RATELIMIT_RATE = "2000/1m"
RATE_LIMIT = "2000/1m"
RQ_QUEUES = {'default': {'HOST': 'localhost', 'DB': 0, 'PORT': 6379, 'ASYNC': False, 'DEFAULT_TIMEOUT': 1200}}
RUNTESTS = True
SECRET_KEY = "$$uo0799i74g3oci-wy4_31mmly-nhlzj+qwi@cgr!@ynqmv=("
SESSION_COOKIE_AGE = 1209600
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SETTINGS_MODULE = "backend.settings_test"
STATICFILES_DIRS = (f'{BASE_DIR}/static', f'{BASE_DIR}/static/icons')
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATIC_ROOT = f"{BASE_DIR}/deploystatic"
SUBDOMAIN = "openta"
SUBPROCESS_TIMEOUT = 100
SUPERUSER_PASSWORD = "pw"
SYMPY_CACHE_TIMEOUT = 10
TEMPLATES = [{'DIRS': [f'{BASE_DIR}/templates',
	 f'{BASE_DIR}/opentalti/templates'],
	 'BACKEND': 'django.template.backends.django.DjangoTemplates',
	 'APP_DIRS': True,
	 'OPTIONS': {'context_processors': ['django.template.context_processors.debug',
	 'django.template.context_processors.request',
	 'django.contrib.auth.context_processors.auth',
	 'django.contrib.messages.context_processors.messages']}}]
TIME_BETWEEN_BACKUPS = 10
TRUST_LTI_USER_ID = True
UNITTESTS = True
USE_ETAG = False
VERSION = "NO_VERSION"
VOLUME = "/tmp/subdomain-data"
WEBWORK_LIBRARY = "/subdomain-data/webwork-open-problem-library"
HEADLESS = os.environ.get("HEADLESS", "True") == "True"
LONG_WAIT = int(os.environ.get("LONG_WAIT", "10"))
SHORT_WAIT = int(os.environ.get("SHORT_WAIT", "20"))
WAIT = 4
INCLUDE_MATRIX_BLOCK=True
SAFE_CACHE=True
DEFAULT_QUESTIONSEED = 134
DEFAULT_EXERCISESEED = 134
USE_OTP=False
ALLOW_OTP_ONLY = False
OTP_BYPASS_MAX_AGE = 60 * 60 * 12 
ACTIVITY_WINDOW = 1;
SAMESITE = 'Lax'
LOGIN_RATE_LIMIT = '200/m'
GIT_HASH = 'git_hash'
SIDECAR_URL = os.environ.get("SIDECAR_URL",None)
USE_SIDECAR = os.environ.get('USE_SIDECAR',"False") == True
TARGET_WINDOW = 'openta'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
CHATGPT_TIMEOUT = 30
AI_KEY =  os.environ.get('AI_KEY',os.environ.get('OPENAI_API_KEY',None))
USE_CHATGPT = os.environ.get('USE_CHATPT',False)
AI_MODEL = os.environ.get('AI_MODEL','gpt-4o-mini')
SERVER = os.environ.get("SERVER", OPENTA_SERVER )
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
APP_KEY = os.environ.get('APP_KEY',None)
APP_ID = os.environ.get('APP_ID',None)
USE_MATHPIX = os.environ.get('USE_MATHPIX','False') == 'True'
DJANGO_RAGAMUFFIN_DB = os.environ.get("DJANGO_RAGAMUFFIN_DB",None) 
DATABASES['django_ragamuffin'] = DATABASES['default'];

#DATABASES.update({
#    'django_ragamuffin': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': DJANGO_RAGAMUFFIN_DB,
#        'USER': 'postgres',
#        'PASSWORD': 'postgres',
#        'HOST': 'localhost',
#        'PORT': '5432',
#        'ATOMIC_REQUESTS' : False,
#    }
#})

INSTALLED_APPS.append('django_ragamuffin')
from django_ragamuffin.settings import *
N_ANSWERS = 999
STUDENT_QUERY_INTERVAL = 0
RUNNING_MANAGEMENT_COMMAND = (
    len(sys.argv) > 1
    and sys.argv[0].endswith("manage.py")
)
# STATIC_URL='https://storage.googleapis.com/opentaproject-cdn-bucket/v251005/deploystatic/'
# OK STATIC_URL='https://storage.googleapis.com/opentaproject-cdn-bucket/v251018/deploystatic/'
USE_URKUND = False
STATIC_URL='https://storage.googleapis.com/opentaproject-cdn-bucket/multi/deploystatic/'
TWILIO_SID = os.environ.get('TWILIO_SID', None)
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', None)
TWILIO_TO = os.environ.get('TWILIO_TO',None)
TWILIO_FROM = os.environ.get("TWILIO_FROM",None)
BUG_TO_EMAIL = os.environ.get("BUG_TO_EMAIL",None)
BUG_FROM_EMAIL = os.environ.get("BUG_FROM_EMAIL",None) 
BUG_CC_EMAIL = os.environ.get("BUG_CC_EMAIL",None) 
BASE_SERVER = 'localhost'
AI_KEY=''
USE_EMAIL = False
USE_BUGREPORT = False
#USE_INVITATIONS = False
USE_SMS = False
USE_AUTOTRANSLATIONS = False
