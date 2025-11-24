# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from exercises.models import Exercise
from course.models import Course
from course.export_import import UserResource, OpenTAUserResource, server_reset
from django.conf import settings
import re
import os
import json
import logging

logger = logging.getLogger(__name__)
import glob
from django.core.cache import caches
import tablib
from collections import OrderedDict
from users.models import OpenTAUser
import subprocess


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry-run", default="True", help="specify if dry-run.")

    def handle(self, *args, **options):
        """Remove name and surname from users."""
        if 'opentasites' in settings.INSTALLED_APPS :
            from opentasites.models import OpenTASite
            opentasites = OpenTASite.objects.using("opentasites").all()
        else :
            opentasites = []
        dry_run = (options.get("dry-run")).lower() == "true"
        print(f" DRY_RUN={dry_run}")
        i = 0
        for opentasite in opentasites:

            db_name = opentasite.db_name
            db_label = opentasite.db_label
            subdomain = opentasite.subdomain
            datapath = f"{settings.VOLUME}/{subdomain}"
            if os.path.exists(f"{datapath}/dbname.txt"):
                db_name_check = (open(f"{datapath}/dbname.txt", "r").read()).strip()
                keep = str(db_name_check) == str(db_name)
            else:
                keep = False
            expired = not keep
            # if not dry_run :
            #    opentasite.db_label = ''
            #    opentasite.save()
            duplicates = list(opentasites.filter(db_name=db_name, subdomain=subdomain))
            if len(duplicates) > 1:
                for duplicate in duplicates[1:]:
                    print(f" DELETE  DUPLICATES {duplicate} {vars(duplicate)} ")
                    if not dry_run:
                        duplicate.delete()
            if expired:
                print(f"{subdomain} expired ")
                if not dry_run:
                    opentasite.delete()
                cmd = f"DROP DATABASE IF EXISTS {db_name};"
                if dry_run:
                    process = subprocess.Popen(
                        ["echo", "echo", "-U", "postgres", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                    )
                else:
                    process = subprocess.Popen(
                        ["psql", "-U", "postgres", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                    )
                for line in process.stdout:
                    print(f" {subdomain} EXPIRED LINE = {line}")
            else:
                cmd = f"SELECT 1 FROM pg_database WHERE datname='{db_name}';"
                process = subprocess.Popen(["psql", "-XtAc", cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for line in process.stdout:
                    logger.debug(f" {subdomain} OK LINE = {line}")
                print(f"{subdomain} is still active - do nothing")
