# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
import glob
import logging
import uuid

logger = logging.getLogger(__name__)
import platform
import subprocess

from backend.settings_local import *
STATICFILES_STORAGE = "compress_staticfiles.storage.CompressStaticFilesStorage"
if os.path.exists("backend/settings_private.py") :
    from backend.settings_private import *

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
DJANGO_SECRETS_FILE = '/subdomain_data/auth/settings_secrets.py'
try:
    import runpy

    secrets_path = (
        os.environ.get("DJANGO_SECRETS_FILE")
        or os.environ.get("SECRETS_FILE")
        or os.path.join("backend", "settings_secrets.py")
    )

    if secrets_path and os.path.isfile(secrets_path):
        _secrets = runpy.run_path(secrets_path)
        for _k, _v in _secrets.items():
            if _k.isupper():
                globals()[_k] = _v
        logger.info(f"Loaded secrets from {secrets_path}")
except Exception as _e:
    logger.warning(f"Failed to load secrets file: {_e}")

SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies"
INCLUDE_MATRIX_BLOCK = False
COMPUTER_SESSION_TIMEOUT = 60 * 60 
#SAFE_IP = ['98.128.246.120']
SAMESITE = 'None'
RATELIMIT_VIEW='backend.views.ratelimit_error'
RATE_LIMIT = "5/m"
try :
    GIT_HASH = subprocess.check_output(["/usr/bin/git", "rev-parse", "--short", "HEAD"]).decode('utf-8').strip()
except :
    GIT_HASH = 'GIT_HASH'
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
#AI_KEY =  os.environ.get("AI_KEY",None)
AI_KEY = globals().get('AI_KEY',  os.environ.get('AI_KEY', None) )
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
os.environ['DJANGO_RAGAMUFFIN_DB'] = DJANGO_RAGAMUFFIN_DB  # MAKE DJANGO_RAGAMUFFIN_DB AVAILABLE TO DJANGO_RAGAMUFFIN
INSTALLED_APPS.append('django_ragamuffin')
DATABASE_ROUTERS = [ 'backend.routers.AuthRouter']
if 'django_ragamuffin' in INSTALLED_APPS :
    from django_ragamuffin.settings import *
    DATABASE_ROUTERS = [ 'django_ragamuffin.db_routers.RagamuffinRouter','backend.routers.AuthRouter']
print(f"ROUTERS = {DATABASE_ROUTERS}")
STUDENT_QUERY_INTERVAL = 0
SAFE_RUN_TIMEOUT = 120
EFFORT = 'medium'
RUNNING_MANAGEMENT_COMMAND = (
    len(sys.argv) > 1
    and sys.argv[0].endswith("manage.py")
    and not 'runserver' in sys.argv[1]
)
if not RUNNING_DEVSERVER :
    STATIC_URL='https://storage.googleapis.com/opentaproject-cdn-bucket/v251123/deploystatic/'
else :
    CACHES["default"] =  {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",     # table name
        "TIMEOUT": 300,                  # seconds; None = never expire
        "OPTIONS": {
            "MAX_ENTRIES": 30000,        # default 300, increase to avoid pruning
            "CULL_FREQUENCY": 3,         # 1/3 of entries deleted when MAX_ENTRIES is hit
        },
        }
USE_URKUND = False
ADOBE_ID = globals().get('ADOBE_ID',  os.environ.get('ADOBE_ID', None) )
OPENAI_UPLOAD_STORAGE = '/subdomain-data/query'
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', None)
TWILIO_TO = os.environ.get('TWILIO_TO',None)
TWILIO_FROM = os.environ.get("TWILIO_FROM",None)
BUG_TO_EMAIL = os.environ.get("BUG_TO_EMAIL",None)
BUG_FROM_EMAIL = os.environ.get("BUG_FROM_EMAIL",None) 
BUG_CC_EMAIL = os.environ.get("BUG_CC_EMAIL",None) 
BUG_FROM_EMAIL = globals().get('BUG_FROM_EMAIL',os.environ.get('BUG_FROM_EMAIL',None))
BUG_TO_EMAIL = globals().get('BUG_TO_EMAIL',os.environ.get('BUG_TO_EMAIL',None))
DJANGO_SUPERUSER_EMAIL = globals().get('DJANGO_SUPERUSER_EMAIL',os.environ.get('DJANGO_SUPERUSER_EMAIL',None))
DJANGO_SUPERUSER_PASSWORD = globals().get('DJANGO_SUPERUSER_PASSWORD',os.environ.get('DJANGO_SUPERUSER_PASSWORD',None))
DJANGO_SUPERUSER_USERNAME = globals().get('DJANGO_SUPERUSER_USERNAME',os.environ.get('DJANGO_SUPERUSER_USERNAME',None))
SUPERUSER = DJANGO_SUPERUSER_USERNAME
SUPERUSER_PASSWORD = DJANGO_SUPERUSER_PASSWORD
DOCKER_EMAIL = globals().get('DOCKER_EMAIL',os.environ.get('DOCKER_EMAIL',None))
DOCKER_PASSWORD = globals().get('DOCKER_PASSWORD',os.environ.get('DOCKER_PASSWORD',None))
DOCKER_USERNAME = globals().get('DOCKER_USERNAME',os.environ.get('DOCKER_USERNAME',None))
EMAIL_HOST_PASSWORD = globals().get('EMAIL_HOST_PASSWORD',os.environ.get('EMAIL_HOST_PASSWORD',None))
KEYFILE = globals().get('KEYFILE',os.environ.get('KEYFILE',None))
OPENAI_API_KEY = globals().get('OPENAI_API_KEY',os.environ.get('OPENAI_API_KEY',None))
OPENAI_ORG_ID = globals().get('OPENAI_ORG_ID',os.environ.get('OPENAI_ORG_ID',None))
OPENAI_PROJECT_ID = globals().get('OPENAI_PROJECT_ID',os.environ.get('OPENAI_PROJECT_ID',None))
PGDATA = globals().get('PGDATA',os.environ.get('PGDATA',None))
PGHOST = globals().get('PGHOST',os.environ.get('PGHOST','localhost'))
PGPASSWORD = globals().get('PGPASSWORD',os.environ.get('PGPASSWORD',None))
PGUSER = globals().get('PGUSER',os.environ.get('PGUSER',None))
SECRET_KEY =globals().get('SECRET_KEY',os.environ.get('SECRET_KEY','abcddfghijklmnopqrst'))
SUPERUSER = globals().get('SUPERUSER',os.environ.get('SUPERUSER',None))
SUPERUSER_PASSWORD = globals().get('SUPERUSER_PASSWORD',os.environ.get('SUPERUSER_PASSWORD',None))
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
USE_CHATGPT = os.environ.get('USE_CHATGPT' ) and OPENAI_API_KEY and OPENAI_PROJECT_ID
APP_DIRS = True
assert SUPERUSER_PASSWORD , 'SUPERUSER PASSWORD NOT SET'
