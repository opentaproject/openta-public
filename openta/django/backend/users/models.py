# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
from pylti.common import LTIException
import shutil, re
import hashlib

from course.models import Course
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models.signals import post_delete
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from exercises.models import AuditExercise, AuditResponseFile, ImageAnswer
import logging

logger = logging.getLogger(__name__)


# https://stackoverflow.com/questions/11317034/django-anonymous-user-group/11317148#11317148


def is_anonymous_student(user):
    groups = list(user.groups.values_list("name", flat=True))
    return "AnonymousStudent" in groups


class AnonymousPermissions(object):
    def authenticate(self, request, username, password=None):
        try:
            user = User.objects.get(username=username, groups__name="AnonymousStudent", is_active=True)
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class OpenTAUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="opentauser")
    courses = models.ManyToManyField(Course)
    lti_user_id = models.CharField(max_length=256, null=True, blank=True, editable=settings.EDITABLE)
    lis_person_contact_email_primary = models.CharField(max_length=256, null=True, blank=True, editable=settings.EDITABLE)
    lti_tool_consumer_instance_guid = models.CharField(max_length=256, null=True, blank=True, editable=settings.EDITABLE)
    lti_context_id = models.CharField(max_length=256, null=True, blank=True, editable=settings.EDITABLE)
    lti_roles = models.CharField(max_length=256, null=True, blank=True)
    lis_person_name_full = models.CharField(max_length=256, null=True, blank=True)
    lis_person_name_given = models.CharField(max_length=256, null=True, blank=True)
    lis_person_name_family = models.CharField(max_length=256, null=True, blank=True)
    immutable_user_id = models.CharField(max_length=256, null=True, blank=True, editable=settings.EDITABLE)

    # class Meta:
    # unique_together = (('lti_user_id', 'lti_context_id', 'lti_tool_consumer_instance_guid'),)

    # SEE https://github.com/misli/django-verified-email-field

    def save(self, *args, **kwargs):
        # print("A")
        lti_user_id = self.lti_user_id
        db = settings.DB_NAME
        if not lti_user_id:
            super().save(*args, **kwargs)
            return
        if OpenTAUser.objects.using(db).filter(lti_user_id=lti_user_id).count() == 0:
            super().save(*args, **kwargs)

    def __str__(self):
        return "Profile of user: {}".format(self.user.username)

    def username(self):
        return self.user.username

    def email(self):
        return self.user.email

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name


@receiver(post_delete, sender=OpenTAUser)
def delete_user_hook(sender, instance, using, **kwargs):
    try:
        user = instance.user
    except Exception as e:
        print(f"{type(e).__name__} {str(e) } ")
        return
    logger.error("DELETEING USER %s " % instance.user)
    images = ImageAnswer.objects.all().filter(user=user)
    for image in images:
        print("IMAGE %s %s " % (image.image, image.pdf))
        image.remove_file()
        image.delete()
    # answers deleteed via cascade
    # answers = Answer.objects.all().filter(user=user)
    # for answer in answers:
    #        print("ANSWER %s " % answer)
    #        answer.delete()
    audits = AuditExercise.objects.all().filter(student=user)
    for audit in audits:
        print("AUDIT = %s " % audit)
        afiles = AuditResponseFile.objects.all().filter(audit=audit)
        for afile in afiles:
            afile.delete()
            print("RESPONSE-FILE = %s " % afile)
        audit.delete()
    # accregation deleted via cascade
    # ags = Aggregation.objects.all().filter(user=user)
    # for ag in ags:
    #    print("AG = %s " % ag )
    #    ag.delete()
    username = str(user)
    print(f" DELETE SUBDOMAIN = {settings.SUBDOMAIN}")
    print(f" MEDIA ROOT = {settings.MEDIA_ROOT}")
    print(f" WALKDIR =  { os.path.join(settings.VOLUME, settings.SUBDOMAIN)}")
    for root, dirs, files in os.walk(
        os.path.join(settings.VOLUME, settings.SUBDOMAIN),
        topdown=False,
    ):
        # for name in files:
        #   if username in name:
        #          print(os.path.join(root, name), "FILE NAME = " , name )
        #          try:
        #             os.rmdir(os.path.join(root, name))
        #          except :
        #             pass
        string_to_hash = str(re.sub(r"(\s|\\n)+", " ", str(username)))  # BE CAREFUL WITH IMPLICIT MULTIPLIES!
        globalhash = (hashlib.md5(string_to_hash.encode("utf-8")).hexdigest())[:10]
        for name in dirs:
            if username == name:
                print(os.path.join(root, name), " DIR NAME = ", name)
                src = os.path.join(root, name)
                dest = os.path.join(root, name + "." + globalhash)
                shutil.move(src, dest)
