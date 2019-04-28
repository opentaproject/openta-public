import os
from exercises.models import Exercise, Answer, Question
from course.models import Course
from django.contrib.auth.models import User
import shutil
from pathlib import Path
import uuid


def duplicate_course(course: Course):
    n_exercises = Exercise.objects.filter(course=course).count()
    old_course_path = course.get_exercises_path()
    course.pk = None
    course.course_key = uuid.uuid4()
    course.lti_secret = uuid.uuid4()
    course.lti_key = uuid.uuid4()
    course.course_name = "{old} (copy)".format(old=course.course_name)
    course.published = False
    course.save()
    yield ("Copying exercises file tree, this could take some time...", 0)
    shutil.copytree(old_course_path, course.get_exercises_path())
    for key_file in Path(course.get_exercises_path()).glob("**/exercisekey"):
        key_file.unlink()
    for index, _ in enumerate(Exercise.objects.sync_with_disc(course, i_am_sure=True)):
        if index % (n_exercises // 20 + 1) == 0:
            yield ("Updating database...", index / n_exercises)
