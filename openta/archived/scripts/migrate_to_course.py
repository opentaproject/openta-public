# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

# /bin/python3
"""Migrate installation from pre- course management versions.

The change in format of the exercise paths and the addition of the model OpenTAUser
makes it necessary to perform some manual migration to bring a server up to the
course management functionality.

This script should be run after the repository is updated to the latest version.

To run, start a django shell with

    python manage.py shell

run this script with

    %run ../../scripts/migrate_to_course.py

"""

from users.models import OpenTAUser
from course.models import Course
from exercises.models import Exercise
from django.contrib.auth.models import User

print("Creating OpenTAUser entries for all current users")
for user in User.objects.all():
    ou, _ = OpenTAUser.objects.get_or_create(user=user)

course = Course.objects.first()

print("Migrate users to new course, disable login and change mail address")
for student in User.objects.filter(groups__name="Student"):
    ou, _ = OpenTAUser.objects.get_or_create(user=student)
    if course not in ou.courses.all():
        ou.courses.add(course)
    if not student.email.startswith("migrated_"):
        student.email = "migrated_" + student.email
        student.set_unusable_password()
        student.save()

print(
    "Migrate exercises path and course association. "
    "Please move exercises in /exercises to a folder "
    "corresponding to the course pk: {}".format(course.pk)
)
for exercise in Exercise.objects.all():
    exercise.course = course
    if exercise.path.startswith("/"):
        exercise.path = exercise.path[1:]
    exercise.save()
