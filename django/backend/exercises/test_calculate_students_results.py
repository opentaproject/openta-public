"""Test calculate_student_results."""
from django.test import TestCase
from django.contrib.auth.models import User, Group
import datetime
from django.utils import timezone

from exercises.aggregation.results import calculate_students_results, calculate_user_results
from exercises.setup_tests import create_user
from exercises.test.test_utils import (
    create_course,
    create_exercise,
    create_question,
    create_answer_before,
    set_meta,
    create_answer_after,
    create_image_answer_before,
    create_image_answer_after,
)

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
        self._course = create_course(
            "A course", datetime.time(DEADLINE_HOUR, DEADLINE_MINUTE, DEADLINE_SECOND)
        )

        # Create student group
        student_group = Group(name="Student")
        student_group.save()

        # Create student and add to group
        self._student = create_user('student1', 'student@test.se', 'pw1', self._course)
        student_group.user_set.add(self._student)


class TestRequiredExercise(BasicCourse):
    """Test minimal exercise.

    Exercise parameters:
        - With deadline
        - Required

    """

    def setUp(self):
        super().setUp()

        # Create exercise
        self._exercise = create_exercise('r1', 'Required Exercise 1', 'path1', course=self._course)
        self._question = create_question(self._exercise, 'q1')
        set_meta(self._exercise, published=True, required=True, deadline_date=DEADLINE)

    def test_before_deadline(self):
        """Answer before deadline.

        Student answers:
            - 1 correct BEFORE deadline

        """

        # Create correct answer before deadline
        create_answer_before(self._student, self._question, DEADLINE, correct=True)

        # Calculate results
        results = calculate_students_results(course=self._course)
        ru1 = list(filter(lambda user: user['username'] == 'student1', results))
        self.assertEqual(ru1[0]['required']['n_complete'], 1)
        self.assertEqual(ru1[0]['required']['n_correct'], 0)
        self.assertEqual(ru1[0]['required']['n_deadline'], 0)
        self.assertEqual(ru1[0]['required']['n_image_deadline'], 0)

    def test_after_deadline(self):
        """Answer after deadline.

        Student answers:
            - 1 correct AFTER deadline

        """

        # Create correct answer after deadline
        create_answer_after(self._student, self._question, DEADLINE, correct=True)

        # Calculate results
        results = calculate_students_results(course=self._course)
        ru1 = list(filter(lambda user: user['username'] == 'student1', results))
        self.assertEqual(ru1[0]['required']['n_complete'], 0)
        self.assertEqual(ru1[0]['required']['n_correct'], 0)
        self.assertEqual(ru1[0]['required']['n_deadline'], 0)
        self.assertEqual(ru1[0]['required']['n_image_deadline'], 0)


class ImageRequired(BasicCourse):
    """Image required.

    Exercise parameters:
        - With deadline
        - Required
        - Image required

    """

    def setUp(self):
        super().setUp()

        # Create exercise
        self._e1 = create_exercise('r1', 'Required Exercise 1', 'path1', course=self._course)
        self._q1 = create_question(self._e1, 'q1')
        set_meta(self._e1, published=True, required=True, image=True, deadline_date=DEADLINE)

    def test_incorrect_answer_before_deadline(self):
        """Answer before deadline.

        Student answers:
            - 1 incorrect BEFORE deadline

        """

        # Create correct answer before deadline
        create_answer_before(self._student, self._q1, DEADLINE, correct=False)

        # Calculate results
        results = calculate_students_results(course=self._course)
        ru1 = list(filter(lambda user: user['username'] == 'student1', results))
        self.assertEqual(ru1[0]['required']['n_complete'], 0)
        self.assertEqual(ru1[0]['required']['n_correct'], 0)
        self.assertEqual(ru1[0]['required']['n_deadline'], 0)
        self.assertEqual(ru1[0]['required']['n_image_deadline'], 0)

    def test_answer_before_deadline(self):
        """Answer before deadline.

        Student answers:
            - 1 correct BEFORE deadline
            - 1 image AFTER deadline

        """

        # Create correct answer before deadline
        create_answer_before(self._student, self._q1, DEADLINE, correct=True)

        # Create image answer before deadline
        create_image_answer_after(self._student, self._e1, DEADLINE)

        # Calculate results
        results = calculate_students_results(course=self._course)
        ru1 = list(filter(lambda user: user['username'] == 'student1', results))
        self.assertEqual(ru1[0]['required']['n_complete'], 0)
        self.assertEqual(ru1[0]['required']['n_correct'], 1)
        self.assertEqual(ru1[0]['required']['n_deadline'], 1)
        self.assertEqual(ru1[0]['required']['n_image_deadline'], 0)

    def test_both_after_deadline(self):
        """Both after deadline.

        Student answers:
            - 1 correct AFTER deadline
            - 1 image AFTER deadline

        """

        # Create correct answer after deadline
        create_answer_after(self._student, self._q1, DEADLINE, correct=True)

        # Create image answer before deadline
        create_image_answer_after(self._student, self._e1, DEADLINE)

        # Calculate results
        results = calculate_students_results(course=self._course)
        ru1 = list(filter(lambda user: user['username'] == 'student1', results))
        self.assertEqual(ru1[0]['required']['n_complete'], 0)
        self.assertEqual(ru1[0]['required']['n_correct'], 1)
        self.assertEqual(ru1[0]['required']['n_deadline'], 0)
        self.assertEqual(ru1[0]['required']['n_image_deadline'], 0)

    def test_both_before_deadline(self):
        """Both before deadline.

        Student answers:
            - 1 correct BEFORE deadline
            - 1 image BEFORE deadline

        """

        # Create correct answer after deadline
        create_answer_before(self._student, self._q1, DEADLINE, correct=True)

        # Create image answer before deadline
        create_image_answer_before(self._student, self._e1, DEADLINE)

        # Calculate results
        results = calculate_students_results(course=self._course)
        ru1 = list(filter(lambda user: user['username'] == 'student1', results))
        self.assertEqual(ru1[0]['required']['n_complete'], 1)
        self.assertEqual(ru1[0]['required']['n_correct'], 1)
        self.assertEqual(ru1[0]['required']['n_deadline'], 1)
        self.assertEqual(ru1[0]['required']['n_image_deadline'], 1)
