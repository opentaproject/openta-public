# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.contrib.auth.hashers import make_password
import datetime
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from exercises.models import Answer, Exercise, AuditExercise
from django.contrib.contenttypes.models import ContentType
import logging
from opentasites.models import OpenTASite
from course.models import Course, sync_opentasite
from users.models import OpenTAUser
from django.conf import settings
import glob
import re
from django.db import connections, connection
from backend.middleware import create_connection, add_database, verify_or_create_database_connection


# psql  -U postgres -c "DROP DATABASE 'sites' ;"
# psql  -U postgres -c "CREATE DATABASE 'sites' OWNER postgres;"
# python manage.py migrate --database='sites'
def str_date(d):
    if d == None:
        return "0"
    ds = str(d).split(" ")[0]
    return ds


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        active_sites = glob.glob("/subdomain-data/*/dbname.txt")
        supers = []
        for a in active_sites:
            subdomain = a.split("/")[2]
            dbname = open(a).read()
            # print(f"SUBDOMAIN = {subdomain} {dbname} ")
            # opentasites =  OpenTASite.objects.using('opentasites').all()
            # for o in opentasites :
            verify_or_create_database_connection(subdomain)
            try:
                # o = OpenTASite.objects.using('opentasites').all().filter(subdomain=subdomain).first()
                # print(f"opentasite = {o}")
                courses = Course.objects.using(subdomain).all()
                superusers = User.objects.using(subdomain).all().filter(is_superuser=True)
                # print(f" DATA = {o.data}")
                for course in courses:
                    # course.data.update(o.data )
                    # print(f" Course data  {course.data}")
                    # print(f" {course.course_long_name} {course.course_name} {superusers.last().email}")
                    firstdat = User.objects.using(subdomain).values_list("date_joined", flat=True).first()
                    bonafide_students = (
                        User.objects.using(subdomain)
                        .filter(groups__name="Student", is_active=True)
                        .exclude(groups__name="View")
                        .exclude(groups__name="Admin")
                        .exclude(groups__name="Author")
                        .exclude(username="student")
                    )
                    answers = Answer.objects.using(subdomain).filter(user__in=bonafide_students)
                    try:
                        last_student_answer = str_date(
                            answers.order_by("date").last().date
                        )  # .values_list('last_login',flat=True) )
                    except:
                        last_student_answer = "null"
                    try:
                        last_student_login = str_date(
                            bonafide_students.order_by("last_login").last().last_login
                        )  # .values_list('last_login',flat=True) )
                    except:
                        last_student_login = "null"

                    us = list(
                        User.objects.using(subdomain)
                        .filter(is_superuser=True)
                        .exclude(last_login=None)
                        .exclude(username="super")
                        .order_by("last_login")
                        .values_list("username", "last_login")
                    )
                    last_admin_logins = [{"username": key, "date": str_date(val)} for (key, val) in us]

                    if True:
                        dat = {}
                        course.data["description"] = course.course_name + ": " + course.course_long_name
                        course.data["creator"] = "no_email " if not course.email_reply_to else course.email_reply_to
                        course.data["creation_date"] = str_date(firstdat)
                        course.save()
                    if True:
                        sync_opentasite(course)
                    course.save()
                # for course in courses:
                # course.save()
                # for course in courses:
                #    print(f"{subdomain} {course}")
                # for su in  superusers :
                #    if not 'super' == su.username :
                #        print(f"{subdomain} pk={su.pk} username={su.username} email={su.email}")
            except:
                pass
        # print(f"SUPERS = {supers}")
        emails = list(set([item["email"] for item in supers]))
        # print(f"emails = {emails}")
        assignments = []
        ps = {}
        for email in emails:
            dat = list(
                set(
                    [
                        (int("".join(item["last_login"].split("-"))), item["subdomain"], item["password"])
                        for item in supers
                        if item["email"] == email
                    ]
                )
            )
            dd = sorted(dat, key=lambda item: item[0])
            print(f" EMAIL = {email}")
            p = make_password(email)
            for d in dd:
                if d[-1] != "":
                    p = d[-1]
            for d in dd:
                if d[-1] != p and p != "":
                    assignments = assignments + [{"subdomain": d[1], "email": email, "password": p}]
            ps[email] = p
        for a in assignments:
            # print(f"a = {a}")
            subdomain = a["subdomain"]
            password = a["password"]
            email = a["email"]
            verify_or_create_database_connection(subdomain)
            courses = Course.objects.using(subdomain).all()
            users = User.objects.using(subdomain).filter(email=email)
            for user in users:
                if user.email == "ostlund@chalmers.se":
                    try:
                        User.objects.using(subdomain).filter(email=email).update(password=password)
                        print(f"succeeded update {user} ")
                    except Exception as e:
                        print(f"failed to update {user} ")
                        logger.error(f" {type(e).__name__} CANNOT SAVE USER {user} {subdomain} {str(e)} ")
        for key in ps.keys():
            print(f"P   {key} {ps[key]}")
