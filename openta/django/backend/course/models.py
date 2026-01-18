# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
from datetime import tzinfo, time
import logging
import os
import re
import shutil
import uuid
from copy import deepcopy

from exercises import paths

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from zoneinfo import ZoneInfo
from datetime import datetime
from django.utils.timezone import make_aware


logger = logging.getLogger(__name__)

EMAIL_VALIDATOR = EmailValidator()

def pytztimezone( t ):
    tz = ZoneInfo( settings.TIME_ZONE)
    return tz
def tzlocalize( t ):
    tz = ZoneInfo( settings.TIME_ZONE)
    return make_aware(t,tz)






def patch_credential_string(value):
    return value.strip().lstrip("r").strip("'")


def patch_credential_string(value):
    return value.strip().lstrip("r").strip("'")


@receiver([pre_delete])
def signal_handler(sender, *args, **kwargs):
    for signal in ["pre_delete"]:
        if hasattr(sender, signal):
            getattr(sender, signal)(sender, *args, **kwargs)


upload_storage = FileSystemStorage(location=settings.VOLUME, base_url="/")

alphanumeric = RegexValidator(r"^[0-9a-z]*$", "Only lowercase and numbers allowed.")


def course_image_filename(instance, filename):
    subdomain = settings.DB_NAME
    fn = "/".join([subdomain, "media", "public", str(filename)])
    return fn


def course_image_asset_name(instance, filename):
    subdomain = settings.DB_NAME
    fn = "/".join(["media", "public", str(filename)])
    return fn


def str_date(d):
    if d == None:
        return "0"
    ds = str(d).split(" ")[0]
    return ds


def sync_opentasite(course):
    from exercises.models import Answer, AuditExercise, Exercise


    subdomain = course.opentasite
    course_key = str(course.course_key)
    if 'opentasites' in settings.INSTALLED_APPS :
        from opentasites.models import OpenTASite
    else  :
        return


    try:
        o = OpenTASite.objects.using("opentasites").get(subdomain=subdomain, course_key=course_key)
    except ObjectDoesNotExist as e:
        o, created = OpenTASite.objects.using("opentasites").get_or_create(subdomain=subdomain)
        o.course_key = course_key
        o.save()
    # print(f"SYNCC")

    course = Course.objects.using(subdomain).get(course_key=course_key)
    # opentausers = OpenTAUser.objects.using(subdomain).filter(courses=course).values_list('user')
    users = User.objects.using(subdomain).all().filter(opentauser__courses=course)  # .filter(course=course)
    # print(f"===============================nusers = {users.count()}")

    firstdat = User.objects.using(subdomain).values_list("date_joined", flat=True).first()
    superusers = User.objects.using(subdomain).all().filter(is_superuser=True)
    bonafide_students = (
        User.objects.using(subdomain)
        .filter(opentauser__courses=course, groups__name="Student", is_active=True)
        .exclude(groups__name="View")
        .exclude(groups__name="Admin")
        .exclude(groups__name="Author")
        .exclude(username="student")
    )
    answers = Answer.objects.using(subdomain).filter(user__in=bonafide_students)
    try:
        last_student_answer = str_date(answers.order_by("date").last().date)  # .values_list('last_login',flat=True) )
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
    supers = []
    pk = str(course.pk)
    if True:
        o.creator = "no_email " if not course.email_reply_to else course.email_reply_to
        data = {}
        # if not o.data :
        #    o.data = {}
        data["creator"] = "no_email " if not course.email_reply_to else course.email_reply_to
        data["course_key"] = course_key
        data["creation_date"] = str_date(firstdat)
        superemails = [
            dict(email=item.email, last_login=str_date(item.last_login), password=item.password)
            for item in superusers
            if not item.email == ""
        ]
        s = [
            dict(email=item.email, subdomain=subdomain, last_login=str_date(item.last_login), password=item.password)
            for item in superusers
            if not item.email == ""
        ]
        supers = supers + s
        data["course_name"] = course.course_name
        data["superusers"] = superemails
        data["users"] = bonafide_students.count()
        data["answers"] = answers.count()
        data["exercises"] = Exercise.objects.using(subdomain).filter(course=course).count()
        data["exercises_published"] = (
            Exercise.objects.using(subdomain).filter(course=course, meta__published=True).count()
        )
        data["last_student_answer"] = last_student_answer
        data["last_student_login"] = last_student_login
        data["last_admin_logins"] = last_admin_logins
        data["audits"] = AuditExercise.objects.using(subdomain).filter(student__in=bonafide_students).count()
        data["icon"] = course.icon.name.split("/")[-1]
        pk = str(course.pk)
        try:
            description = course.data["description"]
        except Exception as e:
            description = course.course_name
            logger.error(f"DESCRIPTIPN DOES NOT EXIST")
        data["description"] = description
        o.data = deepcopy(data)
        # print(f" TYPE = {type(o.data)}")
        # print(f"PK = {course.pk}")
        o.save()


