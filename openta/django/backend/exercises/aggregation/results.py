# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
from django.core.exceptions import ObjectDoesNotExist
from course.models import pytztimezone
import logging
import time
from statistics import mean, median

from aggregation.models import Aggregation, get_cache_and_key
from course.models import Course
from exercises.modelhelpers import (
    bonafide_students,
    p_student_activity,
    post_process_list,
    serialize_exercise_with_question_data,
)
from exercises.models import Answer, Exercise, Question
from exercises.serializers import (
    ExerciseSerializer,
)
from exercises.views import get_unsafe_exercise_summary
from faker import Faker
from users.models import OpenTAUser

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import caches
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import to_locale

logger = logging.getLogger(__name__)


def students_results(cache_seconds=settings.STATISTICS_CACHE_TIMEOUT, force=False, task=None, course=None, has_perm=None,selected=[]):
    # logger.debug(f"STUDENTS_RESULTS WAS CALLED cache_secons={cache_seconds}")
    #logger.debug("DO STUDENTS_RESULTS COURSE = %s " % course)
    #logger.error(f"STUDENTS_RESULTS_SELECTED= {selected}")
    subdomain = task.subdomain
    # print(f"TASK = {task} {vars(task)} course={course}")
    (cache, cachekey) = get_cache_and_key("students_results:", coursePk=course.course_key, subdomain=subdomain)
    try:
        lang = course.languages.split(",")[0]
    except:
        lang = "en"
    locale = to_locale(lang)
    Faker.seed(0)
    fake = Faker(locale)
    result = None
    if not selected :
        result = cache.get(cachekey)
        #logger.error("STUDENTS_RESULT GOT FROM CACHE")
    # Determine permission reliably:
    # 1) use explicit argument if provided
    # 2) fall back to current job meta if available
    # 3) finally, legacy cache key as last resort
    if has_perm is None:
        try:
            from rq import get_current_job

            job = get_current_job()
            if job and isinstance(job.meta, dict):
                has_perm = job.meta.get("has_perm", None)
        except Exception:
            pass
    if has_perm is None and task is not None:
        antimigratekey = f"queutask-has-perm-{task.pk}"  # legacy fallback
        has_perm = caches["default"].get(antimigratekey, None)
    # print(f"has-perm {has_perm}")
    # print(f"COURSE = {course}")
    email_host = course.email_host
    if not "." in email_host:
        email_host = "example.com"
    # print(f"email_host = {email_host}")
    # users = User.objects.all()
    # for u in users:
    #    print(f"USER = {u} {u.has_perm}")
    # logger.error(f"STUDENT_RESULTS DO_CACHE={settings.DO_CACHE} USE_RESULTS_CACHE={settings.USE_RESULTS_CACHE} force={force} cachekey={cachekey}  ")
    if settings.DO_CACHE and settings.USE_RESULTS_CACHE and result is not None and not force:
        # result = [ item.update({'username': item['username'].upper()}) for item in result ]
        if not has_perm:
            for item in result:
                # print(f"ITEM = {item}")
                first = fake.first_name()
                last = fake.last_name()
                item["username"] = f"{first}.{last}@{email_host}".lower()
                item["first_name"] = first
                item["last_name"] = last

                # item['username'] = item[username] + 'ABC'
        # logger.error(f"RETURN {cachekey} FROM CACHE")
        # print(f" RESULT = {result}")
        return result

    # settings.DB_NAME = 'v320a'
    # settings.SUBDOMAIN = 'v320a'
    # logger.debug("SETTINGS DBNAME %s AND SUBDOMAIN  %s " % ( settings.DB_NAME, settings.SUBDOMAIN) )
    result = calculate_students_results(course=course, task=task,selected=selected)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result.append({"date": now})
    if cachekey and not selected:
        cache.set(cachekey, result, cache_seconds)
    # result = [ item.update({'username': item['username'].upper()}) for item in result ]
    if not has_perm:
        for item in result:
            # print(f"ITEM = {item}")
            first = fake.first_name()
            last = fake.last_name()
            item["username"] = f"{first}.{last}@chalmers.se".lower()
            item["first_name"] = first
            item["last_name"] = last
    #print(f"STUDENTS_RESULTS = {result}")
    return result


