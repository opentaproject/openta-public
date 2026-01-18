# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
import glob
import logging
import uuid
from backend.version import get_version_string

import platform
from backend.settings_static import *
from django.core.management.utils import get_random_secret_key



RUNNING_DEVSERVER = os.environ.get("RUNNING_DEVSERVER", "False").lower() in ('true', '1', 't')
ADMINURL = os.environ.get("ADMINURL", str(uuid.uuid4())[0:7])
ADOBE_ID = os.environ.get("ADOBE_ID", "")
ANSWER_DELAY = int(os.environ.get("ANSWER_DELAY", "0"))
CACHE_FOLDERS = os.environ.get("CACHE_FOLDERS", "True") == "True"
CHECK_DEV_LINEAR_ALGEBRA = os.environ.get("CHECK_DEV_LINEAR_ALGEBRA", "False") == "True"
CHECK_REFERER = os.environ.get("CHECK_REFERER", "True") == "True"
# Use short-lived connections in dev, persistent in non-dev by default
if RUNNING_DEVSERVER:
    CONN_MAX_AGE = int(os.environ.get("CONN_MAX_AGE", 0))
else:
    CONN_MAX_AGE = int(os.environ.get("CONN_MAX_AGE", 240))
DB_NAME = os.environ.get("SUBDOMAIN", "default")
DEBUG = os.environ.get("DEBUG", "False") == "True"
DEBUG_PLUS = os.environ.get("DEBUG_PLUS", False) == "True"
DEEPL_AUTH_KEY = os.environ.get("DEEPL_AUTH_KEY", "")
DO_CACHE = os.environ.get("DO_CACHE", 'True') != "False"
EDITABLE = os.environ.get('EDITABLE',False) == "True"

EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "app-password")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", None)
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO", None)


ENABLE_AUTO_TRANSLATE = os.environ.get("ENABLE_AUTO_TRANSLATE", "False") == "True"
ENV_SOURCE = os.environ.get("ENV_SOURCE", "DEFAULT_FROM_SETTINGS")
FILEBASED_EMAIL = os.environ.get("FILEBASED_EMAIL", "False") == "True"
HANDLER_500 = os.environ.get("HANDLER_500", False) == "True"
HTTP_PROTOCOL          = os.environ.get("HTTP_PROTOCOL","http")
HTTP_SERVER_PORT = os.environ.get("HTTP_SERVER_PORT","8000")
ISRQWORKER = os.environ.get("ISRQWORKER", "True") == "True"
LEVEL = os.environ.get("LEVEL", "WARNING")
MEMCACHEDLOCATION = os.environ.get("MEMCACHEDLOCATION", MEMCACHEDLOCATION)
NODE_NAME = os.environ.get("NODE_NAME", "name-node").split("-")[-1]
PGDATA = os.environ.get('PGDATA', globals().get('PGDATA',None))
PGHOST = os.environ.get('PGHOST', globals().get('PGHOST','localhost'))
PGUSER = os.environ.get('PGUSER', globals().get('PGUSER','postgres'))
PGPASSWORD = os.environ.get('PGPASSWORD', globals().get('PGPASSWORD', 'postgres' ))
OPENTA_SERVER = os.environ.get("OPENTA_SERVER",OPENTA_SERVER);
POD_NAME = os.environ.get("POD_NAME", "name-pod").split("-")[-1]
POD_NUMBER = os.environ.get("POD_NAME", "localhost-0").split("-")[-1]
PORT = os.environ.get("PORT", "")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REFRESH_SEED_ON_CORRECT_ANSWER = os.environ.get("REFRESH_SEED_ON_CORRECT_ANSWER", "True") == "True"
RENDERER_HOST = os.environ.get("WW_RENDERER_SERVICE_HOST", "localhost")
RUNNING_DEVSERVER = os.environ.get("RUNNING_DEVSERVER", "False") == "True"
RUNNING_DEVSERVER = os.environ.get("RUNNING_DEVSERVER", "False").lower() in ('true', '1', 't')
RUNTESTS = os.environ.get("DJANGO_SETTINGS_MODULE", False) == "backend.settings_test"
SECURE_CONTENT_TYPE_NOSNIFF = os.environ.get("SECURE_CONTENT_TYPE_NOSNIFF", False) == "True"
SHOW_TIMING = os.environ.get("SHOW_TIMING", False) == "True"
SOCKET_CONNECT_TIMEOUT = int(os.environ.get("SOCKET_CONNECT_TIMEOUT", 5))
SOCKET_TIMEOUT = int(os.environ.get("SOCKET_CONNECT_TIMEOUT", 300))
STATIC_URL = os.environ.get("STATIC_URL", '/static/')
SUBDOMAIN = os.environ.get("SUBDOMAIN", "")
SUBDOMAIN_DATA = os.environ.get("SUBDOMAIN_DATA ", "subdomain-data")
SUBPROCESS_TIMEOUT = os.environ.get("SUBPROCESS_TIMEOUT", 30)
SUPERUSER_PASSWORD = os.environ.get("SUPERUSER_PASSWORD","")
SYMPY_CACHE_TIMEOUT = int(os.environ.get("SYMPY_CACHE_TIMEOUT ", "300"))
month_in_seconds = 60 * 60 * 24 * 30
TIME_BETWEEN_BACKUPS = os.environ.get("TIME_BETWEEN_BACKUPS", month_in_seconds)
TRUST_LTI_USER_ID = os.environ.get("TRUST_LTI_USER_ID", False) == "True"
USE_ACCEL_REDIRECT = os.environ.get("USE_ACCEL_REDIRECT", "False") == "True"
USE_CUSTOM_SMTP_EMAIL = os.environ.get("USE_CUSTOM_SMTP_EMAIL", True)
USE_DEEPL = os.environ.get("USE_DEEPL", False) == "True"
USE_DEVTOOLS = os.environ.get("USE_DEVTOOLS", False) == "True"
if RUNNING_DEVSERVER :
    USE_GMAIL = os.environ.get("USE_GMAIL", "False") == "True"  # DEFAULT TO FALSE FOR DEV