class Course(models.Model):
    data = JSONField(default=dict)
    opentasite = models.CharField(max_length=255, default="")
    course_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course_name = models.CharField(max_length=255, default="OpenTA")
    lti_key = models.UUIDField(unique=True, default=uuid.uuid4)
    lti_secret = models.UUIDField(unique=True, default=uuid.uuid4)
    icon = models.ImageField(
        default=None, null=True, blank=True, upload_to=course_image_filename, storage=upload_storage
    )
    motd = models.CharField(max_length=1024, default="", blank=True)
    course_long_name = models.CharField(max_length=255, default="")
    registration_password = models.CharField(
        verbose_name="Registration password",
        max_length=255,
        null=True,
        default=None,
        blank=True,
    )
    registration_by_password = models.BooleanField(default=False, blank=True)
    deadline_time = models.TimeField(null=True, default=None, blank=True)
    url = models.CharField(max_length=255, blank=True, null=True, default=None)
    registration_domains = models.CharField(max_length=255, blank=True, null=True, default=None)
    registration_by_domain = models.BooleanField(default=False, blank=True)
    languages = models.CharField(max_length=255, blank=True, null=True, default=None)
    difficulties = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        default="+:Recommended,*:Easy,**:Medium,***:Hard",
    )
    email_reply_to = models.CharField(max_length=255, blank=True, null=True, default="", validators=[EMAIL_VALIDATOR])
    email_host = models.CharField(max_length=255, blank=True, null=True, default="")
    email_host_user = models.CharField(max_length=255, blank=True, null=True, default="")
    email_username = models.CharField(max_length=255, blank=True, null=True, default="")
    email_host_password = models.CharField(max_length=255, blank=True, null=True, default="")
    published = models.BooleanField(default=False)
    owners = models.ManyToManyField(User, limit_choices_to={"is_staff": True})
    use_auto_translation = models.BooleanField(default=False)
    google_auth_string = models.CharField(
        max_length=4096, blank=True, default=""
    )  # , validators=[validate_google_auth_string] )
    stars = models.IntegerField(default=0)
    use_email = models.BooleanField(default=False, blank=True)
    use_lti = models.BooleanField(default=False, blank=True)
    allow_anonymous_student = models.BooleanField(default=False, blank=True)

    def post_save(self, *args, **kwargs):
        if settings.RUNTESTS:
            return

        instance = kwargs["instance"]
        course = instance
        subdomain = course.opentasite
        try:
            sync_opentasite(instance)
        except Exception as e:
            logger.error(f" NO_POST_SAVE_SINCE_ERROR_IN_SYNC {type(e).__name__} {str(e)}")

    def save(self, *args, **kwargs):
        if settings.MULTICOURSE:
            from utils import touch_

            touch_(self.opentasite)
            subdomain = settings.SUBDOMAIN
            # print(f"COURSE SAVE SUBDOMAIN = {subdomain}")
            if hasattr(self, "opentasite"):
                subdomain = str(self.opentasite)
            else:
                subdomain = settings.SUBDOMAIN
                self.opentasite = subdomain
            settings.DB_NAME = subdomain
            settings.SUBDOMAIN = subdomain
            # print("B")
            if not subdomain == settings.SUBDOMAIN:
                msg = f"ERROR COURSE_MODEL subdomain={subdomain} settings.SUBDOMAIN={settings.SUBDOMAIN}"
                logger.error(msg)
            f = open(settings.VOLUME + "/" + subdomain + "/dbname.txt")
            # print("D")
            db_name = f.read()
            db_name = re.sub(r"\W", "", db_name)
            course_key = str(self.course_key)
            f.close()
            # print("H")
            #opentasite_obj, _ = OpenTASite.objects.get_or_create(subdomain=subdomain, course_key=course_key)
            # print("K")
            self.opentasite = subdomain
        if self.allow_anonymous_student:
            perm_log_answers = Permission.objects.filter(codename="log_question")
            anonymous_group, created = Group.objects.get_or_create(name="AnonymousStudent")
            if created:
                for perm in perm_log_answers:
                    anonymous_group.permissions.add(perm)
                anonymous_group.save()
        # print("L")
        super().save(*args, **kwargs)  # Call the "real" save() method.
        # print("M")
        defaultuser, created = User.objects.get_or_create(username="student")
        if created:
            from users.models import OpenTAUser

            opentauser, _ = OpenTAUser.objects.get_or_create(user=defaultuser)
        try:
            opentauser = defaultuser.opentauser
        except ObjectDoesNotExist:
            from users.models import OpenTAUser

            opentauser = OpenTAUser.objects.create(user=defaultuser)
            opentauser.save
        except Exception as e:
            logger.error(f"EXCEPTION  = {type(e).__name__}")
            # opentauser = OpenTAUser.object.create(user=defaultuser)
            # opentauser.save
        opentauser.courses.add(self)

    def pre_delete(self, *args, **kwargs):
        instance = kwargs["instance"]
        exercises_path = instance.get_exercises_path()
        answer_images_path = exercises_path.replace("exercises", "media/answerimages")
        student_assets_path = answer_images_path.replace("answerimages", "studentassets")
        cache_path = f"{settings.VOLUME}/CACHE/{instance.opentasite}/media/answerimages/{str(instance.course_key)}"
        paths_to_delete = [exercises_path, answer_images_path, student_assets_path, cache_path]
        # logger.error(f"EXERCISES_PATH = {exercises_path}")
        for path in paths_to_delete:
            try:
                p = re.sub(rf"{settings.VOLUME}", f"{settings.VOLUME}/deleted", path)
                shutil.move(path, p)
            except Exception as e:
                logger.error(f"{type(e).__name__} {str(e)} ")
        # super().delete(*args, **kwargs)

    def course_key_copy(self):
        return str(self.course_key)

    def subdomain(self):
        return self.opentasite

    def clean(self):
        if settings.VALIDATE_GOOGLE_AUTH_STRING and self.use_auto_translation and self.google_auth_string == "":
            raise ValidationError(
                {"use_auto_translation": _("Auto translation cannot be enabled with a blank Google auth string.")},
                code="invalid",
            )
        if self.use_auto_translation and (self.languages == "" or self.languages is None):
            raise ValidationError(
                {"use_auto_translation": _("Auto translation can only be enabled if Languages is nonempty.")},
                code="invalid",
            )

    def __str__(self):
        return self.course_name + " - " + self.course_long_name

    def get_exercises_path(self,db=None):
        if db == None :
            db = self.opentasite;
        if not settings.MULTICOURSE:
            self.opentasite = "openta"
        res = settings.VOLUME + "/" + str(self.opentasite) + "/exercises" + "/" + self.get_exercises_folder()
        return str(res)

    def get_pages_path(self):
        res = settings.VOLUME + "/" + str(self.opentasite) + "/pages/" + str(self.course_key)
        return str(res)


    def get_base_path(self):
        res = settings.VOLUME + "/" + str(self.opentasite) + "/exercises/" + str(self.course_key)
        return str(res)

    def get_student_answerimages_path(self):
        return os.path.join(paths.STUDENT_ANSWERIMAGES_PATH, self.get_exercises_folder())

    def get_exercises_folder(self):
        return str(self.course_key)

    def get_registration_domains(self):
        if self.registration_domains is not None:
            return list(map(lambda s: s.strip(), self.registration_domains.split(",")))
        else:
            return None

    def get_deadline_time(self):
        if self.deadline_time is not None:
            return self.deadline_time
        else:
            return time(hour=23, minute=59, second=0, tzinfo=pytztimezone(settings.TIME_ZONE))

    def get_languages(self):
        if self.languages is not None:
            return list(map(str.strip, self.languages.split(",")))
        else:
            return None
