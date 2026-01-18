# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
import glob
import logging
import uuid

logger = logging.getLogger(__name__)
import platform
import subprocess


PGHOST = "localhost"
PGUSER = "postgres"
ADMINURL = "administration"
ADOBE_ID = ""
ALLOWED_HOSTS = ['*']
ALLOW_JSON_INVITES = True
ALL_DATABASES = {}
ANSWER_DELAY = 0
ANYMAIL = False
APPEND_SLASH = True
ASGI_APPLICATION = "backend.asgi.application"
ASSET_WHITELIST = ['127.0.0.1', '::1', 'localhost', 'localhost']
AUTHENTICATION_BACKENDS = ['opentalti.apps.LTIAuth', 'django.contrib.auth.backends.ModelBackend' , 'users.models.AnonymousPermissions']
AUTH_PASSWORD_VALIDATORS = []
AUTOTRANSLATE_TRANSLATOR_SERVICE = "autotranslate.services.GoogleAPITranslatorService"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_LENGTH = 300
BLOCK_EMAIL_AUDITS = False
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache', 'LOCATION': 'localhost:11211', 'TIMEOUT': 10}, 'aggregation': {'BACKEND': 'django_redis.cache.RedisCache', 'LOCATION': ['redis://localhost:6379/1'], 'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient', 'MAX_ENTRIES': '10000'}, 'TIMEOUT': None, 'KEY_PREFIX': 'aggregation'}, 'imagekit': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache', 'LOCATION': '/subdomain-data/CACHE/imagekit', 'TIMEOUT': None, 'OPTIONS': {'MAX_ENTRIES': 30000}}, 'translations': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache', 'LOCATION': '/subdomain-data/translations_cache', 'TIMEOUT': None, 'OPTIONS': {'MAX_ENTRIES': 30000}}}
CACHE_FOLDERS = True
CACHE_LIFETIME = 900
CHECK_AGGREGATIONS = False
CHECK_DEV_LINEAR_ALGEBRA = False
CHECK_REFERER = False
CONN_HEALTH_CHECKS = False
CONN_MAX_AGE = 0
CSRF_COOKIE_NAME = "csrftokenv1600"
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"
CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*', 'http://*.localhost:3000', 'http://localhost:3000', 'http://canary.localhost:*', 'http://127.0.0.1:3000', 'http://*.localhost:3200', 'http://localhost:3200', 'http://127.0.0.1:3200', 'http://[::1]:8000', 'http://localhost:8000', 'http://*.localhost', 'https://*.localhost']
DATABASE_ROUTERS = ['backend.routers.AuthRouter']
DATA_UPLOAD_MAX_MEMORY = 52428800
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
DB_BACKUP = "./osx_db_backup"
DB_CREATECOURSE = "./osx_db_createcourse"
DB_NUMBER = 13
DB_PURGE = "./osx_db_purge"
DB_RESTORE = "./osx_db_restore"
DEBUG = True
DEBUG_PLUS = True
DEEPL_AUTH_KEY = ""
DEEPL_DOMAIN = "api-free.deepl.com"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
DEFAULT_FROM_EMAIL = "webmaster@localhost"
DEFAULT_QUESTION_TYPE = "basic"
DEFAULT_SITE_ID = 1
DELETE_ANONYMOUS_STUDENT_ON_LOGOUT = True
DONT_REPLY_EMAIL = "opentaproject@gmail.com"
DO_CACHE = True
DO_CACHE_EXERCISE_XML = False
EDITABLE = False
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_BACKLOG = 48
EMAIL_FILE_PATH = "/tmp"
EMAIL_HOST = "localhost"
EMAIL_HOST_PASSWORD = ""
EMAIL_HOST_USER = ""
EMAIL_USE_TLS = True
EMAIL_PORT = 25
EMAIL_REPLY_TO = "info@opentaproject.com"
ENABLE_AUTO_TRANSLATE = True
ENFORCE_ONTIME = False
ENV_SOURCE = "DEFAULT_FROM_SETTINGS"
ESCALATE_FIRST_ANONYMOUS_USER_TO_ADMIN = False
EXERCISES_IMPORT_FILE_SIZE_LIMIT = 3000000000
FILEBASED_EMAIL = True
FILE_UPLOAD_HANDLERS = ['django.core.files.uploadhandler.TemporaryFileUploadHandler']
FILE_UPLOAD_PERMISSIONS = 420
FIX_XML = True
FORCE_ROLE_TO_STUDENT = True
GONE_ON_ACCEPT_ERROR = False
GOOGLE_AUTH_STRING_EXISTS = False
HANDLER_500 = False
HELP_URL = "https://opentaproject.com"
HIJACK_ALLOW_GET_REQUESTS = True
HIJACK_AUTHORIZE_STAFF = True
HIJACK_INSERT_BEFORE = "</form>"
HIJACK_PERMISSION_CHECK = "hijack.permissions.superusers_and_staff"
HTDOCS_TMP = ""
HTTP_PROTOCOL = "http"
HTTP_SERVER_PORT = "8000"
IGNORE_NOFEEDBACK = False
IGNORE_NO_FEEDBACK = False
IMAGEKIT_CACHEFILE_DIR = "CACHE/"
IMAGEKIT_CACHE_BACKEND = "imagekit"
IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = "imagekit.cachefiles.backends.Simple"
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = "backend.cache_strategy.CustomStrategy"
IMAGEKIT_SPEC_CACHEFILE_NAMER = "backend.cache_strategy.my_source_name_as_path"
INSTALLED_APPS = ['daphne', 'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'django.contrib.sites', 'rest_framework', 'exercises.apps.ExercisesConfig', 'course.apps.CourseConfig', 'users.apps.UsersConfig', 'workqueue.apps.WorkqueueConfig', 'widget_tweaks', 'django_extensions', 'django_rq', 'imagekit', 'hijack', 'import_export', 'autotranslate', 'translations', 'aggregation', 'opentalti', 'django_json_widget', 'invitations', 'myinvitations']
INVITATIONS_ADAPTER = "myinvitations.adapters.BaseInvitationsAdapter"
INVITATIONS_SIGNUP_REDIRECT = "/login"
ISRQWORKER = True
LANGUAGE_CODE = "en"
LANGUAGE_COOKIE_NAME = "lang"
LEVEL = "ERROR"
LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

LOGGING = {'version': 1, 'disable_existing_loggers': False, 
           'formatters': {\
                'verbose': {'format': 'verbose %(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'}, \
                'middle': {'format': 'middle %(levelname)s %(asctime)s %(module)s %(process)d %(filename)s %(funcName)s [%(message)s]'}, \
                'simple': {'format': 'simple %(levelname)s %(message)s'}, \
                'console': {'format': 'console %(asctime)s.%(msecs)03d %(levelname)-5.5s %(filename)s:%(lineno)s [%(funcName)s]  %(message)s', 'datefmt': '%H:%M:%S'}}, \
            'handlers': { \
                'console': {'level': LEVEL , 'class': 'logging.StreamHandler', 'formatter': 'console'}, \
                'stderr': {'level':  LEVEL , 'class': 'logging.StreamHandler', 'formatter': 'middle'}, \
                'file': {'level':    LEVEL , 'class': 'logging.handlers.RotatingFileHandler', 'backupCount': 4, 'maxBytes': 5242880, 'filename': '/tmp/logfile', 'formatter': 'middle'}},\
            'root': {\
                'handlers': ['console'], 'level': LEVEL }, \
            'loggers': {\
                'werkzeug': {'handlers': ['console'], 'level': LEVEL , 'propagate': False }, \
                'django': {'handlers': ['file', 'stderr'], 'level':  LEVEL , 'propagate': False}, \
                'exercises.questiontypes': {'handlers': ['console'], 'level':  LEVEL , 'propagate': False}, \
                'backend.views': {'handlers': ['console'], 'level':  LEVEL , 'propagate': False},  \
                'workqueue': {'handlers': ['console'], 'level': LEVEL , 'propagate': False }}}
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"
MAIN_CACHE_TIMEOUT = 3600
MAKE_GLOBALNODE_NONEMPTY = True
MAX_ASSET_UPLOAD_SIZE = 200000000.0
MEDIA_ROOT = "/subdomain-data"
MEDIA_TAG = "media"
MEDIA_URL = "/media/"
MEMCACHEDLOCATION = "127.0.0.1:11211"
MIDDLEWARE = [
            'backend.middleware.DynamicSiteDomainMiddleware',  # ADDED THIS TO GET IN THERE FIRST WITH CONNECTION
            'django.middleware.common.CommonMiddleware', 
            'backend.middleware.SameSiteMiddleware', 
            #'backend.middleware.SubpathMiddleware', 
            #'backend.middleware.DynamicSiteDomainMiddleware', 
            'django.middleware.security.SecurityMiddleware', 
            'django.contrib.sessions.middleware.SessionMiddleware', 
            'backend.middleware.SetBasicSessionVars',  
            'whitenoise.middleware.WhiteNoiseMiddleware', 
            'django.middleware.locale.LocaleMiddleware', 
            'django.middleware.csrf.CsrfViewMiddleware', 
            'django.contrib.auth.middleware.AuthenticationMiddleware', 
            'django.contrib.messages.middleware.MessageMiddleware', 
            'django.middleware.clickjacking.XFrameOptionsMiddleware', 
            'hijack.middleware.HijackUserMiddleware',
            'django_ratelimit.middleware.RatelimitMiddleware',
            'backend.middleware.maintenance.MaintenanceMiddleware',
            ]
MULTICOURSE = True
NEW_FOLDER = "0:New"
NEW_LOGGING = {'version': 1, 'filters': {'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'}}, 'handlers': {'console': {'level': 'DEBUG', 'filters': ['require_debug_true'], 'class': 'logging.StreamHandler'}}, 'loggers': {'django.db.backends': {'level': 'DEBUG', 'handlers': ['console']}}}
NODE_NAME = "node"
OPENTA_SERVER = "localhost"
OPENTA_VERSION = "p1621-6-gcb81589c cb81589c 2024-03-09-pod-node-pod-node"
OPTIMIZE_COMPARE = False
OS = "OSX"
PGHOST = "localhost"
PGUSER = "postgres"
PG_DUMP_BINARY = "/usr/local/opt/postgresql/bin/pg_dump"
POD_NAME = "pod"
POD_NUMBER = "0"
PORT = ":8000"
RATELIMIT_RATE = "20/120s"
RATE_LIMIT = "5/m"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REFRESH_SEED_ON_CORRECT_ANSWER = True
REGRADE_DIR = "/tmp/regrade"
RENDERER_HOST = "localhost"
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework.authentication.SessionAuthentication',), 'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',)}
ROOT_URLCONF = "backend.urls"
RQ_QUEUES = {'default': {'HOST': 'localhost', 'DB': 13, 'PORT': 6379, 'ASYNC': True, 'DEFAULT_TIMEOUT': 1200}}
RUNNING_DEVSERVER = True
RUNTESTS = False
SAFE_RUN_TIMEOUT = 2
SAFE_SUMMARY_CACHE_LIFETIME = 560
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_SECONDS = 0
SECURE_SSL_REDIRECT = False
SERIALIZE_EXERCISE_DATA_FOR_COURSE_TIMEOUT = None
SERIALIZE_EXERCISE_WITH_QUESTION_DATA = None
SERVER = "localhost:8000"
SESSION_COOKIE_AGE = 604800
SESSION_COOKIE_NAME = "sessionidv1600"
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SETTINGS_MODULE = "backend.settings"
SHOW_TIMING = False
SITE_ID = 3
SOCKET_CONNECT_TIMEOUT = 5
SOCKET_TIMEOUT = 300
SPOOL_DIR = "workqueue/"
#STATICFILES_STORAGE = "compress_staticfiles.storage.CompressStaticFilesStorage"
STATIC_ROOT = os.path.join(BASE_DIR, "deploystatic")
STATIC_TAG = "static"
STATIC_URL = "/static/"
STATICFILES_DIRS = ( os.path.join( BASE_DIR, "static",), os.path.join( BASE_DIR, "static/icons",),)

