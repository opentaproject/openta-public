# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
import glob
import logging
import uuid
import re
import sys

logger = logging.getLogger(__name__)
import platform
import subprocess

from backend.settings_local import *
STATICFILES_STORAGE = "compress_staticfiles.storage.CompressStaticFilesStorage"
#if os.path.exists("/settings_private2.py") :
#    from backend.settings_private import *

"""
Optionally load a Python secrets file into the settings namespace.

How it works:
- If `DJANGO_SECRETS_FILE` (or `SECRETS_FILE`) env var is set and points
  to a readable file, execute it and inject any UPPERCASE names.
- Otherwise, if `backend/settings_secrets.py` exists, load from there.

The secrets file should contain plain Python assignments like:

    SECRET_VARIABLE1 = 'abc'
    SECRET_VARIABLE2 = 123

This runs after importing local/private settings so secrets override them
and are available to the rest of this module.
"""
DJANGO_SECRETS_FILE = os.environ.get( 'DJANGO_SECRETS_FILE',None)
if bool( DJANGO_SECRETS_FILE) and os.path.exists( DJANGO_SECRETS_FILE) :
    secrets_path = DJANGO_SECRETS_FILE 
else :
    secrets_path = None
UPPER_UNDER = re.compile(r'^[A-Z0-9_]+$')


def load_secrets() :
    try:
        import runpy
    
        if secrets_path and os.path.isfile(secrets_path):
            _secrets = runpy.run_path(secrets_path)
            for _k, _v in _secrets.items():
                if bool(UPPER_UNDER.fullmatch(_k)) :
                    print(f"LOAD {_k} = {_v}")
                    globals()[_k] = _v
            logger.error(f"Loaded secrets from {secrets_path}")
        else :
            logger.error(f"FILE = {DJANGO_SECRETS_FILE} SECRETS_PATH = {secrets_path}")
    except Exception as _e:
        logger.warning(f"Failed to load secrets file: {_e}")

load_secrets()
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies"
INCLUDE_MATRIX_BLOCK = False
COMPUTER_SESSION_TIMEOUT = 60 * 60 
#SAFE_IP = ['98.128.246.120']
SAMESITE = 'None'
RATELIMIT_VIEW='backend.views.ratelimit_error'
RATE_LIMIT = "5/m"
logger.error(f"BASE_DIR = {BASE_DIR}")
GIT_DIR = '/'.join( BASE_DIR.split('/')[0:-3] )+"/.git"
OPENTA_VERSION = get_version_string(GIT_DIR)
try :
    GIT_HASH = subprocess.check_output(["/usr/bin/git", '-C',GIT_DIR,"rev-parse", "--short", "HEAD"]).decode('utf-8').strip()
except :
    GIT_HASH = 'GIT_HASH'
logger.error(f"GIT_HASH = {GIT_HASH}")
SIDECAR_URL = os.environ.get('SIDECAR_URL',False) and ( os.environ.get('USE_SIDECAR_URL','False') == 'True')
USE_SIDECAR = SIDECAR_URL != None
TARGET_WINDOW = os.environ.get("TARGET_WINDOW",'openta')
CSRF_TRUSTED_ORIGINS = [
    'https://www.openta.se',
    'http://*.localhost:8080',
    'https://instructure.com',
    'https://*.instructure.com',
    'http://127.0.0.1:8000',
    'https://*',
    'http://*',
    'http://localhost:3200',
]
CHATGPT_TIMEOUT = 240
MAXWAIT = globals().get('MAXWAIT',  os.environ.get('MAXWAIT', 120 ) )
AI_MODEL = os.environ.get('AI_MODEL','gpt-5-mini')
SERVER = os.environ.get("SERVER", OPENTA_SERVER )
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
#print(f"CACHES = {CACHES}")
#print(f"SESSION = {SESSION_ENGINE}")
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
#NOCACHES = {};
#NOCACHES['default'] =  {
#        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",  # uses pure Python
#        "LOCATION": "memcached:11211",
#    }
#NOCACHES['default']  = {
#        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
#        'LOCATION': 'memcached:11211',
#        'OPTIONS': {
#            'binary': True,
#            'behaviors': {
#                'tcp_nodelay': True,
#                'tcp_keepalive': True,
#                'connect_timeout': 2000,  # milliseconds
#                'send_timeout': 750 * 1000,
#                'receive_timeout': 750 * 1000,
#                'retry_timeout': 2,        # seconds before retrying downed server
#                'dead_timeout': 10,        # seconds to mark server as "dead"
#            },
#        },
#    }
CACHES['default']  = {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": ["127.0.0.1:11211"],  # or "memcached:11211" in Docker/K8s
        "TIMEOUT": 300,  # Key TTL in seconds (None = never expire)
        "OPTIONS": {
            # Connection pooling
            "use_pooling": True,
            "max_pool_size": 10,

            # Network timeouts (in seconds)
            "connect_timeout": 2,   # TCP connection timeout
            "timeout": 2,           # Read/write timeout

            # TCP options
            "no_delay": True,       # Disable Nagle’s algorithm (faster small writes)
            #"tcp_keepalive": True,  # Keep connections alive

            # Error handling
            "ignore_exc": False,    # Raise errors instead of silently ignoring them
        },
    }


