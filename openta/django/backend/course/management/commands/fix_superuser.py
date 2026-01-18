# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib.auth.models import User, Group
from backend.middleware import add_database

import os
from course.models import Course
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from users.models import OpenTAUser
from backend.middleware import verify_or_create_database_connection
from django.contrib.auth import get_user_model
import django
User = get_user_model()
django.setup()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# python manage.py fix_superuser --username super --password XXXXX --email 'super8@gmail.com' --subdomain vektorfalt
# python manage.py fix_superuser --email 'super9@gmail.com' --subdomain vektorfalt


class Command(BaseCommand):
    help = "Crate a superuser, and allow password to be provided"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username", dest="username", default=None, help="Specifies the username for the superuser."
        )
        parser.add_argument(
            "--password", dest="password", default=None, help="Specifies the password for the superuser."
        )
        parser.add_argument(
            "--subdomain", dest="subdomain", default=None, help="Specifies the subdomain for the superuser."
        )
        parser.add_argument("--email", dest="email", default=None, help="Specifies the email for the superuser.")

    def handle(self, *args, **options):
        emails = options.get("email").split(",")
        username_ = options.get("username")
        subdomain = options.get("subdomain")
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        db = subdomain
        add_database(subdomain)
        verify_or_create_database_connection(subdomain)
        for email in emails:
            print("EMAIL = %s " % email)
            password = options.get("password")
            username = username_
            if password == None:
                password = email
            if username == username_:
                username = email.split("@")[0]

            print(f'USERNAME = {username} email={email} password={password}')



            try:
                from django.core.management import call_command
                call_command('migrate')  # ensure DB schema is ready
            except OperationalError as e:
                print("Database not ready:", e)
                exit(1)
            
            User = get_user_model()
            try:
                users = User.objects.using(db).filter( username=username) 
                if users :
                    users[0].delete()
            except Exception as e :
                print(f"EXCEPTION ON DELETE = {str(e)}")
                pass
            user = User.objects.db_manager(db).create_superuser(username=username, email=email, password=password)
            groupnames = ["Admin", "Author", "View"]
            # groupnames = Group.objects.all().values_list('name',flat=True)
            for groupname in groupnames:
                group = Group.objects.using(db).get(name=groupname)
                user.groups.add(group)
                print("GROUP = ", group)
            courses = Course.objects.all()
            opentauser, _ = OpenTAUser.objects.get_or_create(user=user)
            for course in courses:
                course_key = course.course_key
                os.makedirs(f"/subdomain-data/{subdomain}/exercises/{course_key}", exist_ok=True)
                opentauser.courses.add(course)
            opentauser.save()
            user.save()
            superadmin = user
            superusers = User.objects.all().filter(is_superuser=True).order_by("pk")
            for course in courses:
                course.google_auth_string = ""
                course.email_reply_to = superadmin.email
                course.email_host = superadmin.email.split("@")[-1]
                course.email_host_user = superadmin.email.split("@")[0]
                course.email_username = superadmin.email
                for superuser in superusers:
                    course.owners.add(superuser)
                course.save()