def student_statistics_exercises(
    cache_seconds=settings.STATISTICS_CACHE_TIMEOUT, force=False, course=None, source=None
):
    logger.debug(f"STUDENTS_STATISTICS_EXERCISES source = {source} ")
    logger.debug("STUDENTS_STATISTICS_EXERCISES %s %s " % (cache_seconds, settings.STATISTICS_CACHE_TIMEOUT))
    subdomain = settings.SUBDOMAIN
    (cache, cachekey) = get_cache_and_key(
        "student_statistics_exercises:", coursePk=course.course_key, subdomain=subdomain
    )
    logger.debug(f" STATISTICS TRY CACHEKEY = {cachekey}")
    try:
        logger.debug(f"STATISTICS DO_CACHE={settings.DO_CACHE} USE_RESULTS_CACHE={settings.USE_RESULTS_CACHE}")
        result = cache.get(cachekey)
        if settings.DO_CACHE and settings.USE_RESULTS_CACHE and result is not None and not force:
            logger.debug(f"STATISTICS CACHE FOUND for {cachekey}")
            return result
        else:
            result = calculate_student_statistics_exercises(course=course)
            logger.debug(f"STATISTICS RESULT RECALCULATED ")
        return result
    except ValueError as e:
        logger.debug(f"STATISTICS VALUE ERROR  RECALCULATE")
        result = calculate_student_statistics_exercises(course=course)
        return result


# @job('high')
# def testfunc() :
#    time.sleep(60)
#    testfile = open("/tmp/qfile.txt","a")
#    now = datetime.datetime.now()
#    testfile.write( now.strftime("%Y-%m-%d %H:%M:%S") )
#    testfile.write('\n')
#    testfile.close()


def calculate_students_custom_results(dbexercises, task, course):
    if task is not None:
        subdomain = task.subdomain
    else:
        subdomain = settings.SUBDOMAIN
    db = subdomain
    if settings.MULTICOURSE:
        from backend.middleware import verify_or_create_database_connection

        verify_or_create_database_connection(subdomain)
    students = (
        User.objects.using(subdomain).filter(groups__name="Student", opentauser__courses=course)
        .order_by("first_name")
    )
    results = []
    n_students = students.count()

    for index, student in enumerate(students):
        if task is not None:
            task.status = "Calculating custom results in aggregation.results.py "
            task.progress = round(((index + 1) / n_students) * 100)
            task.save(using='default')
        summary = calculate_unsafe_user_summary(student.pk, course.id, subdomain, dbexercises)
        results.append(summary)
        if True or logger.isEnabledFor(logging.DEBUG):
            logger.debug("Adding custom result for %s  entries = %s " % (student.username, len(str(summary))))
            # if dbexercises:
            #    logger.debug(
            #        "CALCULATE STUDENTS CUSTOM RESULTS DBEXERCISEDS " + str(dbexercises.count())
            #    )
    return results


def calculate_students_results(course, task=None,selected=[]):
    if task == None:
        subdomain = course.opentasite
    else:
        subdomain = task.subdomain
    if settings.MULTICOURSE and not settings.RUNTESTS:
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        from backend.middleware import verify_or_create_database_connection

        verify_or_create_database_connection(subdomain)
        # logger.error("CALCULATE STUDENTS_RESULTS DB_NAME = %s " % settings.DB_NAME)
        db = subdomain
    else:
        db = "default"
    students = (
        User.objects.using(db).filter(groups__name="Student", opentauser__courses=course)
    )
    results = []
    n_students = students.count()
    #logger.error(f"nstudents = {n_students}")
    for index, student in enumerate(students):
        if task is not None:
            task.status = "Calculating results in aggregation.results.py "
            task.progress = round(((index + 1) / n_students) * 100)
            task.save(using='default')
        summary = calculate_unsafe_user_summary(student.pk, course.id, subdomain, None, selected )
        results.append(summary)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Adding %s result for %s  " % (len(summary), student.username))
    # logger.error(json.dumps(results, indent=2))
    return results


