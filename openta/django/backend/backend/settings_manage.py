# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
import re

# if not 'DJANGO_SETTINGS_MODULE' in os.environ.keys() :
os.environ["DJANGO_SETTINGS_MODULE"] = "backend.settings"
# if not 'SETTINGS_MODULE' in os.environ.keys() :
os.environ["SETTINGS_MODULE"] = "backend.settings"
VOLUME = "/subdomain-data/"
from backend.settings import *

dblist = os.listdir(VOLUME)
DBLIST = os.listdir(VOLUME)
droplist = ["sites", "taskresults", "default"]
for d in droplist:
    try:
        dblist.remove(d)
    except:
        pass
for x in dblist:
    dbnamefile = VOLUME + "/" + x + "/dbname.txt"
    if os.path.exists(dbnamefile):
        f = open(VOLUME + "/" + x + "/dbname.txt")
        db_name = f.read()
        db_name = re.sub(r"\W", "", db_name)
        f.close()
        logger.debug("subpath  db :  %s =  >%s< " % (x, db_name))
        DATABASES[x] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": PGUSER,
            "PASSWORD": PGPASSWORD,
            "HOST": PGHOST,
            "CONN_MAX_AGE": 240,
            "PORT": "5432",
        }
