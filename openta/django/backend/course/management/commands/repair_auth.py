# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.contrib.auth import get_user_model
from collections import OrderedDict
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
import logging
from course.models import Course
from users.models import OpenTAUser
from django.conf import settings
import re

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--list ", dest="list", default="True", help="specify if list.")

    def handle(self, *args, **options):

        do_list = (options.get("list")).lower() == "true"
        print(f"LIST = {do_list}")
        print(f"OPTIONS = {options}")

        all_permission = [
            "add_logentry",
            "change_logentry",
            "delete_logentry",
            "view_logentry",
            "add_aggregation",
            "change_aggregation",
            "delete_aggregation",
            "view_aggregation",
            "add_group",
            "change_group",
            "delete_group",
            "view_group",
            "add_permission",
            "change_permission",
            "delete_permission",
            "view_permission",
            "add_user",
            "change_user",
            "delete_user",
            "view_user",
            "add_contenttype",
            "change_contenttype",
            "delete_contenttype",
            "view_contenttype",
            "add_course",
            "change_course",
            "delete_course",
            "view_course",
            "add_answer",
            "change_answer",
            "delete_answer",
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
            "add_opentasite",
            "change_opentasite",
            "delete_opentasite",
            "view_opentasite",
            "add_session",
            "change_session",
            "delete_session",
            "view_session",
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
            "add_queuetask",
            "change_queuetask",
            "delete_queuetask",
            "view_queuetask",
            "add_regradetask",
            "change_regradetask",
            "delete_regradetask",
            "view_regradetask",
        ]

        """Remove name and surname from users."""

        subdomain = settings.SUBDOMAIN
        db = subdomain
        all_permissions = Permission.objects.all()
        for p in all_permissions:
            print(f"pk={p.pk} codename={p.codename} content_type=({p.content_type.name}) ")
        print("codenamelist = {} ")
        User = get_user_model()
        if not User.objects.using(db).filter(username='super') :
            super =    User.objects.using(db).create_superuser('super', 'super@example.com', settings.SUPERUSER_PASSWORD)
        else :
            super , _  = User.objects.using(db).get_or_create(username="super")
        if do_list:
            for g in Group.objects.using(db).all():
                p = g.permissions.all()
                pss = list(set(p.values_list("codename", flat=True)))
                cts = p.values_list("content_type", "codename")
                # for ct in cts :
                #    print(f"CT = {ct}")
                print(f'codenamelist["{g.name}"] = [', end="")
                for ps in pss:
                    print(f'"{ps}"', end=",")
                print("]")
            return
        codenamelist = {}
        codenamelist["AnonymousStudent"] = [
            "log_question",
        ]
        codenamelist["Student"] = [
            "log_question",
        ]
        codenamelist["View"] = [
            "view_exercise",
            "view_statistics",
            "view_xml",
            "view_solution",
        ]
        codenamelist["Author"] = [
            "add_translation",
            "view_translation",
            "delete_translation",
            "view_student_id",
            "log_question",
            "reload_exercise",
            "view_answer",
            "add_exercise",
            "view_exercisemeta",
            "create_exercise",
            "add_exercisemeta",
            "change_exercisemeta",
            "view_exercise",
            "view_unpublished",
            "delete_exercisemeta",
            "view_solution",
            "view_statistics",
            "delete_exercise",
            "edit_exercise",
            "change_translation",
            "view_xml",
            "administer_exercise",
            "change_exercise",
        ]
        codenamelist["Admin"] = [
            "delete_translation",
            "view_auditexercise",
            "change_auditexercise",
            "view_student_id",
            "add_user",
            "log_question",
            "reload_exercise",
            "view_answer",
            "view_exercisemeta",
            "delete_auditexercise",
            "add_exercisemeta",
            "change_exercisemeta",
            "view_exercise",
            "view_unpublished",
            "delete_exercisemeta",
            "view_solution",
            "view_statistics",
            "edit_exercise",
            "change_user",
            "change_translation",
            "add_auditexercise",
            "administer_exercise",
        ]
        codenamelist["Author"] = list(set(codenamelist["Author"] + codenamelist["View"]))
        codenamelist["Admin"] = list(set(codenamelist["Admin"] + codenamelist["Author"]))

        # codenamelist["Admin"] = ["add_user","log_question","administer_exercise","edit_exercise","view_exercise","view_statistics","change_translation","delete_translation","change_user","view_answer","view_statistics"]
        # codenamelist["Author"] = ["log_question","edit_exercise","administer_exercise","change_translation","delete_translation","view_answer","view_statistics"]
        # codenamelist["View"] = ["view_xml","view_exercise","view_statistics",]
        # codenamelist["AnonymousStudent"] = ["log_question",]
        # codenamelist["Student"] = ["log_question",]
        # print(f" LIST PERMISSONS")
        # pss = Permission.objects.all().values_list('codename',flat=True)
        # for ps in pss :
        #        print(f'"{ps}"', end=',  ')
        opentasites = []
        f = open(settings.VOLUME + "/" + settings.SUBDOMAIN + "/dbname.txt")
        db_name = f.read()
        db_name = re.sub(r"\W", "", db_name)
        f.close()
        if 'opentasites' in settings.INSTALLED_APPS :
            opentasite, _ = OpenTASite.objects.get_or_create(subdomain=settings.SUBDOMAIN, db_name=db_name)
            opentasite.subdomain = settings.SUBDOMAIN
        else :
            opentasite = None
        superusers = User.objects.using(db).all().filter(is_superuser=True).order_by("date_joined")
        superadmin = superusers.last()
        now = datetime.datetime.now()
        t = now.strftime("%Y-%m-%d %H:%M:%S")
        if opentasite :
            if not opentasite.db_label:
                opentasite.db_label = f" Initialized as {subdomain}  on {t} "
            if not opentasite.creator or opentasite.creator == "super":
                opentasite.creator = superadmin.email
                opentasite.data = {"creator": superadmin.email, "creation_date": t}
            # print(f"SUPERUSERS = {superusers}")
            # print("SUBDOMAIN = %s %s %s %s " % ( opentasite.id, opentasite.subdomain, opentasite.db_name, opentasite.db_label ) )
            # print("OPENTASITE = %s " % opentasite)
            opentasite.save()
        courses = Course.objects.all()
        # print("COURSES = %s " % len( courses) )
        Group.objects.get_or_create(name="AnonymousStudent")
        print(f"DO COURSES {courses}")
        for course in courses:
            # print("SETTINGS SUBDOMAIN = %s for course %s  " % ( settings.SUBDOMAIN,  settings.SUBDOMAIN) )
            # print(f"KEY = {course.course_key}")
            course.opentasite = settings.SUBDOMAIN
            course.google_auth_string = ""
            course.save()
            groups = Group.objects.using(settings.SUBDOMAIN).all()
            # print(f"CT = {ct}")
            # codenamelist = {'Author' :  ['edit_exercise', 'log_question'] ,
            #      'Student' :  ['log_question'] ,
            #      'View' : ['view_solution', 'view_statistics', 'view_xml'],
            #      'Admin' : adminperms,
            #      'AnonymousStudent': []
            #      }
            for g in groups:
                codenames = list(set(codenamelist[g.name]))
                print(f"g = {g} ")
                g.permissions.clear()
                for codename in codenames:
                    perms = Permission.objects.all().filter(codename=codename)
                    for perm in perms:
                        if not perm.content_type.name in [
                            "site",
                            "session",
                            "contnet_type",
                            "group",
                            "permission",
                            "log_entry",
                        ]:
                            g.permissions.add(perm)
                            print(f"{g} ADDED perm=({perm}) ct=({perm.content_type})  codename = {codename}")
                        else:
                            print(f"{g} REJECTED perm=({perm}) ct=({perm.content_type})  codename = {codename}")
                g.save()
            superusers = User.objects.using(db).filter(is_superuser=True)
            allgroups = Group.objects.all()
            gs = OrderedDict([("AnonymousStudent", 1), ("Student", 2), ("View", 3), ("Author", 4), ("Admin", 5)])
            gs_all = {}
            for item in allgroups:
                gs_all[item.name] = item
            # print(f"gs_all = {gs_all}")
            # print(f"gs = {gs}")
            for user in User.objects.using(db).all():
                u_groups = set(user.groups.all().values_list("name", flat=True))
                highrank = gs_all["AnonymousStudent"]
                for g in gs:
                    print(f"g = {g}")
                    if g in u_groups:
                        # print(f"{user} has {g}")
                        highrank = gs_all[g]
                # print(f"user {user} highrank {highrank}")
                if not user.is_superuser:
                    for g in u_groups:
                        if not g == highrank.name:
                            print(f" delete {gs_all[g]} for {user}")
                            gs_all[g].user_set.remove(user)
                            user.save()
                        else:
                            pass
                            # print(f" KEEP {gs_all[g]} for {user}")
                if highrank.name == "Admin":
                    if not user.is_staff:
                        print(f" Fix staff for {user}")
                        user.is_staff = True
                    print(f" add Author to {user}")
                    user.groups.add(gs_all["Author"])
                    user.groups.add(gs_all["View"])
                    user.save()
                    # print(f" OWNERS = {course.owners.all() }")
                    owners = list(course.owners.all())
                    if not user in list(owners):
                        course.owners.add(user)
                        course.save()
                        print(f" Add {user} as owner")
                    else:
                        logger.info(f" {user} already owner")

                if highrank.name == "Author":
                    if not user.is_staff:
                        print(f" Fix staff for {user}")
                        user.is_staff = True
                    print(f" add Author to {user}")
                    user.groups.add(gs_all["View"])
                    user.save()
                    # print(f" OWNERS = {course.owners.all() }")
                    owners = list(course.owners.all())
                    if not user in list(owners):
                        course.owners.add(user)
                        course.save()
                        print(f" Add {user} as owner")
                    else:
                        logger.info(f" {user} already owner")
