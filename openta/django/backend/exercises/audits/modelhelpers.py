# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from course.models import Course, pytztimezone, tzlocalize
from exercises.parsing import exercise_xmltree, question_xmltree_get
from exercises.question import question_check
from django.contrib.auth.models import User
from exercises.serializers import ExerciseSerializer, ExerciseMetaSerializer, AnswerSerializer
from exercises.serializers import ImageAnswerSerializer, AuditExerciseSerializer
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch, Count, Avg, Q, F
from django.test import RequestFactory
import os
from functools import reduce
from collections import OrderedDict, defaultdict, namedtuple
import datetime
from django.utils import timezone
from django.conf import settings
from aggregation.models import Aggregation
from exercises.modelhelpers import duration_to_string
from statistics import median, mean
from exercises.modelhelpers import e_student_tried, get_all_who_tried, bonafide_students, get_all_who_passed


AnalyzeResults = namedtuple(
    "AnalyzeResults",
    ["answered_set", "answered_on_time_set", "with_image_set", "with_image_on_time_set"],
)


def analyze_exercise(exercise):
    """Get students to be audited.

    If exercise feedback is enabled this returns all student that have answered
    correctly and submitted an image answer.
    If exercise feedback is disabled this returns all students that have uploaded
    an image before deadline.
    """
    students = get_all_who_tried(exercise)
    tz = pytztimezone(settings.TIME_ZONE)
    deadline_time = datetime.time(23, 59, 59)
    course = exercise.course
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time

    questions = Question.objects.filter(exercise=exercise).select_related("exercise", "exercise__meta")
    deadline_date = datetime.datetime.now(tz) + datetime.timedelta(days=1)
    if exercise.meta.deadline_date is not None:
        deadline_date = exercise.meta.deadline_date
    users_answered_questions = []
    users_answered_questions_ontime = []
    for question in questions:
        if exercise.meta.feedback:
            users_answered_questions.append(
                students.filter(answer__question=question, answer__correct=True).values_list("pk", flat=True).distinct()
            )

            users_answered_questions_ontime.append(
                students.filter(
                    answer__question=question,
                    answer__correct=True,
                    answer__date__lt=tzlocalize(datetime.datetime.combine(deadline_date, deadline_time)),
                )
                .values_list("pk", flat=True)
                .distinct()
            )
        else:
            users_answered_questions.append(
                students.filter(answer__question=question).values_list("pk", flat=True).distinct()
            )

            users_answered_questions_ontime.append(
                students.filter(
                    answer__question=question,
                    answer__date__lt=tzlocalize(datetime.datetime.combine(deadline_date, deadline_time)),
                )
                .values_list("pk", flat=True)
                .distinct()
            )

    def _to_set(list_of_lists):
        if list_of_lists:
            return set.intersection(*map(set, list_of_lists))
        else:
            return set([])

    set_passed_users_answered_questions = _to_set(users_answered_questions)
    set_passed_users_answered_questions_ontime = _to_set(users_answered_questions_ontime)

    users_submitted_image_ontime = (
        students.filter(
            imageanswer__exercise=exercise,
            imageanswer__date__lt=tzlocalize(datetime.datetime.combine(deadline_date, deadline_time)),
        )
        .values_list("pk", flat=True)
        .distinct()
    )

    users_submitted_image = students.filter(imageanswer__exercise=exercise).values_list("pk", flat=True).distinct()

    return AnalyzeResults(
        answered_set=set_passed_users_answered_questions,
        answered_on_time_set=set_passed_users_answered_questions_ontime,
        with_image_set=set(users_submitted_image),
        with_image_on_time_set=set(users_submitted_image_ontime),
    )


