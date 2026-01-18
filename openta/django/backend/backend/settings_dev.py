# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
import glob
import logging
import uuid
from django.conf import settings
from backend.settings_static import *
from backend.settings_local import *

EMAIL_FILE_PATH = "/tmp"  # change this to a proper location
SECRET_KEY = "SECRET_KEY"
SUPERUSER_PASSWORD = 'super'
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
USE_GMAIL=False
ADMINURL='administration'
USE_ACCEL_REDIRECT=False
BLOCK_EMAIL_AUDITS = False
