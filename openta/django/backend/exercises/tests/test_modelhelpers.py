# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Test calculate_student_results."""
from django.test import TestCase
from django.contrib.auth.models import User, Group
import datetime
from django.utils import timezone
import pytest

from exercises.aggregation.results import (
    calculate_students_results,
)
from backend.selenium_utils.utils import create_user
from .test_utils import (
    create_course,
    create_exercise,
    create_question,
    create_answer_before,
    set_meta,
    create_answer_after,
    create_image_answer_before,
    create_image_answer_after,
)
from exercises.audits.modelhelpers import get_students_not_active
import time

DEADLINE_HOUR = 8
DEADLINE_MINUTE = 0
DEADLINE_SECOND = 0
DEADLINE = timezone.make_aware(
    datetime.datetime(
        year=2005,
        month=5,
        day=1,
        hour=DEADLINE_HOUR,
        minute=DEADLINE_MINUTE,
        second=DEADLINE_SECOND,
    )
)

# TODO
# The current calculate_students_results require an image uploaded for all required
# and bonus exercises to count correct/deadline/image_deadline


class BasicCourse(TestCase):
    """Basic course test case.

    - 1 course
    - 1 student

    """

    def setUp(self):
        # Create course
        self.databases = {"default", "openta"}
        self._course = create_course("A course", datetime.time(DEADLINE_HOUR, DEADLINE_MINUTE, DEADLINE_SECOND))

        # Create student group
        student_group = Group(name="Student")
        student_group.save()

        # Create student and add to group
        self._student = create_user("student1", "student@test.se", "pw1", self._course)
        student_group.user_set.add(self._student)


@pytest.mark.enable_signals
class TestInactiveStudents(BasicCourse):
    def test_get_students_not_active_1(self):
        exercise = create_exercise("r1", "exercise1", "path1", self._course)
        question = create_question(exercise, "q1")
        user = self._student
        # No answers so should be inactive
        self.assertIn(self._student, get_students_not_active(exercise))
        # With an answer the student should be active
        create_answer_before(self._student, question, DEADLINE)
        self.assertNotIn(self._student, get_students_not_active(exercise))

    def test_get_students_not_active_image(self):
        exercise = create_exercise("r1", "exercise1", "path1", self._course)
        # Exercise with only image upload and no questions
        set_meta(exercise, image=True)

        # With no image answer the student should be inactive
        self.assertIn(self._student, get_students_not_active(exercise))

        # With an image answer the student should be active
        create_image_answer_before(self._student, exercise, DEADLINE)

        self.assertNotIn(self._student, get_students_not_active(exercise))