else :
    USE_GMAIL = os.environ.get("USE_GMAIL", "True") == "True"  # DEFAULT TO TRUE FOR PRODUCTION
USE_INVITATIONS = os.environ.get("USE_INVITATIONS", "True") == "True"
USE_JSON_CACHE = os.environ.get("USE_JSON_CACHE", False) == "True"
USE_VITE = os.environ.get("USE_VITE", "True" ) == "True"
VERSION = os.environ.get("VERSION", "")
SERVER = os.environ.get("SERVER", "localhost:8000")
RUNNING_DEVSERVER = os.environ.get("RUNNING_DEVSERVER", "False").lower() in ('true', '1', 't')
ATOMIC_REQUESTS = False



ISRQWORKER = os.environ.get("ISRQWORKER", "True") == "True"
DB_NUMBER = 1 + int(POD_NUMBER)
DB_NUMBER = os.environ.get("DB_NUMBER", DB_NUMBER)
# Default to handling queue tasks in main thread


RQ_QUEUES = {
    "default": {
        "HOST": REDIS_HOST,
        "DB": DB_NUMBER,
        "PORT": REDIS_PORT,
        "ASYNC": True,
        "DEFAULT_TIMEOUT": 20 * 60,
    }
}


CSRF_TRUSTED_ORIGINS = ['https://*', 'http://*', 'http://*.localhost:3000', 'http://localhost:3000', 'http://canary.localhost:*', 'http://127.0.0.1:3000', 'http://*.localhost:3200', 'http://localhost:3200', 'http://127.0.0.1:3200', 'http://[::1]:8000', 'http://localhost:8000', 'http://*.localhost', 'https://*.localhost']


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
        'LOCATION': MEMCACHEDLOCATION,
        "TIMEOUT": 100,
        "OPTIONS": {
            'binary': True,
            "behaviors": {
                "cas": False,  # <-- critical line
                "tcp_nodelay": True,
                "ketama": True,
                },
            #'use_pooling': True,
            }
    },
    "aggregation": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": [f"redis://{REDIS_HOST}:{REDIS_PORT}/1"],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "MAX_ENTRIES": "10000",
            # "SOCKET_CONNECT_TIMEOUT": SOCKET_CONNECT_TIMEOUT,
            # "SOCKET_TIMEOUT": SOCKET_TIMEOUT,
        },
        "TIMEOUT": None,
        "KEY_PREFIX": "aggregation",
    },
    "imagekit": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/subdomain-data/CACHE/imagekit",
        "TIMEOUT": None,
        "OPTIONS": {"MAX_ENTRIES": 30000},
    },
}

