# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Test utility functions."""
import os
from django.conf import settings
from exercises.models import (
    Exercise,
    ExerciseMeta,
    Question,
    Answer,
    ImageAnswer,
    AuditExercise,
)
from course.models import Course
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime
from django.utils import timezone


def create_exercise(key, name, path, course):
    """Create an Exercise row and a minimal on-disk exercise.xml so XML parsing works in tests.

    Filesystem layout:
    /tmp/subdomain-data/openta/exercises/<course_key>/<path>/exercise.xml
    /tmp/subdomain-data/openta/exercises/<course_key>/<path>/exercisekey
    """
    e = Exercise(exercise_key=key, name=name, path=path, course=course)
    e.save(using="default")

    # Create minimal exercise folder and files expected by parsing helpers
    base = os.path.join(settings.VOLUME, "openta", "exercises", str(course.course_key))
    exdir = os.path.join(base, path)
    os.makedirs(exdir, exist_ok=True)
    # Minimal XML with one question; tests often create Question separately, key may differ
    xml_path = os.path.join(exdir, "exercise.xml")
    if not os.path.exists(xml_path):
        with open(xml_path, "w") as f:
            f.write(
                """
<exercise>
  <exercisename>{name}</exercisename>
  <global type="basic">
    <p>Test exercise</p>
  </global>
  <question key="q1" type="basic">
    <expression>1+1</expression>
  </question>
</exercise>
""".strip().format(name=name)
            )
    # Write exercisekey file matching the Exercise pk
    key_path = os.path.join(exdir, "exercisekey")
    with open(key_path, "w") as f:
        f.write(str(e.exercise_key))

    return e


def set_meta(exercise, **kwargs):
    meta, created = ExerciseMeta.objects.get_or_create(exercise=exercise)
    for key, value in kwargs.items():
        setattr(meta, key, value)
    meta.save(using="default")
    return meta


def create_question(exercise, key):
    question = Question(exercise=exercise, question_key=key)
    question.save()
    return question


def _create_answer(user, question, **kwargs):
    a = Answer(user=user, question=question, **kwargs)
    a.save(using="default")
    return a


def _create_answer_at(user, question, date, correct=True):
    return _create_answer(user, question, answer="a correct answer", correct=correct, date=date)


def create_answer_before(user, question, deadline, correct=True):
    before = deadline - datetime.timedelta(seconds=1)
    return _create_answer_at(user, question, date=before, correct=correct)


def create_answer_after(user, question, deadline, correct=True):
    after = deadline + datetime.timedelta(seconds=1)
    return _create_answer_at(user, question, date=after, correct=correct)


def _create_image_answer(user, exercise, **kwargs):
    ia = ImageAnswer(user=user, exercise=exercise, **kwargs)
    ia.save()
    return ia


def _create_image_answer_at(user, exercise, date):
    image_path = "testdata/test_image.jpg"
    ia = _create_image_answer(
        user=user,
        exercise=exercise,
        image=SimpleUploadedFile(
            name="test_image.jpg",
            content=open(image_path, "rb").read(),
            content_type="image/jpeg",
        ),
        date=date,
    )
    return ia


def create_image_answer_before(user, exercise, deadline):
    before = deadline - datetime.timedelta(seconds=600)
    return _create_image_answer_at(user, exercise, date=before)


def create_image_answer_after(user, exercise, deadline):
    after = deadline + datetime.timedelta(seconds=600)
    return _create_image_answer_at(user, exercise, date=after)


def create_course(name, deadline_time):
    course = Course(
        opentasite="default",
        course_name=name,
        course_long_name=name,
        deadline_time=deadline_time,
        published=True,
    )
    course.save()
    return course


def create_audit(auditor, user, exercise, **kwargs):
    audit = AuditExercise(auditor=auditor, student=user, exercise=exercise, **kwargs)
    audit.save()
    return audit