def serialize_exercise_data_for_course(course, exercise):
    # logger.debug(f"SERIALIZE EXERCISE_DATA_FOR_COURSE {exercise}")
    subdomain = course.opentasite
    db = subdomain
    (cache, cachekey) = get_cache_and_key(
        "exercise_data_for_course:", coursePk=course.course_key, exercise_key=exercise.exercise_key, subdomain=subdomain
    )
    if settings.DO_CACHE and settings.USE_RESULTS_CACHE and cache.has_key(cachekey):
        # logger.debug("FOUND CACHE")
        return cache.get(cachekey)
    users = bonafide_students.filter(opentauser__courses=course)
    nstudents = users.count()
    try:
        serializer = ExerciseSerializer(exercise)
        esdata = serializer.data
        exercise_key = esdata["exercise_key"]
    except Exception as e:
        db = course.opentasite
        logger.error(
            f"ERROR IN SERIALIZE_EXERCISE_DATA type={type(e).__name__} {str(e)} subdomain={subdomain} course={course} exercise={exercise}"
        )
        exercise = (
            Exercise.objects.using(db).select_related("meta").get(exercise_key=exercise.exercise_key, course=course)
        )
        serializer = ExerciseSerializer(exercise)
        esdata = serializer.data
        exercise_key = esdata["exercise_key"]
        logger.error(
            f"RECOVERED ERROR IN SERIALIZE_EXERCISE_DATA course={course} exercise={exercise} meta={exercise.meta}"
        )
    ed = {}
    ags = Aggregation.objects.using(db).filter(course=course, exercise=exercise, user__in=users)
    n_questions = Question.objects.using(db).filter(exercise=exercise).count()
    attempt_list = list(ags.values_list("attempt_count", flat=True))
    med = 0 if (sum(attempt_list) == 0 or n_questions == 0) else median(attempt_list) / n_questions
    avg = 0 if len(attempt_list) == 0 else mean(attempt_list)
    avg = 0 if n_questions == 0 else avg / n_questions
    ed["name"] = esdata["name"]
    ed["path"] = esdata["path"]
    ed["ntried"] = ags.count()
    ed["percent_tried"] = 0 if nstudents == 0 else ed["ntried"] / nstudents
    try:
        ed["deadline"] = exercise.meta.deadline_date
    except:
        ed["deadline"] = None
    ed["ncorrect"] = ags.filter(user_is_correct=True).count()
    ed["percent_correct"] = 0 if nstudents == 0 else ed["ncorrect"] / nstudents
    ed["ncomplete"] = ags.filter(all_complete=True).count()
    ed["percent_complete"] = 0 if nstudents == 0 else ed["ncomplete"] / nstudents
    ed["attempts_mean"] = avg
    ed["attempts_median"] = med
    ed["nstudents"] = nstudents
    ed["response_awaits"] = ags.filter(audit_needs_attention=True).count()
    if cachekey:
        cache.set(cachekey, ed, settings.SERIALIZE_EXERCISE_DATA_FOR_COURSE_TIMEOUT)
    logger.debug(f"RECOMPUTED CACHE {cachekey} ")
    return ed


