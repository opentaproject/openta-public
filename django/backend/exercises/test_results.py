from django.test import TestCase
from .models import Exercise, ExerciseMeta, Question, Answer, ImageAnswer, AuditExercise
from course.models import Course
from django.contrib.auth.models import User, Group
import datetime
from django.utils import timezone
from exercises.aggregation.results import calculate_students_results, calculate_user_results
from exercises.views.api import exercise_list
from django.core.files.uploadedfile import SimpleUploadedFile
import pprint


def create_exercise(key, name, path):
    e = Exercise(exercise_key=key, name=name, path=path)
    e.save()
    return e


def set_meta(exercise, **kwargs):
    meta, created = ExerciseMeta.objects.get_or_create(exercise=exercise)
    for key, value in kwargs.items():
        setattr(meta, key, value)
    meta.save()
    return meta


def create_question(exercise, key):
    question = Question(exercise=exercise, question_key=key)
    question.save()
    return question


def create_answer(user, question, **kwargs):
    a = Answer(user=user, question=question, **kwargs)
    a.save()
    return a


def create_answer_at(user, question, date):
    return create_answer(user, question, answer='a correct answer', correct=True, date=date)


def create_incorrect_at(user, question, date):
    return create_answer(user, question, answer='an incorrect answer', correct=False, date=date)


def create_image_answer(user, exercise, **kwargs):
    ia = ImageAnswer(user=user, exercise=exercise, **kwargs)
    ia.save()
    return ia


def create_image_answer_at(user, exercise, date):
    image_path = 'testdata/test_image.jpg'
    ia = create_image_answer(
        user=user,
        exercise=exercise,
        image=SimpleUploadedFile(
            name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg'
        ),
        date=date,
    )
    return ia


def create_course(name, deadline_time):
    course = Course(course_name=name, deadline_time=deadline_time)
    course.save()
    return course


def create_audit(auditor, user, exercise, **kwargs):
    audit = AuditExercise(auditor=auditor, student=user, exercise=exercise, **kwargs)
    audit.save()
    return audit


def create_answers_and_imageanswers(user, deadline, q1, q2, q3, q4, e1, e2, e3, e4):
    now = deadline
    midnight = timezone.make_aware(datetime.datetime(year=now.year, month=now.month, day=now.day))
    create_answer_at(
        user, q1, midnight + datetime.timedelta(hours=7, minutes=59, seconds=59)
    )  # Just before deadline
    create_incorrect_at(
        user, q1, midnight + datetime.timedelta(hours=8, minutes=59, seconds=59)
    )  # An incorrect answer after a correct one should still register as passed
    create_answer_at(
        user, q2, midnight + datetime.timedelta(hours=8, minutes=0, seconds=1)
    )  # Just after deadline
    create_answer_at(user, q3, now - datetime.timedelta(days=1))  # Well before deadline
    create_incorrect_at(
        user, q3, now - datetime.timedelta(days=1) + datetime.timedelta(hours=2)
    )  # An incorrect answer after a correct one should still register as passed
    # 3 images, 1 before deadline, 2 after deadline
    create_image_answer_at(
        user, e1, midnight + datetime.timedelta(hours=7, minutes=59, seconds=59)
    )  # Just before deadline
    create_image_answer_at(
        user, e2, timezone.now() + datetime.timedelta(days=1)
    )  # Well after deadline
    create_image_answer_at(
        user, e3, midnight + datetime.timedelta(hours=8, minutes=0, seconds=1)
    )  # Just after deadline

    # Both after deadline
    create_answer_at(user, q4, now + datetime.timedelta(days=1))
    create_image_answer_at(user, e4, now + datetime.timedelta(days=1))


def create_database():
    course = create_course("A course", datetime.time(8, 0, 0))
    e1 = create_exercise('r1', 'Required Exercise 1', 'path1')
    e2 = create_exercise('r2', 'Required Exercise 2', 'path2')
    e3 = create_exercise('r3', 'Required Exercise 3', 'path3')
    e4 = create_exercise('r4', 'Required Exercise 4', 'path4')
    b1 = create_exercise('b1', 'Bonus Exercise 1', 'path1')
    b2 = create_exercise('b2', 'Bonus Exercise 2', 'path2')
    b3 = create_exercise('b3', 'Bonus Exercise 3', 'path3')
    b4 = create_exercise('b4', 'Bonus Exercise 4', 'path4')
    q1 = create_question(e1, 'q1')
    q2 = create_question(e2, 'q2')
    q3 = create_question(e3, 'q3')
    q4 = create_question(e4, 'q4')
    bq1 = create_question(b1, 'q1')
    bq2 = create_question(b2, 'q2')
    bq3 = create_question(b3, 'q3')
    bq4 = create_question(b4, 'q4')
    now = timezone.now()
    midnight = timezone.make_aware(datetime.datetime(year=now.year, month=now.month, day=now.day))
    set_meta(e1, published=True, required=True, deadline_date=now)
    set_meta(e2, published=True, required=True, deadline_date=now)
    set_meta(e3, published=True, required=True, deadline_date=now)
    set_meta(e4, published=True, required=True, deadline_date=now)
    set_meta(b1, published=True, bonus=True, deadline_date=now)
    set_meta(b2, published=True, bonus=True, deadline_date=now)
    set_meta(b3, published=True, bonus=True, deadline_date=now)
    set_meta(b4, published=True, bonus=True, deadline_date=now)
    student = Group(name="Student")
    student.save()
    admin = Group(name="Admin")
    admin.save()
    u1 = User.objects.create_user('student1', 'student1@test.se', 'pw1')
    u2 = User.objects.create_user('student2', 'student2@test.se', 'pw2')
    uadmin = User.objects.create_user('admin1', 'admin1@test.se', 'pw3')
    student.user_set.add(u1)
    student.user_set.add(u2)
    admin.user_set.add(uadmin)
    # 3 correct, 2 before deadline, 1 after deadline
    # 1 force passed by audit
    create_answers_and_imageanswers(u1, now, q1, q2, q3, q4, e1, e2, e3, e4)
    create_answers_and_imageanswers(u2, now, bq1, bq2, bq3, bq4, b1, b2, b3, b4)

    create_audit(uadmin, u1, e4, force_passed=True)
    create_audit(uadmin, u2, b4, force_passed=True)


