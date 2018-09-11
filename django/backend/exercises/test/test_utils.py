"""Test utility functions."""
from exercises.models import Exercise, ExerciseMeta, Question, Answer, ImageAnswer, AuditExercise
from course.models import Course
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime
from django.utils import timezone


def create_exercise(key, name, path, course):
    e = Exercise(exercise_key=key, name=name, path=path, course=course)
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


def _create_answer(user, question, **kwargs):
    a = Answer(user=user, question=question, **kwargs)
    a.save()
    return a


def _create_answer_at(user, question, date, correct=True):
    return _create_answer(user, question, answer='a correct answer', correct=correct, date=date)


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
    image_path = 'testdata/test_image.jpg'
    ia = _create_image_answer(
        user=user,
        exercise=exercise,
        image=SimpleUploadedFile(
            name='test_image.jpg', content=open(image_path, 'rb').read(), content_type='image/jpeg'
        ),
        date=date,
    )
    return ia


def create_image_answer_before(user, exercise, deadline):
    before = deadline - datetime.timedelta(seconds=1)
    return _create_image_answer_at(user, exercise, date=before)


def create_image_answer_after(user, exercise, deadline):
    after = deadline + datetime.timedelta(seconds=1)
    return _create_image_answer_at(user, exercise, date=after)


def create_course(name, deadline_time):
    course = Course(course_name=name, deadline_time=deadline_time, published=True)
    course.save()
    return course


def create_audit(auditor, user, exercise, **kwargs):
    audit = AuditExercise(auditor=auditor, student=user, exercise=exercise, **kwargs)
    audit.save()
    return audit