STATISTICS_CACHE_TIMEOUT = 300
STUDENTS_STATISTICS_CACHE_TIMEOUT = 300
SUBDOMAIN_DATA = ""
SUBPATH = ""
SUBPATH_REGEX = False
SUBPROCESS_TIMEOUT = 10
SUPERUSER_PASSWORD = ""
SYMPY_CACHE_TIMEOUT = 300
TEMPLATES = [
    {
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
TEMPLATES[0]["DIRS"].append(os.path.join(BASE_DIR, "opentalti", "templates"))
TIME_BETWEEN_BACKUPS = 2592000
TIME_ZONE = "Europe/Stockholm"
TMPDIR = "/subdomain-data/deleted"
TRASH_FOLDER = "z:Trash"
TRUST_LTI_USER_ID = False
UNITTESTS = False
USE_ACCEL_REDIRECT = False
USE_DEEPL = False
USE_DEVTOOLS = True
USE_ETAG = True
USE_EXERCISES_CACHE = False
USE_GMAIL = False
USE_I18N = True
USE_INVITATIONS = True
USE_JSON_CACHE = False
USE_L10N = True
USE_MAIL = False
USE_MAILGUN = False
USE_RESULTS_CACHE = True
USE_STARS = False
USE_TZ = True
USE_VITE = True
VALIDATE_GOOGLE_AUTH_STRING = True
VALIDATE_IDENTIFIER = False
VALID_ROLES = ['ContentDeveloper', 'Learner', 'Student', 'Instructor', 'Observer', 'AnonymousStudent', 'Guest', 'TeachingAssistant']
VERSION = ""
VOLUME = "/subdomain-data"
WEBWORK_LIBRARY = ""
WOLFRAM_ENGINE = ""
WSGI_APPLICATION = "backend.wsgi.application"
X_FRAME_OPTIONS = "SAMEORIGIN"
DB_NUMBER = 12
COMPUTER_SESSION_TIMEOUT = 3600 * 24 ;
RATELIMIT_VIEW = 'backend.views.ratelimit_error';
