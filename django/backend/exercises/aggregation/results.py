from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from aggregation.models import Aggregation, get_cache_and_key, STATISTICS_CACHE_TIMEOUT
from exercises.modelhelpers import serialize_exercise_with_question_data, get_exercise_render
from exercises.serializers import ExerciseSerializer, AnswerSerializer, ImageAnswerSerializer
from django.conf import settings
from exercises.views import get_exercise_list, get_unsafe_exercise_summary
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from statistics import mean, median
import datetime
import time
from django.core.cache import caches
from exercises.modelhelpers import (
    exercise_list_data,
    e_name,
    e_path,
    e_student_tried,
    has_audit_response_waiting,
    bonafide_students,
)
from exercises.modelhelpers import e_student_percent_complete, e_student_attempts_mean
from exercises.modelhelpers import e_student_attempts_median, e_student_activity, post_process_list
from exercises.modelhelpers import p_student_activity
from aggregation.models import Aggregation
import pytz
import logging
import django_rq
from rq.decorators import job


logger = logging.getLogger(__name__)


def students_results(cache_seconds=STATISTICS_CACHE_TIMEOUT, force=False, task=None, course=None):
    (cache, cachekey) = get_cache_and_key('students_results:', coursePk=course.id)
    result = cache.get(cachekey)
    if result is not None and not force:
        return result
    result = calculate_students_results(task, course=course)
    if cachekey:
        cache.set(cachekey, result)
    return result


def student_statistics_exercises(cache_seconds=STATISTICS_CACHE_TIMEOUT, force=False, course=None):
    (cache, cachekey) = get_cache_and_key('student_statistics_exercises:', coursePk=course.pk)
    result = cache.get(cachekey)
    if result is not None and not force:
        return result
    result = calculate_student_statistics_exercises(course=course)
    if cachekey:
        cache.set(cachekey, result, cache_seconds)
    return result


# @job('high')
# def testfunc() :
#    time.sleep(60)
#    testfile = open("/tmp/qfile.txt","a")
#    now = datetime.datetime.now()
#    testfile.write( now.strftime("%Y-%m-%d %H:%M:%S") )
#    testfile.write('\n')
#    testfile.close()


def calculate_students_custom_results(dbexercises, task=None, course=None):
    students = (
        User.objects.filter(groups__name='Student', opentauser__courses=course)
        .exclude(username='student')
        .order_by('first_name')
    )
    results = []
    n_students = students.count()
    for index, student in enumerate(students):
        if task is not None:
            task.status = "Calculating custom results in aggregation.results.py "
            task.progress = round(((index + 1) / n_students) * 100)
            task.save()
        results.append(calculate_unsafe_user_summary(student.pk, course.id, dbexercises))
        if True or logger.isEnabledFor(logging.DEBUG):
            logger.debug("Adding result for " + student.username)
            if dbexercises:
                logger.debug("CALCULATE STUDENTS CUSTOM RESULTS DBEXERCISEDS " + str(  dbexercises.count()) )
    return results


def calculate_students_results(task=None, course=None):
    students = (
        User.objects.filter(groups__name='Student', opentauser__courses=course)
        .exclude(username='student')
        .order_by('first_name')
    )
    results = []
    n_students = students.count()
    for index, student in enumerate(students):
        if task is not None:
            task.status = "Calculating results in aggregation.results.py "
            task.progress = round(((index + 1) / n_students) * 100)
            task.save()
        results.append(calculate_unsafe_user_summary(student.pk, course.id, None))
        if True or logger.isEnabledFor(logging.DEBUG):
            logger.debug("Adding result for " + student.username)
    return results


def serialize_exercise_data_for_course(course, exercise):
    (cache, cachekey) = get_cache_and_key(
        'exercise_data_for_course:', coursePk=course.id, exercise_key=exercise.exercise_key
    )
    if cache.has_key(cachekey):
        return cache.get(cachekey)
    users = bonafide_students.filter(opentauser__courses=course)
    nstudents = users.count()
    serializer = ExerciseSerializer(exercise)
    esdata = serializer.data
    exercise_key = esdata['exercise_key']
    ed = {}
    ags = Aggregation.objects.filter(course=course, exercise=exercise, user__in=users)
    n_questions = Question.objects.filter(exercise=exercise).count()
    attempt_list = list(ags.values_list('attempt_count', flat=True))
    med = 0 if (sum(attempt_list) == 0 or n_questions == 0) else median(attempt_list) / n_questions
    avg = 0 if len(attempt_list) == 0 else mean(attempt_list)
    avg = 0 if n_questions == 0 else avg / n_questions
    ed['name'] = esdata['name']
    ed['path'] = esdata['path']
    ed['ntried'] = ags.count()
    ed['percent_tried'] = 0 if nstudents == 0 else ed['ntried'] / nstudents
    ed['deadline'] = exercise.meta.deadline_date
    ed['ncorrect'] = ags.filter(user_is_correct=True).count()
    ed['percent_correct'] = 0 if nstudents == 0 else ed['ncorrect'] / nstudents
    ed['ncomplete'] = ags.filter(all_complete=True).count()
    ed['percent_complete'] = 0 if nstudents == 0 else ed['ncomplete'] / nstudents
    ed['attempts_mean'] = avg
    ed['attempts_median'] = med
    ed['nstudents'] = nstudents
    ed['response_awaits'] = ags.filter(audit_needs_attention=True).count()
    if cachekey:
        cache.set(cachekey, ed, settings.CACHE_LIFETIME)
    return ed


