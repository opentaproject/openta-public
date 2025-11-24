# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
import json
import logging
import os
import re

from course.models import Course
from exercises.models import Exercise

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
from django.core.cache import caches


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        logger.error(f"SETTINGS SUBDOMAIN = {settings.SUBDOMAIN}")
        opentasites = []
        f = open(settings.VOLUME + "/" + settings.SUBDOMAIN + "/dbname.txt")
        db_name = f.read()
        db_name = re.sub(r"\W", "", db_name)
        f.close()
        if 'opentasites' in settings.INSTALLED_APPS
            from opentasites.models import OpenTASite
            opentasite, _ = OpenTASite.objects.get_or_create(subdomain=settings.SUBDOMAIN, db_name=db_name)
            opentasite.subdomain = settings.SUBDOMAIN
            opentasite.save()
        # print( "SUBDOMAIN = %s %s %s %s " % (opentasite.id, opentasite.subdomain, opentasite.db_name, opentasite.db_label))
        # print("OPENTASITES = %s " % opentasites)
        courses = Course.objects.using(settings.SUBDOMAIN).all()
        logger.error("COURSES = %s " % len(courses))
        for course in courses:
            logger.error("SETTINGS SUBDOMAIN = %s for course %s  " % (settings.SUBDOMAIN, settings.SUBDOMAIN))
        logger.error(f"KEY = {course.course_key}")
        # course.opentasite = settings.SUBDOMAIN
        # course.google_aut_string = ''
        # course.save()
        # exdir = f"/subdomain-data/{opentasite.subdomain}/exercises/{course.course_key}"
        # print(f"CREATING {exdir}")
        # os.makedirs(exdir, exist_ok=True)
        # n_exercises = 100.0
        # for progress in Exercise.objects.sync_with_disc(course, i_am_sure=True):
        #    #print(f"{progress}")
        db = settings.SUBDOMAIN
        messages = []
        for course in courses :
            for progress in Exercise.objects.sync_with_disc(course, i_am_sure=True):
                messages = messages + progress
            exercises = Exercise.objects.using(db).select_related("course", "meta")
            for exercise in exercises:
                ca = caches["default"].get("temporarily_block_translations")
                # logger.error(f"CA = {ca}" )
                # print(f"EXERCIS IN IMPORT {exercise}")
                meta = exercise.meta
                fullpath = exercise.get_full_path()
                jsonfile = os.path.join(fullpath, "meta.json")
                if os.path.exists(jsonfile):
                    # print(f"jsonfile = {jsonfile} exists ")
                    with open(jsonfile, "r") as f:
                        s = f.read()
                    j = json.loads(s)
                    # print(f"j = {j}")
                    for key in [
                        "difficulty",
                        "required",
                        "image",
                        "allow_pdf",
                        "bonus",
                        "published",
                        "locked",
                        "sort_key",
                        "feedback",
                        "deadline_date",
                    ]:
                        jm = getattr(meta, key)
                        # print(f"KEY={key} {j[key]} {jm}")
                        setattr(meta, key, j[key])
                    # print(f" META = {meta}")
                    meta.save()
                    exercise.meta = meta
                    exercise.save()
                    os.remove(jsonfile)
        logger.debug("DONE YIELD")
