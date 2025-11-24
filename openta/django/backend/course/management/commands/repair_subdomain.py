# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
import datetime
import re

from course.models import Course

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        all_permissions = [
            "change_group",
            "view_group",
            "add_user",
            "change_user",
            "delete_user",
            "view_user",
            "change_course",
            "delete_course",
            "view_answer",
            "add_auditexercise",
            "change_auditexercise",
            "delete_auditexercise",
            "view_auditexercise",
            "add_auditresponsefile",
            "change_auditresponsefile",
            "delete_auditresponsefile",
            "view_auditresponsefile",
            "add_exercise",
            "administer_exercise",
            "change_exercise",
            "create_exercise",
            "delete_exercise",
            "edit_exercise",
            "reload_exercise",
            "view_exercise",
            "view_solution",
            "view_statistics",
            "view_student_id",
            "view_unpublished",
            "view_xml",
            "add_exercisemeta",
            "change_exercisemeta",
            "delete_exercisemeta",
            "view_exercisemeta",
            "add_imageanswer",
            "change_imageanswer",
            "delete_imageanswer",
            "view_imageanswer",
            "add_imageanswermanager",
            "change_imageanswermanager",
            "delete_imageanswermanager",
            "view_imageanswermanager",
            "add_question",
            "change_question",
            "delete_question",
            "log_question",
            "view_question",
            "add_site",
            "change_site",
            "delete_site",
            "view_site",
            "add_translation",
            "change_translation",
            "delete_translation",
            "view_translation",
            "add_opentauser",
            "change_opentauser",
            "delete_opentauser",
            "view_opentauser",
        ]

        """Remove name and surname from users."""

        print("SETTINGS SUBDOMAIN = %s " % settings.SUBDOMAIN)
        subdomain = settings.SUBDOMAIN
        db = subdomain
        opentasites = []
        f = open(settings.VOLUME + "/" + settings.SUBDOMAIN + "/dbname.txt")
        db_name = f.read()
        db_name = re.sub(r"\W", "", db_name)
        f.close()
        if 'opentasites' in settings.INSTALLED_APPS :
            opentasite, _ = OpenTASite.objects.get_or_create(subdomain=settings.SUBDOMAIN, db_name=db_name)
        else :
            opentasite = None
        #    print("OPENTASITES DID NOT EXIST")
        #    pass
        superusers = User.objects.using(db).filter(is_superuser=True).order_by("date_joined")
        superadmin = superusers.last()
        print(f"SUPERADMINM = {superadmin} {superadmin.email}")
        now = datetime.datetime.now()
        t = now.strftime("%Y-%m-%d %H:%M:%S")
        if opentasite :
            if not opentasite.db_label:
                print("SET DB_LABEL")
                opentasite.db_label = f" Initialized as {subdomain}  on {t} "
            if not opentasite.creator or opentasite.creator == "super":
                opentasite.creator = superadmin.email
                opentasite.data = {"creator": superadmin.email, "creation_date": t}
            print(f"SUPERUSERS = {superusers}")
            print(
                "SUBDOMAIN = %s %s %s %s " % (opentasite.id, opentasite.subdomain, opentasite.db_name, opentasite.db_label)
            )
            print("OPENTASITE = %s " % opentasite)
            opentasite.save()
        courses = Course.objects.all()
        print("COURSES = %s " % len(courses))
        for course in courses:
            print("SETTINGS SUBDOMAIN = %s for course %s  " % (settings.SUBDOMAIN, settings.SUBDOMAIN))
            print(f"KEY = {course.course_key}")
            course.opentasite = settings.SUBDOMAIN
            course.google_auth_string = ""
            print(f"DATA = {course.data}")
            try:
                data = course.data
            except Exception as e:
                print(f"ERROR IN DATA = {type(e).__name__}")
            if not data and opentasite:
                print(f"DATA IS NULL")
                data = opentasite.data
                if not "description" in data.keys():
                    data["description"] = settings.SUBDOMAIN
                course.data = data
                course.save()
        groups = Group.objects.using(settings.SUBDOMAIN).all()
        ct = ContentType.objects.get_for_model(User)
        print(f"CT = {ct}")
        permissions = Permission.objects.all()
        adminperms = list(
            set(all_permissions)
            - set(
                ["change_group", "view_group", "delete_course", "add_site", "change_site", "delete_site", "view_site"]
            )
        )
        codenamelist = {
            "Author": ["edit_exercise", "log_question"],
            "Student": ["log_question"],
            "View": ["view_solution", "view_statistics", "view_xml"],
            "Admin": adminperms,
            "AnonymousStudent": [],
        }
        for g in groups:
            codenames = codenamelist[g.name]
            print(f"g = {g} ")
            content_type = ContentType.objects.get_for_model(Group)
            for codename in codenames:
                perm, _ = Permission.objects.using(db).get_or_create(codename=codename, content_type=content_type)
                g.permissions.add(perm)
                g.save()
                print(f"perm = {perm}")
        superusers = User.objects.all().filter(is_superuser=True)
        # print('[')
        # pss = g.permissions.all().values_list('codename',flat=True)
        # for ps in pss :
        # print(f'"{ps}"')
        # print(',')
        # print(']')