def calculate_student_statistics_exercises(course):
    """
    DATA =  {'40fc7217-8832-48ac-8b81-d18c712a2d13':
        {'name': 'asdfasdf', 'path': 'asdfasdf', 'ntried': 2, 'percent_tried': 1.0, 'percent_complete': 0.5,
        'percent_correct': 0.5, 'ncomplete': 1, 'ncorrect': 1, 'nstudents': 2, 'deadline':
        datetime.date(2019, 11, 9), 'response_awaits': 0, 'attempts_mean': 1.25, 'attempts_median': 1.25,
        'activity': {'1h': 0, '24h': 0, '1w': 2, 'all': 2}},
        '78896b7c-c6e2-4045-bff4-4a76147b4a9f': ...
    AGGREGATES =  {'max_1h': 0, 'max_24h': 0, 'max_1w': 4, 'max_all': 6}
    }
    """
    x = datetime.datetime.now()
    subdomain = course.opentasite
    db = subdomain
    (cache, cachekey) = get_cache_and_key(
        "student_statistics_exercises:", coursePk=course.course_key, subdomain=subdomain
    )
    # print(f" DO_CACHE = { settings.DO_CACHE } USE_RESULTS_CACHE = {settings.USE_RESULTS_CACHE} cachekey={cachekey} ")
    if settings.DO_CACHE and settings.USE_RESULTS_CACHE and cache.has_key(cachekey):
        # logger.error(f"{x} FOUND CACHE CALCULATE_STUDENT_STATISTICS_TIMEOUT")
        return cache.get(cachekey)
    exercises = Exercise.objects.using(db).select_related("meta").filter(course=course, meta__published=True)
    data = {}
    t0 = time.time()
    for exercise in exercises:
        s = serialize_exercise_data_for_course(course, exercise)
        if s:
            data[exercise.exercise_key] = s
            data[exercise.exercise_key]["activity"] = {"1h": 0, "24h": 0, "1w": 0, "all": 0}
    t1 = time.time()
    t2 = time.time()
    tz = pytztimezone(settings.TIME_ZONE)
    minnow = datetime.datetime.now().astimezone(tz)
    # all_answers = Answer.objects.filter(user__groups__name="Student" )\
    #        .annotate(trunctime=Trunc('date','m',output_field=DateTimeField() )) \
    #        .values('trunctime','question__exercise') \
    #        .annotate(bins=Count('id') ) \
    #        .order_by('question__exercise','-trunctime') \
    #        .values_list('trunctime','bins','question__exercise')
    t5 = time.time()
    dt1 = t1 - t0
    n_questions = dict(Exercise.objects.using(db).annotate(qs=Count("question__exercise")).values_list("exercise_key", "qs"))
    t1h = timezone.now() - datetime.timedelta(hours=1)
    t24h = timezone.now() - datetime.timedelta(hours=24)
    t1w = timezone.now() - datetime.timedelta(days=7)
    answers = Answer.objects.using(db).filter(user__groups__name="Student")
    activity_all = dict(Exercise.objects.using(db).annotate(qs=Count("question__answer")).values_list("exercise_key", "qs"))
    answers = answers.filter(date__gt=t1w)
    activity_t1w = dict(
        Exercise.objects.using(db).filter(question__answer__in=answers)
        .annotate(qs=Count("question__answer"))
        .values_list("exercise_key", "qs")
    )
    answers = answers.filter(date__gt=t24h)
    activity_t24h = dict(
        Exercise.objects.using(db).filter(question__answer__in=answers)
        .annotate(qs=Count("question__answer"))
        .values_list("exercise_key", "qs")
    )
    answers = answers.filter(date__gt=t1h)
    activity_t1h = dict(
        Exercise.objects.using(db).filter(question__answer__in=answers)
        .annotate(qs=Count("question__answer"))
        .values_list("exercise_key", "qs")
    )
    t6 = time.time()
    dt1 = t1 - t0
    dt6 = t6 - t5
    for e in data.keys():
        e_all = round(activity_all.get(e, 0) / max(n_questions.get(e, 1), 1))
        e_t1w = round(activity_t1w.get(e, 0) / max(n_questions.get(e, 1), 1))
        e_t24h = round(activity_t24h.get(e, 0) / max(n_questions.get(e, 1), 1))
        e_t1h = round(activity_t1h.get(e, 0) / max(n_questions.get(e, 1), 1))
        data[e]["activity"] = {"1h": e_t1h, "24h": e_t24h, "1w": e_t1w, "all": e_all}

    x = datetime.datetime.now()
    # logger.error(f"{x} TIMING CALCULATE_STUDENT_STATISTICS_EXERCISES {x} DT1={dt1} DT6={dt6}")
    aggregates = post_process_list(data, [p_student_activity])
    result = {"exercises": data, "aggregates": aggregates}
    (cache, cachekey) = get_cache_and_key(
        "student_statistics_exercises:", coursePk=course.course_key, subdomain=subdomain
    )
    cache.set(cachekey, result, settings.STUDENTS_STATISTICS_CACHE_TIMEOUT)
    return result


# stypes = ['number_complete','number_complete_by_deadline','number_correct','number_correct_by_deadline','number_image_by_deadline',


def get_exercises_render(user, course_pk, db=None):
    assert db != None, "GET_EXERCISES_RENDER db=None"
    course = Course.objects.using(db).get(pk=course_pk)
    exercises = Exercise.objects.using(db).filter(course=course)
    exercises_render = {}
    for exercise in exercises:
        try :
            item = serialize_exercise_with_question_data(exercise, user, False, db=db)
            if "exercise_render" in item:
                exercises_render[exercise.exercise_key] = item["exercise_render"]
        except  ObjectDoesNotExist as e :
            pass;

    return exercises_render


