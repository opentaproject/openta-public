# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.files.base import ContentFile
import shutil
import datetime
import re
from PIL import Image
import os
from exercises.views.api import upload_image
from django.core.exceptions import ObjectDoesNotExist
import logging
from course.models import Course
from exercises.models import ImageAnswer, Exercise, Answer
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files import File
from django.db.models import ImageField, FileField
from users.models import OpenTAUser
from backend.middleware import verify_or_create_database_connection
import glob

logger = logging.getLogger(__name__)
# python manage.py transfer_answers --src_username=kostara\@student.chalmers.se --dest_username=adammoln\@student.chalmers.se --subdomain=ffm516-2022


import io


class Command(BaseCommand):
    help = "python manage.py fix_broken_lti --username=stellan.ostlund\@physics.gu.se --subdomain=new5 --opentauser=96e4df65be3e5dacc9db851549cb4df2bc3fd1f3"

    def add_arguments(self, parser):
        parser.add_argument(
            "--src_username", dest="src_username", default=None, help="Specifies the username to copy from."
        )
        parser.add_argument(
            "--dest_username", dest="dest_username", default=None, help="Specifies the username to copyt to."
        )
        parser.add_argument(
            "--subdomain", dest="subdomain", default=None, help="Specifies the subdomain for the superuser."
        )

    def handle(self, *args, **options):
        src_username = options.get("src_username")
        dest_username = options.get("dest_username")
        subdomain = options.get("subdomain")
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        db = subdomain
        print(f"src_username = {src_username} dest_username = {dest_username} subdomain={subdomain} ")
        verify_or_create_database_connection(subdomain)
        src_user = User.objects.using(db).get(username=src_username)
        dest_user = User.objects.using(db).get(username=dest_username)
        answers = Answer.objects.using(db).filter(user=src_user)
        for answer in answers:
            answer.user = dest_user
            print(f"answer = {answer}")
            answer.save()