N_ANSWERS = 999
DJANGO_RAGAMUFFIN_DB = globals().get('DJANGO_RAGAMUFFIN_DB',os.environ.get('DJANGO_RAGAMUFFIN_DB',None))
#os.environ['DJANGO_RAGAMUFFIN_DB'] = str( DJANGO_RAGAMUFFIN_DB  ) # MAKE DJANGO_RAGAMUFFIN_DB AVAILABLE TO DJANGO_RAGAMUFFIN
DATABASE_ROUTERS = [ 'backend.routers.AuthRouter']
STUDENT_QUERY_INTERVAL = 0
SAFE_RUN_TIMEOUT = 120
EFFORT = 'medium'
RUNNING_MANAGEMENT_COMMAND = (
    len(sys.argv) > 1
    and sys.argv[0].endswith("manage.py")
    and not 'runserver' in sys.argv[1]
)
if RUNNING_DEVSERVER :
    STATIC_URL = "/static/"
else :
    STATIC_URL='https://storage.googleapis.com/opentaproject-cdn-bucket/multi/deploystatic/'
#else :
#    CACHES["default"] =  {
#        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
#        "LOCATION": "django_cache",     # table name
#        "TIMEOUT": 300,                  # seconds; None = never expire
#        "OPTIONS": {
#            "MAX_ENTRIES": 30000,        # default 300, increase to avoid pruning
#            "CULL_FREQUENCY": 3,         # 1/3 of entries deleted when MAX_ENTRIES is hit
#        },
#        }
USE_URKUND = False
ADOBE_ID = globals().get('ADOBE_ID',  os.environ.get('ADOBE_ID', None) )
OPENAI_UPLOAD_STORAGE = '/subdomain-data/query'
#TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', None)
#TWILIO_TO = os.environ.get('TWILIO_TO',None)
#TWILIO_FROM = os.environ.get("TWILIO_FROM",None)
#BUG_TO_EMAIL = os.environ.get("BUG_TO_EMAIL",None)
#BUG_FROM_EMAIL = os.environ.get("BUG_FROM_EMAIL",None) 
#BUG_CC_EMAIL = os.environ.get("BUG_CC_EMAIL",None) 
BUG_FROM_EMAIL = globals().get('BUG_FROM_EMAIL',os.environ.get('BUG_FROM_EMAIL',None))
BUG_CC_EMAIL = globals().get('BUG_CC_EMAIL',os.environ.get('BUG_CC_EMAIL',None))
BUG_TO_EMAIL = globals().get('BUG_TO_EMAIL',os.environ.get('BUG_TO_EMAIL',None))
DJANGO_SUPERUSER_EMAIL = globals().get('DJANGO_SUPERUSER_EMAIL',os.environ.get('DJANGO_SUPERUSER_EMAIL',None))
DOCKER_EMAIL = globals().get('DOCKER_EMAIL',os.environ.get('DOCKER_EMAIL',None))
DOCKER_PASSWORD = globals().get('DOCKER_PASSWORD',os.environ.get('DOCKER_PASSWORD',None))
DOCKER_USERNAME = globals().get('DOCKER_USERNAME',os.environ.get('DOCKER_USERNAME',None))
EMAIL_HOST_PASSWORD = globals().get('EMAIL_HOST_PASSWORD',os.environ.get('EMAIL_HOST_PASSWORD',None))
KEYFILE = globals().get('KEYFILE',os.environ.get('KEYFILE',None))
OPENAI_API_KEY = globals().get('OPENAI_API_KEY',os.environ.get('OPENAI_API_KEY',None))
OPENAI_ORG_ID = globals().get('OPENAI_ORG_ID',os.environ.get('OPENAI_ORG_ID',None))
DEFAULT_TEMPERATURE = globals().get('DEFAULT_TEMPERATURE',os.environ.get('DEFAULT_TEMPERATURE',None))
OPENAI_PROJECT_ID = globals().get('OPENAI_PROJECT_ID',os.environ.get('OPENAI_PROJECT_ID',None))
APP_KEY = globals().get('APP_KEY',os.environ.get('APP_KEY',None))
APP_ID = globals().get('APP_ID',os.environ.get('APP_ID',None))
#SUPERUSER = os.environ.get('SUPERUSER') or (SUPERUSER if 'SUPERUSER' in globals() else None)
SUPERUSER = 'super'
SUPERUSER_PASSWORD = os.environ.get('SUPERUSER_PASSWORD') or (SUPERUSER_PASSWORD if 'SUPERUSER_PASSWORD' in globals() else None)
LOCK_SUPER = os.environ.get('LOCK_SUPER','False') == 'True' or (LOCK_SUPER if 'LOCK_SUPER' in globals() else  False )