def calculate_student_statistics_exercises(course):
    '''
    DATA =  {'40fc7217-8832-48ac-8b81-d18c712a2d13': 
        {'name': 'asdfasdf', 'path': 'asdfasdf', 'ntried': 2, 'percent_tried': 1.0, 'percent_complete': 0.5, 
        'percent_correct': 0.5, 'ncomplete': 1, 'ncorrect': 1, 'nstudents': 2, 'deadline': 
        datetime.date(2019, 11, 9), 'response_awaits': 0, 'attempts_mean': 1.25, 'attempts_median': 1.25, 
        'activity': {'1h': 0, '24h': 0, '1w': 2, 'all': 2}}, 
        '78896b7c-c6e2-4045-bff4-4a76147b4a9f': ...
    AGGREGATES =  {'max_1h': 0, 'max_24h': 0, 'max_1w': 4, 'max_all': 6}
    }
    '''
    exercises = Exercise.objects.filter(course=course, meta__published=True)
    data = {}
    for exercise in exercises:
        data[exercise.exercise_key] = serialize_exercise_data_for_course(course, exercise)
        data[exercise.exercise_key]['activity'] = e_student_activity(exercise)['activity']
    # data  = exercise_list_data(
    #    [
    #        e_name,
    #        e_path,
    #        e_student_tried,
    #        e_student_percent_complete,
    #        has_audit_response_waiting,
    #        e_student_attempts_mean,
    #        e_student_attempts_median,
    #        e_student_activity,
    #    ],
    #    course=course,
    # )
    #
    aggregates = post_process_list(data, [p_student_activity])
    return {'exercises': data, 'aggregates': aggregates}


# stypes = ['number_complete','number_complete_by_deadline','number_correct','number_correct_by_deadline','number_image_by_deadline',


def get_exercises_render(user, course_pk):
    course = Course.objects.get(pk=course_pk)
    exercises = Exercise.objects.filter(meta__published=True, course=course)
    exercises_render = {}
    for exercise in exercises:
        item = serialize_exercise_with_question_data(exercise, user, False)
        exercises_render[exercise.exercise_key] = item['exercise_render']
    return exercises_render


def calculate_unsafe_user_summary(user_pk, course_pk, dbexercises):
    student = User.objects.get(pk=user_pk)
    course = Course.objects.get(pk=course_pk)
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time

    sums = get_unsafe_exercise_summary(user_pk, course_pk, dbexercises)
    required = sums['required']
    bonus = sums['bonus']
    optional = sums['optional']
    summary = {
        'username': student.username,
        'lti_user_id': student.opentauser.lti_user_id,
        'pk': student.pk,
        'first_name': student.first_name,
        'last_name': student.last_name,
        'required': required,  # {
        'bonus': bonus,
        'optional': optional,
        'n_optional': sums['n_optional'],
        'failed_by_audits': sums['failed_by_audits'],
        'passed_audits': sums['passed_audits'],
        'total_audits': sums['total_audits'],
        'manually_passed': sums['manually_passed'],
        'total': sums['total'],  # ags.filter(user_is_correct=True).count(),
        'total_complete_before_deadline': sums['total_complete_before_deadline'],
        'total_complete_no_deadline': sums['total_complete_no_deadline'],
    }
    if not dbexercises == None:
        summary['exercises'] = []
        for exercise in dbexercises:
            summary['exercises'].append(
                serialize_exercise_with_question_data(exercise, student, False)
            )
    return summary


def calculate_user_results(user_pk, course_pk):
    user = User.objects.get(pk=user_pk)
    course = Course.objects.get(pk=course_pk)
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    exercises_render = get_exercises_render(user, course_pk)
    summary = get_unsafe_exercise_summary(user_pk, course_pk, None)

    result = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'pk': user.pk,
        'lti_user_id': user.opentauser.lti_user_id,
        'exercises': exercises_render,
        'summary': summary,
    }
    return result
