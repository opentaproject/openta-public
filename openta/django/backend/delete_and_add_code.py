# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from course.models import Course
from exercises.models import Exercise, ImageAnswer, Answer, AuditExercise, AuditResponseFile
from aggregation.models import Aggregation
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings
import os, shutil


settings.DB_NAME = "ffm521"
settings.SUBDOMAIN = "ffm521"


email = "joe3@gmail.com"
password = email
username = "joe3"
user = User.objects.create_user(username, email=email, password=password)
groupnames = ["Admin", "Author", "View"]
for groupname in groupnames:
    group = Group.objects.get(name=groupname)
    user.groups.add(group)
courses = Course.objects.all()
opentauser, _ = OpenTAUser.objects.get_or_create(user=user)
for course in courses:
    opentauser.courses.add(course)
opentauser.save()
user.save()

user = User.objects.get(username="tijohans@student.chalmers.se")
images = ImageAnswer.objects.all().filter(user=user)
for image in images:
    print("IMAGE %s %s " % (image.image, image.pdf))
    image.remove_file()
    image.delete()
answers = Answer.objects.all().filter(user=user)
for answer in answers:
    print("ANSWER %s " % answer)
    answer.delete()
audits = AuditExercise.objects.all().filter(student=user)
for audit in audits:
    print("AUDIT = %s " % audit)
    afiles = AuditResponseFile.objects.all().filter(audit=audit)
    for afile in afiles:
        afile.delete()
        print("RESPONSE-FILE = %s " % afile)
    audit.delete()
ags = Aggregation.objects.all().filter(user=user)
for ag in ags:
    print("AG = %s " % ag)
    ag.delete()

username = str(user)
for root, dirs, files in os.walk(os.path.join(settings.VOLUME, settings.SUBDOMAIN, settings.MEDIA_ROOT), topdown=False):
    for name in files:
        if username in name:
            print(os.path.join(root, name))
            os.rmdir(os.path.join(root, name))
    for name in dirs:
        if username in name:
            print(os.path.join(root, name))
            shutil.rmtree(os.path.join(root, name))
user.delete()