class QuestionMethodTests(TestCase):
    def setUp(self):
        create_database()

    def test_results(self):
        """
        Tests the aggregated results. First tests the calculate_students_results and then calculate_user_results. In both cases the database consists of required and bonus exercise with answers and image answers at different times. The audit force_passed is also tested.
        """
        results = calculate_students_results()
        ru1 = list(filter(lambda user: user['username'] == 'student1', results))
        self.assertEqual(ru1[0]['required']['n_correct'], 4)
        self.assertEqual(ru1[0]['required']['n_deadline'], 3)
        self.assertEqual(ru1[0]['required']['n_image_deadline'], 2)
        self.assertEqual(ru1[0]['total'], 4)
        self.assertEqual(ru1[0]['optional'], 0)
        ru2 = list(filter(lambda user: user['username'] == 'student2', results))
        self.assertEqual(ru2[0]['bonus']['n_correct'], 4)
        self.assertEqual(ru2[0]['bonus']['n_deadline'], 3)
        self.assertEqual(ru2[0]['bonus']['n_image_deadline'], 2)
        self.assertEqual(ru2[0]['total'], 4)
        self.assertEqual(ru2[0]['optional'], 0)

        u1 = User.objects.get(username='student1')
        u1detailed = calculate_user_results(u1.pk)
        u2 = User.objects.get(username='student2')
        u2detailed = calculate_user_results(u2.pk)

        self.assertEqual(u1detailed['summary']['required']['n_correct'], 4)
        self.assertEqual(u1detailed['summary']['required']['n_deadline'], 3)
        self.assertEqual(u1detailed['summary']['required']['n_image_deadline'], 2)
        self.assertEqual(u2detailed['summary']['bonus']['n_correct'], 4)
        self.assertEqual(u2detailed['summary']['bonus']['n_deadline'], 3)
        self.assertEqual(u2detailed['summary']['bonus']['n_image_deadline'], 2)
        self.assertEqual(u1detailed['summary']['total'], 4)
        self.assertEqual(u1detailed['summary']['optional'], 0)
        self.assertEqual(u2detailed['summary']['total'], 4)
        self.assertEqual(u2detailed['summary']['optional'], 0)

        self.assertEqual(u1detailed['exercises']['r1']['correct'], True)
        self.assertEqual(u1detailed['exercises']['r1']['image'], True)
        self.assertEqual(u1detailed['exercises']['r1']['correct_deadline'], True)
        self.assertEqual(u1detailed['exercises']['r1']['image_deadline'], True)

        self.assertEqual(u1detailed['exercises']['r2']['correct'], True)
        self.assertEqual(u1detailed['exercises']['r2']['image'], True)
        self.assertEqual(u1detailed['exercises']['r2']['correct_deadline'], False)
        self.assertEqual(u1detailed['exercises']['r2']['image_deadline'], False)

        self.assertEqual(u1detailed['exercises']['r3']['correct'], True)
        self.assertEqual(u1detailed['exercises']['r3']['image'], True)
        self.assertEqual(u1detailed['exercises']['r3']['correct_deadline'], True)
        self.assertEqual(u1detailed['exercises']['r3']['image_deadline'], False)

        self.assertEqual(u1detailed['exercises']['r4']['correct'], True)
        self.assertEqual(u1detailed['exercises']['r4']['image'], True)
        self.assertEqual(u1detailed['exercises']['r4']['correct_deadline'], False)
        self.assertEqual(u1detailed['exercises']['r4']['image_deadline'], False)
        self.assertEqual(u1detailed['exercises']['r4']['force_passed'], True)

        self.assertEqual(u2detailed['exercises']['b1']['correct'], True)
        self.assertEqual(u2detailed['exercises']['b1']['image'], True)
        self.assertEqual(u2detailed['exercises']['b1']['correct_deadline'], True)
        self.assertEqual(u2detailed['exercises']['b1']['image_deadline'], True)

        self.assertEqual(u2detailed['exercises']['b2']['correct'], True)
        self.assertEqual(u2detailed['exercises']['b2']['image'], True)
        self.assertEqual(u2detailed['exercises']['b2']['correct_deadline'], False)
        self.assertEqual(u2detailed['exercises']['b2']['image_deadline'], False)

        self.assertEqual(u2detailed['exercises']['b3']['correct'], True)
        self.assertEqual(u2detailed['exercises']['b3']['image'], True)
        self.assertEqual(u2detailed['exercises']['b3']['correct_deadline'], True)
        self.assertEqual(u2detailed['exercises']['b3']['image_deadline'], False)

        self.assertEqual(u2detailed['exercises']['b4']['correct'], True)
        self.assertEqual(u2detailed['exercises']['b4']['image'], True)
        self.assertEqual(u2detailed['exercises']['b4']['correct_deadline'], False)
        self.assertEqual(u2detailed['exercises']['b4']['image_deadline'], False)
        self.assertEqual(u2detailed['exercises']['b4']['force_passed'], True)
