# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib.auth.models import User, Group
import os
from django.core.exceptions import ObjectDoesNotExist
from course.models import Course
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from users.models import OpenTAUser
from backend.middleware import verify_or_create_database_connection

# IMPORTANT ; FIRST DELETE OPENTAUSER FOR THE CORRECT USER
# python manage.py fix_superuser --username super --password XXXXX --email 'super8@gmail.com' --subdomain vektorfalt
# python manage.py fix_superuser --email 'super9@gmail.com' --subdomain vektorfalt


class Command(BaseCommand):
    help = "python manage.py fix_broken_lti --username=stellan.ostlund\@physics.gu.se --subdomain=new5 --opentauser=96e4df65be3e5dacc9db851549cb4df2bc3fd1f3"

    def add_arguments(self, parser):
        parser.add_argument("--username", dest="username", default=None, help="Specifies the username original user.")
        parser.add_argument(
            "--subdomain", dest="subdomain", default=None, help="Specifies the subdomain for the superuser."
        )
        parser.add_argument("--opentauser", dest="opentauser", default=None, help="Specifies opentauser.")

    def handle(self, *args, **options):
        username_ = options.get("username")
        subdomain = options.get("subdomain")
        opentauser_ = options.get("opentauser")
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        db = subdomain
        print(f"username = {username_} subdomain={subdomain} opentauser={opentauser_}")
        verify_or_create_database_connection(subdomain)
        opentauser_user = User.objects.using(db).get(username=opentauser_)
        user = User.objects.using(db).get(username=username_)
        try:
            opentauser = user.opentauser
            print(f" User {user} has opentauser already and will not be overwritten; delete it first")
            exit()
        except ObjectDoesNotExist:
            print(f"OK: so opentauser does not exist")
        try:
            opentauserhash = opentauser_user.opentauser
        except RelatedObjectDoesNotExist:
            print(f"opentauser_user does not have opentauser so exit")
            exit()
        opentauserhash = opentauser_user.opentauser
        print(f"OK: user={user} opentauserhash={opentauserhash}")
        opentauserhash_email = opentauserhash.lis_person_contact_email_primary
        print(f"hash email = {opentauserhash_email}")
        print(f"username = {user.username}")
        emails_match = opentauserhash_email == user.username
        if emails_match:
            print("EMAILS MATCH SO DO THE TRANSFER")
            correct_opentauser = opentauserhash
            print("A")
            user.opentauser = correct_opentauser
            print("B")
            opentauser_user.opentauser.opentauser = None
            print("C")
            opentauser_user.save()
            print("D")
            user.opentauser.save()
            print("E")
        # opentauser = opentauser_user.opentauser
