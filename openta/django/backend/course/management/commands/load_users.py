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
from course.duplicate import resource_lookup
from users.models import OpenTAUser


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        opentasites = []
        f = open(settings.VOLUME + "/" + settings.SUBDOMAIN + "/dbname.txt")
        db_name = f.read()
        db_name = re.sub(r"\W", "", db_name)
        if 'opentasites' in settings.INSTALLED_APPS :
            from opentasites.models import OpenTASite
            opentasite, _ = OpenTASite.objects.get_or_create(subdomain=settings.SUBDOMAIN, db_name=db_name)
            subdomain = opentasite.subdomain
        else :
            subdomain = settings.SUBDOMAIN
        courses = Course.objects.using(settings.SUBDOMAIN).all()

        for course in courses:
            course_key = course.course_key
            csv_file_names = glob.glob(f"/subdomain-data/{subdomain}/exercises/{course_key}/*.csv")
            dryrun = False
            for csv_file_name in csv_file_names:
                with open(csv_file_name) as csv_file:
                    bs = csv_file_name.split("/")[-1]
                    resource_name = bs.split(".")[0]
                    dataset = tablib.Dataset().load(csv_file.read(), format="csv")
                    resource = resource_lookup[resource_name]
                    res = resource.import_data(dataset, dry_run=dryrun)
                    if res.has_errors():
                        logger.error(f"db_load_users has errors in {resource_name} ")
                    else:
                        os.remove(csv_file_name)
        users = User.objects.using(subdomain).all()
        for user in users:
            try:
                opentauser = user.opentauser
            except:
                opentauser = OpenTAUser.objects.using(subdomain).create(user=user)
            for course in courses:
                opentauser.courses.add(course)
                opentauser.save()
            user.save()

        logger.debug("DONE YIELD")