TWILIO_FROM = globals().get('TWILIO_FROM',os.environ.get('TWILIO_FROM',None))
TWILIO_SID = globals().get('TWILIO_SID',os.environ.get('TWILIO_SID',None))
TWILIO_TO = globals().get('TWILIO_TO',os.environ.get('TWILIO_TO',None))
TWILIO_TOKEN = globals().get('TWILIO_TOKEN',os.environ.get('TWILIO_TOKEN',None))
OAUTH_SECRET = globals().get('OAUTH_SECRET',os.environ.get('OAUTH_SECRET',None))
EMAIL_HOST = globals().get('EMAIL_HOST',os.environ.get('EMAIL_HOST',None))
EMAIL_HOST_PASSWORD = globals().get('EMAIL_HOST_PASSWORD',os.environ.get('EMAIL_HOST_PASSWORD',None))
EMAIL_HOST_USER = globals().get('EMAIL_HOST_USER',os.environ.get('EMAIL_HOST_USER',None))
EMAIL_REPLY_TO = globals().get('EMAIL_REPLY_TO',os.environ.get('EMAIL_REPLY_TO',None))
BASE_SERVER = globals().get('BASE_SERVER',os.environ.get('BASE_SERVER','localhost'))

USE_MATHPIX = os.environ.get('USE_MATHPIX','False') == 'True'
if APP_KEY == None or APP_ID == None :
    USE_MATHPIX = False
is_rqworker = any(arg.endswith("rqworker") or arg == "rqworker" for arg in sys.argv)
USE_CHATGPT = ( os.environ.get('USE_CHATGPT' , 'False' ) == 'True'  or is_rqworker )  and bool( OPENAI_API_KEY ) and bool( OPENAI_PROJECT_ID )
# ALWAYS GET SUPERUSER PASSWORD FROM ENVIRONMENT
APP_DIRS = True
AI_KEY = OPENAI_API_KEY

#print(f"SUPERUSER_PASSWORD = {SUPERUSER_PASSWORD}")
#print(f"SUPERUSER = {SUPERUSER}")
#print(f"OPENTA_VERSION = {OPENTA_VERSION}")
#print(f"OPENAI_API_KEY = {OPENAI_API_KEY}")
#print(f"AI_KEY = {AI_KEY}")
print(f"USE_CHATGPT1 = {USE_CHATGPT}")
if bool( OPENAI_ORG_ID) and  bool( OPENAI_API_KEY) and bool( OPENAI_PROJECT_ID) and bool( AI_KEY) and  USE_CHATGPT :
    INSTALLED_APPS.append('django_ragamuffin')
    from django_ragamuffin.settings import *
    DATABASE_ROUTERS = [ 'django_ragamuffin.db_routers.RagamuffinRouter','backend.routers.AuthRouter']
else :
    USE_CHATGPT = False


VALIDATE_GOOGLE_AUTH_STRING = False
USE_SMS = os.environ.get('USE_SMS','True') == 'True'  and bool( TWILIO_FROM) and bool( TWILIO_SID) and bool( TWILIO_TO) and bool( TWILIO_TOKEN )
USE_EMAIL =  os.environ.get('USE_EMAIL', "True" ) == 'True' and bool( EMAIL_HOST ) and bool( EMAIL_HOST_USER) and bool( EMAIL_HOST_PASSWORD) and bool( EMAIL_REPLY_TO)
USE_AUTOTRANSLATIONS = os.environ.get("USE_AUTORANSLATIONS", "True" ) == "True" and bool( KEYFILE) and os.path.exists( KEYFILE) 
USE_INVITATIONS =  os.environ.get("USE_INVITATIONS","True") == "True"  and USE_EMAIL
USE_BUGREPORT = os.environ.get("USE_BUGREPORT", "True")  == "True" and USE_EMAIL and bool( BUG_CC_EMAIL) and bool( BUG_FROM_EMAIL ) and bool( BUG_TO_EMAIL ) 
ENABLE_AUTO_TRANSLATE = USE_AUTOTRANSLATIONS  # legacy
if os.environ.get('USE_LOCMEM', 'False' ) == 'True':
     CACHES['default'] = { "BACKEND": "django.core.cache.backends.locmem.LocMemCache", }

ADOBE_IDS =  globals().get('ADOBE_IDS', {} )
if ADOBE_IDS :
    ADOBE_ID = ADOBE_IDS.get(OPENTA_SERVER,os.environ.get('ADOBE_ID',None ) )

assert SUPERUSER_PASSWORD , 'SUPERUSER PASSWORD NOT SET'
assert SUPERUSER , 'SUPERUSER NOT SET'
print(f"SUPERUSER = {SUPERUSER}")
print(f"SUPERUSER_PASSWORD = {SUPERUSER_PASSWORD}")
print(f"USE_CHATGPT2 = ", USE_CHATGPT)
print(f"OPENTA_VERSION = {OPENTA_VERSION}")
CHUNK_SIZE = 2 * 5242880
if False and RUNNING_DEVSERVER :
    LOGGING.update({
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "rq.worker": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "django_rq": {
                "handlers": ["console"],
                "level": "INFO",
            },
        },
        })
    RQ_QUEUES = {'default': {'HOST': 'localhost', 'DB': 0, 'PORT': 6379, 'ASYNC': True , 'DEFAULT_TIMEOUT': 1200}}