def analyze_exercise_for_student(exercise, student_pk):
    tz = pytztimezone(settings.TIME_ZONE)
    deadline_time = datetime.time(23, 59, 59)
    course = exercise.course
    did_something = False
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    questions = Question.objects.filter(exercise=exercise).select_related("exercise", "exercise__meta")
    deadline_date = datetime.datetime.now(tz) + datetime.timedelta(days=1)
    if exercise.meta.deadline_date is not None:
        deadline_date = exercise.meta.deadline_date
    if deadline_date is not None:
        deadline_date_time = tzlocalize(datetime.datetime.combine(deadline_date, deadline_time))

    passed_all = True
    passed_all_on_time = True
    submitted_image = True
    submitted_image_on_time = True
    for question in questions:
        if Answer.objects.filter(user__pk=student_pk, question=question).exists():
            did_something = True
        if not Answer.objects.filter(user__pk=student_pk, question=question, correct=True).exists():
            passed_all = False
        if deadline_date is not None:
            correct_before_deadline = Answer.objects.filter(
                user__pk=student_pk, question=question, correct=True, date__lt=deadline_date_time
            )
            if not correct_before_deadline.exists():
                passed_all_on_time = False

    if not ImageAnswer.objects.filter(user__pk=student_pk, exercise=exercise).exists():
        submitted_image = False
    else:
        did_something = True
    if deadline_date is not None:
        image_before_deadline = ImageAnswer.objects.filter(
            user__pk=student_pk,
            exercise=exercise,
            date__lt=tzlocalize(datetime.datetime.combine(deadline_date, deadline_time)),
        )
        if not image_before_deadline.exists():
            submitted_image_on_time = False

    message = ""
    pass_ = True
    revision_needed = None
    if questions.count() > 0:
        if passed_all_on_time:
            message = message + "Answers OK and on time. "
        elif passed_all:
            pass_ = False
            message = message + "Answers OK but "
            latest = 0
            for question in questions:
                dbanswer = Answer.objects.filter(user__pk=student_pk, correct=True, question=question).earliest("date")
                submitted_at = dbanswer.date
                due_at = tzlocalize(datetime.datetime.combine(deadline_date, deadline_time))
                diff = submitted_at - due_at
                latest = max(diff.total_seconds(), latest)
            message = message + duration_to_string(latest) + " late.\n"
        else:
            pass_ = False
            message = message + "Answers wrong or incomplete. "
            revision_needed = True
    if exercise.meta.image:
        if submitted_image_on_time:
            message = message + "Image on time. "
        elif submitted_image:
            pass_ = False
            message = message + "Image  "
            image_answer = ImageAnswer.objects.filter(user=student_pk, exercise=exercise).latest("date")
            submitted_at = image_answer.date
            due_at = tzlocalize(datetime.datetime.combine(deadline_date, deadline_time))
            diff = submitted_at - due_at
            latest = diff.total_seconds()
            message = message + duration_to_string(latest) + " late.\n"
        else:
            pass_ = False
            message = message + "Image missing. "
            revision_needed = True

    return (pass_, message, did_something, revision_needed)


def get_students_to_be_audited(exercise):
    analyze_results = analyze_exercise(exercise)
    questions = Question.objects.filter(exercise=exercise).select_related("exercise", "exercise__meta")

    students = get_all_who_passed(exercise)
    passed = set(students.values_list("pk", flat=True))
    if settings.ENFORCE_ONTIME:
        if questions.count() > 0:
            passed = set.intersection(passed, analyze_results.answered_on_time_set)
        if exercise.meta.image:
            passed = set.intersection(passed, analyze_results.with_image_on_time_set)
    return students.filter(pk__in=passed)


def get_students_not_active(exercise):
    """Get students that haven't answered the questions or uploaded an image."""
    users = bonafide_students
    ag = Aggregation.objects.filter(exercise=exercise, user__in=users)
    students_not_active = []
    for user in users:
        cnt = Aggregation.objects.filter(exercise=exercise, user=user).exists()
        if not cnt:
            students_not_active = students_not_active + [user.pk]
        # else:
        #    #print("CNT = ", cnt , " user = ", user )
    return users.filter(pk__in=students_not_active)


def get_students_not_to_be_audited(exercise):
    """Get who are active but not scheduled for audit"""
    active_students = get_all_who_tried(exercise)
    passed_students = get_students_to_be_audited(exercise)
    return active_students.exclude(pk__in=passed_students)