def get_exercise_render(user, course_pk, exercise, db=None):
    course = Course.objects.using(db).get(pk=course_pk)
    db = course.opentasite
    exercises_render = {}
    item = serialize_exercise_with_question_data(exercise, user, False, db=db)
    exercises_render[exercise.exercise_key] = item["exercise_render"]
    return exercises_render


def calculate_unsafe_user_summary(user_pk, course_pk, subdomain, dbexercises,selected=[]):
    db = 'default' if settings.RUNTESTS else subdomain
    if settings.MULTICOURSE:
        if not subdomain == settings.SUBDOMAIN:
            student = User.objects.using(db).get(pk=user_pk)
            msg = f"ERROR inconsistent subdomain CALCULATE_UNSAFE_USER_SUMMARY {user_pk} {student.username} {subdomain} {settings.SUBDOMAIN}"
            logger.error(msg)
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
    student = User.objects.using(db).get(pk=user_pk)
    course = Course.objects.using(db).get(pk=course_pk)
    tz = pytztimezone(settings.TIME_ZONE)
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    # logger.debug("CALCULATE_UNSAFE_USER_SUMMARY %s " % len( str( dbexercises )) )
    sums = get_unsafe_exercise_summary(user_pk, course_pk, dbexercises, db, selected)
    required = sums["required"]
    bonus = sums["bonus"]
    optional = sums["optional"]
    queries = Answer.objects.using(subdomain).filter(user=student)
    total_queries = queries.count()
    total_correct_queries = queries.filter(correct=True).count()
    summary = {
        "username": student.username,
        "lti_user_id": student.opentauser.lti_user_id,
        "pk": student.pk,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "required": required,  # {
        "bonus": bonus,
        "optional": optional,
        "n_optional": sums["n_optional"],
        "failed_by_audits": sums["failed_by_audits"],
        "passed_audits": sums["passed_audits"],
        "total_audits": sums["total_audits"],
        "manually_passed": sums["manually_passed"],
        "total": sums["total"],  # ags.filter(user_is_correct=True).count(),
        "total_complete_before_deadline": sums["total_complete_before_deadline"],
        "total_complete_no_deadline": sums["total_complete_no_deadline"],
        "total_queries": total_queries,
        "total_correct_queries": total_correct_queries,
    }
    if not dbexercises == None:
        summary["exercises"] = []
        for exercise in dbexercises:
            summary["exercises"].append(
                serialize_exercise_with_question_data(exercise, student, False, db=settings.DB_NAME)
            )
    return summary


def calculate_user_results(user_pk, course_pk, db=None):
    assert db != None, "CALCULATE_USER_RESULTS DB=None"
    logger.debug("CALCULATE_USER_RESULTS")
    user = User.objects.using(db).get(pk=user_pk)
    course = Course.objects.using(db).get(pk=course_pk)
    tz = pytztimezone(settings.TIME_ZONE)
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    exercises_render = get_exercises_render(user, course_pk, db=db)
    summary = get_unsafe_exercise_summary(user_pk, course_pk, None, db)

    result = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "pk": user.pk,
        "lti_user_id": user.opentauser.lti_user_id,
        "exercises": exercises_render,
        "summary": summary,
    }
    return result


def calculate_user_exercise_results(user_pk, course_pk, exercise, db=None):
    assert db != None, "CALCULATE_USER_EXERCISE_RESULTS DB=None"
    user = User.objects.using(db).get(pk=user_pk)
    opentauser, _ = OpenTAUser.objects.using(db).get_or_create(user=user)
    course = Course.objects.using(db).get(pk=course_pk)
    tz = pytztimezone(settings.TIME_ZONE)
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    exercises_render = get_exercise_render(user, course_pk, exercise, db=db)
    summary = get_unsafe_exercise_summary(user_pk, course_pk, None, db)
    #logger.error(f"SUMMARY = {summary}")
    if not opentauser.lti_user_id:
        lti_user_id = None
    else:
        lti_user_id = opentauser.lti_user_id

    result = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "pk": user.pk,
        "lti_user_id": lti_user_id,
        "exercises": exercises_render,
        "summary": summary,
    }
    return result
