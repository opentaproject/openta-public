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
from course.models import Course, pytztimezone, tzlocalize
from exercises.models import ImageAnswer, Exercise
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files import File
from django.db.models import ImageField, FileField
from users.models import OpenTAUser
from backend.middleware import verify_or_create_database_connection
import glob

logger = logging.getLogger(__name__)

# IMPORTANT ; FIRST DELETE OPENTAUSER FOR THE CORRECT USER
# python manage.py fix_superuser --username super --password XXXXX --email 'super8@gmail.com' --subdomain vektorfalt
# python manage.py fix_superuser --email 'super9@gmail.com' --subdomain vektorfalt

# from django.core.files.storage import FileSystemStorage
# upload_storage = FileSystemStorage(location=settings.VOLUME, base_url="/")
# def answer_image_filename(instance, filename):
#    subdomain = settings.DB_NAME
#    ret = "/".join(
#        [
#            subdomain,
#            "media",
#            "answerimages",
#            str(instance.exercise.course.course_key),
#            instance.user.username,
#            instance.exercise.exercise_key,
#            str(uuid.uuid4()) + os.path.splitext(filename)[1],
#        ]
#    )
#    ret = re.sub(r"^/", "", ret)
#    #logger.info(f"TRIGGER ANSWER_IMAGE_FILANAME {ret}")
#    return ret


import io


class Command(BaseCommand):
    help = "python manage.py fix_broken_lti --username=stellan.ostlund\@physics.gu.se --subdomain=new5 --opentauser=96e4df65be3e5dacc9db851549cb4df2bc3fd1f3"

    def add_arguments(self, parser):
        parser.add_argument("--username", dest="username", default=None, help="Specifies the username original user.")
        parser.add_argument(
            "--subdomain", dest="subdomain", default=None, help="Specifies the subdomain for the superuser."
        )

    def handle(self, *args, **options):
        username = options.get("username")
        subdomain = options.get("subdomain")
        opentauser_ = options.get("opentauser")
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        db = subdomain
        print(f"username = {username} subdomain={subdomain} opentauser={opentauser_}")
        verify_or_create_database_connection(subdomain)
        user = User.objects.using(db).get(username=username)
        imagedir = str(os.path.join(settings.VOLUME, subdomain, "media", "answerimages"))
        print(f"imagedir = {imagedir}")
        userpath = f"{imagedir}/*/{username}/*/*"
        images = [item for item in glob.glob(userpath) if ".bak" not in item]
        user = User.objects.get(username=username)
        print(f"MEDIA_ROOT = {settings.MEDIA_ROOT}")
        for answer_image_filename in images:
            print(f"image = {answer_image_filename}")
            splits = answer_image_filename.split("/")
            coursekey = splits[5]
            exercise_key = splits[7]
            exercise = Exercise.objects.using(subdomain).get(exercise_key=exercise_key)
            dbexercise = exercise
            filebase = splits[8]
            extension = filebase.split(".")[-1]
            filetype = "Pdf" if extension == "pdf" else "Image"
            with open(answer_image_filename, "rb") as f:
                b = f.read()
            content_file = ContentFile(b, name=filebase)
            t = os.path.getmtime(answer_image_filename)
            tz = pytztimezone(settings.TIME_ZONE)

            date = tzlocalize(datetime.datetime.fromtimestamp(t))
            print(f"CONTENT_FILE = {content_file}")
            print(f"DATE = {date}")
            print(f"FileType = {filetype}")
            if extension == "pdf":
                content_file.content_type = "application/pdf"
                print(f"PDF FILE = {content_file} {vars(content_file)}")
                instance = ImageAnswer(
                    user=user, exercise=exercise, pdf=content_file, filetype=ImageAnswer.PDF, date=date
                )
                print(f" DID PDF")
            else:
                instance = ImageAnswer(user=user, exercise=exercise, image=content_file, date=date)
            instance.save()