POSTGRES_DEFAULT_DB= os.environ.get('POSTGRES_DEFAULT_DB',None)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DEFAULT_DB,
        "USER": PGUSER,
        "PASSWORD": PGPASSWORD,
        "HOST": PGHOST,
        "PORT": 5432,
        "ATOMIC_REQUESTS": ATOMIC_REQUESTS,
        "CONN_MAX_AGE": CONN_MAX_AGE,
    },
    "sites": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sites",
        "USER": PGUSER,
        "PASSWORD": PGPASSWORD,
        "HOST": PGHOST,
        "PORT": 5432,
        "ATOMIC_REQUESTS": ATOMIC_REQUESTS,
        "CONN_MAX_AGE": CONN_MAX_AGE,
    },
    "opentasites": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "opentasites",
        "USER": PGUSER,
        "PASSWORD": PGPASSWORD,
        "HOST": PGHOST,
        "PORT": 5432,
        "ATOMIC_REQUESTS": ATOMIC_REQUESTS,
        "CONN_MAX_AGE": CONN_MAX_AGE,
    },
}

GOOGLE_AUTH_STRING_EXISTS = os.path.isfile("/subdomain-data/auth/google_auth_string.txt")
CACHES["translations"] = {
    "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
    "LOCATION": "%s/translations_cache" % VOLUME,
    "TIMEOUT": None,
    "OPTIONS": {"MAX_ENTRIES": 30000},
}

if platform.system() == "Darwin":
    PG_DUMP_BINARY = "/usr/local/opt/postgresql/bin/pg_dump"
    DB_BACKUP = "./osx_db_backup"
    DB_CREATECOURSE = "./osx_db_createcourse"
    DB_PURGE = "./osx_db_purge"
    DB_RESTORE = "./osx_db_restore"
DEBUG = os.environ.get("DEBUG", "False") == "True"
CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS + [ f"http://*.{OPENTA_SERVER}", f"https://*.{OPENTA_SERVER}", ]
SECRET_KEY =globals().get('SECRET_KEY',os.environ.get('SECRET_KEY','abcddfghijklmnopqrst'))
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND","django.core.mail.backends.filebased.EmailBackend")
if RUNNING_DEVSERVER:
    EMAIL_FILE_PATH = "/tmp"
    PORT = ":8000"
    USE_ACCEL_REDIRECT = False
    STATIC_URL = "/static/"
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    STATIC_URL = "/static/"
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    ADMINURL = "administration/"
    BLOCK_EMAIL_AUDITS = False
EMAIL_PORT = int( os.environ.get("EMAIL_PORT","587") )
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS","True") == "True"
PG_DUMP_BINARY = "/usr/bin/pg_dump"
DB_BACKUP = "./db_backup"
DB_CREATECOURSE = "./db_createcourse"
DB_PURGE = "./db_purge"
DB_RESTORE = "./db_restore"
if platform.system() == "Darwin":
    PG_DUMP_BINARY = "/usr/local/opt/postgresql/bin/pg_dump"
    DB_BACKUP = "./osx_db_backup"
    DB_CREATECOURSE = "./osx_db_createcourse"
    DB_PURGE = "./osx_db_purge"
    DB_RESTORE = "./osx_db_restore"
WW_PROTOCOL=os.environ.get("WW_PROTOCOL",HTTP_PROTOCOL)
WW_PORT = os.environ.get("WW_PORT", "443" if WW_PROTOCOL == "https" else ( "8000" if OPENTA_SERVER == "localhost" else "80" ))
DBHOST=os.environ.get("DB_SERVER_SERVICE_HOST", os.environ.get("PGHOST",os.environ.get("DBHOST","localhost")))
SAFE_CACHE=os.environ.get("SAFE_CACHE",'False') == 'True'
DEFAULT_QUESTIONSEED = 134
DEFAULT_EXERCISESEED = 134
WOLFRAM_ENGINE = f"http://" + os.environ.get('WOLFRAM_ENGINE_SERVICE_HOST', 'localhost:8090')
USE_OTP = os.environ.get("USE_OTP", "False") == "True"
USE_URKUND =  os.environ.get("USE_URKUND", "False") == "True"
ALLOW_OTP_ONLY = False
OTP_BYPASS_MAX_AGE = 0
NO_OTP_FOR_SUPER = True
EMAIL_TIMEOUT = 10
if USE_OTP :
    AUTHENTICATION_BACKENDS = ['opentalti.apps.LTIAuth', 'django.contrib.auth.backends.ModelBackend' , 'twofactor.views.twofactorauth','users.models.AnonymousPermissions']
    ALLOW_OTP_ONLY = os.environ.get("ALLOW_OTP_ONLY", "False") == "True" # HAS BEEN COMMENTED OUT IN otp/views.py
    OTP_BYPASS_MAX_AGE =  int( os.environ.get("OTP_BYPASS_MAX_AGE", 10 )  )

SAFE_IP = []
ACTIVITY_WINDOW = os.environ.get("ACTIVITY_WINDOW","300")
LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT","20/m")
REGRADE_DIR = "/subdomain-data/regrade"
