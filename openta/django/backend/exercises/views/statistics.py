# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from rest_framework.decorators import api_view
from django.utils import timezone
from django.contrib.auth.models import User, Group, Permission
from django.views.decorators.cache import cache_control

import hashlib
from utils import get_subdomain_and_db
from django.views.decorators.http import condition, etag

# import openpyxl
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from aggregation.models import get_cache_and_key
from django.core.cache import caches
from exercises.models import Exercise, Answer, Question, ImageAnswer, AuditExercise
from exercises.aggregation import student_statistics_exercises, students_results
from exercises.aggregation import create_xlsx_from_results_list
from exercises.aggregation import excel_custom_results_pipeline, students_results_async_pipeline
from course.models import Course
from workqueue.models import QueueTask
import workqueue.util as workqueue
from workqueue.exceptions import WorkQueueError
from datetime import datetime, timedelta
import time
from django.conf import settings
from datetime import datetime
from django.db.models import Count, DateTimeField
from django.db.models.functions import Trunc
import logging

logger = logging.getLogger(__name__)

import numpy
from messages import error, embed_messages


#
# return a stale etag  for one minute after time has expired
# so that admin does not have to wait for about 15 seconds
# every time
#


# def disable_get_statistics_etag(request, course_pk) : # FIXME The delay is pointless since student_statistics_exercises is not async
#    logger.info("GET STATISTICS ETAG")
#    if settings.MULTICOURSE :
#        course = Course.objects.get(pk=course_pk,opentasite=settings.SUBDOMAIN)
#    else :
#        course = Course.objects.get(pk=course_pk )
#    (cache, cachekey) = get_cache_and_key('student_statistics_exercises:', coursePk=course.course_key)
#    etag = (hashlib.md5(cachekey.encode()).hexdigest())[0:7]
#    deltat = 0
#    if 'student_statistics_exercises_timer' in request.session :
#        deltat = time.time() - request.session['student_statistics_exercises_timer']
#    else :
#        request.session['student_statistics_exercises_timer'] = time.time()
#    logger.info(f"DELTAT = {deltat}")
#    if cache.get(cachekey) :
#        request.session['student_statistics_exercises_timer'] = time.time()
#        logger.info(f"RETURN1 etag = {etag}")
#        return etag
#    else :
#        if deltat < 60.0 :
#            logger.info(f"RETURN2 etag = {etag} deltat={deltat}")
#            return etag
#    logger.info(f"RETURN3 etag = None ")onClick={() => onGenerateResults(exerciseState, activeCourse)}
#    return None
#
#
# def get_statistics_etag(request, course_pk) :
#    #logger.info("GET STATISTICS ETAG")
#    if settings.MULTICOURSE :
#        course = Course.objects.get(pk=course_pk,opentasite=settings.SUBDOMAIN)
#    else :
#        course = Course.objects.get(pk=course_pk )
#    (cache, cachekey) = get_cache_and_key('student_statistics_exercises:', coursePk=course.course_key)
#    etag = (hashlib.md5(cachekey.encode()).hexdigest())[0:7]
#    if cache.get(cachekey) :
#        #logger.info(f"RETURN1 etag = {etag}")
#        return etag
#    else :
#        #logger.info(f"RETURNING NONE")
#        return None


@permission_required("exercises.view_statistics")
@api_view(["GET"])
@cache_control(private=True, max_age=settings.STATISTICS_CACHE_TIMEOUT)
def get_statistics_per_exercise(request, course_pk):
    x = datetime.now()
    subdomain, db = get_subdomain_and_db(request)
    # print(f"{x} CALCULATE_STUDENT_STATISTGICS_EXERCISES")
    (cache, cachekey) = get_cache_and_key("student_statistics_exercises:", coursePk=course_pk, subdomain=subdomain)
    if settings.DO_CACHE and settings.USE_RESULTS_CACHE and cache.has_key(cachekey):
        # print(f"{x} FOUND CACHE CALCULATE_STUDENT_STATISTICS_TIMEOUT")
        return Response(cache.get(cachekey))

    # print(f"RECOMPUTE STATISTICS USE_RESULTS_CACHE={settings.USE_RESULTS_CACHE} DO_CACHE={settings.DO_CACHE} ")
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    try :
        result = student_statistics_exercises(course=dbcourse, source="get_statistics_per_exercise")
        (cache, cachekey) = get_cache_and_key("student_statistics_exercises:", coursePk=course_pk, subdomain=subdomain)
        cache.set(cachekey, result, settings.STUDENTS_STATISTICS_CACHE_TIMEOUT)
    except :
        result = {}
    return Response(result)


@permission_required("exercises.view_statistics")
@api_view(["GET"])
# @cache_control(private=True, max_age=settings.STATISTICS_CACHE_TIMEOUT)
def get_course_statistics(request, course_pk, activityRange="all"):
    # print(f"activityRange={activityRange}")
    subdomain, db = get_subdomain_and_db(request)
    logger.info(f"GET_COURSE_STATISTICS {course_pk} ")
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    required = Exercise.objects.using(db).filter(meta__required=True)
    bonus = Exercise.objects.using(db).filter(meta__bonus=True)
    optional = Exercise.objects.using(db).filter(meta__required=False, meta__bonus=False)
    questions = {}
    questions["required"] = Question.objects.using(db).filter(exercise__in=required).exclude(type='aibased')
    questions["optional"] = Question.objects.using(db).filter(exercise__in=optional).exclude(type='aibased')
    questions["bonus"] = Question.objects.using(db).filter(exercise__in=bonus).exclude(type='aibased')
    questions["aibased"] = Question.objects.using(db).filter(type='aibased')
    dts = {}
    dts["1h"] = timezone.now() - timedelta(hours=1)
    dts["24h"] = timezone.now() - timedelta(hours=24)
    dts["1w"] = timezone.now() - timedelta(days=7)
    dts["all"] = timezone.now() - timedelta(days=1000)
    answer_dicts = {}
    answers = {}
    answers_truncated = {}
    old_use_tz = settings.USE_TZ
    settings.USE_TZ = False
    ttimes = {}
    ttimes["all"] = "hour"
    ttimes["1h"] = "minute"
    ttimes["1w"] = "hour"
    ttimes["24h"] = "minute"
    ttime = ttimes.get(activityRange, "all")
    dt = dts.get(activityRange, "all")
    fmts = {}
    fmts["all"] = "%Y-%m-%d:%H"
    fmts["1h"] = "%H:%M"
    fmts["1w"] = "%m-%d:%H"
    fmts["24h"] = "%H:%M"
    fmt = fmts.get(activityRange, "%Y-%m-%d:%H")

    for qtype in ["required", "optional", "bonus","aibased"]:
        q = questions[qtype]
        answers[qtype] = (
            Answer.objects.using(db)
            .filter(date__gt=dt, question__in=q)
            .annotate(trunctime=Trunc("date", ttime, output_field=DateTimeField()))
            .values("trunctime")
            .annotate(bins=Count("id"))
            .order_by("trunctime")
            .values("trunctime", "bins")
        )
        answer_dicts[qtype] = [{item["trunctime"].strftime(fmt): item["bins"]} for item in answers[qtype]]
    answers["all"] = (
        Answer.objects.using(db)
        .filter(date__gt=dt)
        .annotate(trunctime=Trunc("date", ttime, output_field=DateTimeField()))
        .values("trunctime")
        .annotate(bins=Count("id"))
        .order_by("trunctime")
        .values("trunctime", "bins")
    )
    answer_dicts["all"] = [{item["trunctime"].strftime(fmt): item["bins"]} for item in answers["all"]]
    exercises = Exercise.objects.using(db).filter(course=course_pk)
    image_answers = ImageAnswer.objects.using(db).filter(date__gt=dt, exercise__in=exercises)
    audits = AuditExercise.objects.using(db).filter(date__gt=dt, exercise__in=exercises)
    answer_dicts["summary"] = {
        "image_answers": str(image_answers.count()),
        "audits": str(audits.count()),
        "activityRange": activityRange,
    }
    settings.USE_TZ = old_use_tz
    # print(f"{answer_array.get('optional',None)}"  )
    # for answer in answers:
    #    trunctime = answer['trunctime']
    #    for qtype in ['required','optional','bonus'] :
    #        answer_dicts[qtype][trunctime] =  answer_dicts[qtype].get(trunctime,0)
    # print(f"ANSWERS = {answer_dict}")
    # print(f"LENGTH = {len(answer_dict)}")
    # print( answers_truncated['optional'] )
    # for answer in answers_truncated_all  :
    #        trunctime = answer['trunctime']
    #        for qtype in ['required','optional','bonus'] :
    #            answers_truncated[qtype][trunctime] = answers_truncated[qtype].get(trunctime,0)
    # for qtype in ['required','optional','bonus'] :
    #    answer_dicts[qtype]  = [ { item['trunctime'].strftime('%Y-%m-%d:%H') : item['bins'] }  for item in answers_truncated[qtype] ]

    return Response(answer_dicts)


@permission_required("exercises.view_statistics")
@api_view(["GET","POST"])
def get_results_async(request, course_pk):
    subdomain, db = get_subdomain_and_db(request)
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    subdomain = settings.SUBDOMAIN
    logger.info("GET RESULTS ASYNC SUBDOMAIN = %s " % subdomain)
    # pss = Permission.objects.all().values_list('codename',flat=True)
    username = request.user.username
    user = User.objects.using(db).get(username=username)
    user = request.user
    # pss = user.get_all_permissions()
    has_perm = request.user.has_perm("exercises.view_student_id")
    # for ps in pss :
    #    print(f'"{ps}"' )
    # print(f"HAS_PERM={has_perm}")
    cachekey = request.user.username + db + 'selectedExercises'
    selected = caches['default'].get(cachekey)
    try:
        task_id = workqueue.enqueue_task(
            "student_results",
            students_results_async_pipeline,
            course=dbcourse,
            subdomain=subdomain,
            username=request.user.username,
            has_perm=has_perm,
            selected=selected,
        )
        return Response({"task_id": task_id})
    except WorkQueueError as e:
        messages = embed_messages([error(str(e))])
        return Response(messages)


@permission_required("exercises.view_statistics")
@api_view(["GET", "POST"])
def get_results_excel(request, course_pk):
    subdomain, db = get_subdomain_and_db(request)
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    dbexercises = Exercise.objects.using(db).filter(course_id=course_pk, meta__published=True)
    task_id = workqueue.enqueue_task("Custom results", excel_custom_results_pipeline, dbexercises, course=dbcourse)
    return Response({"task_id": task_id})


@permission_required("exercises.view_statistics")
@api_view(["GET", "POST"])
def enqueue_custom_result_excel(request, course_pk):
    subdomain, db = get_subdomain_and_db(request)
    exercises = None
    if request.method == "GET":
        # print("GET", str( request.query_params ) )
        exercises = request.query_params.get("exercises").split(",")
    if request.method == "POST":
        # logger.info("POST", str( request.data ) )
        exercises = request.data.get("exercises")
    if exercises is None:
        return Response({})

    dbcourse = Course.objects.using(db).get(pk=course_pk)
    dbexercises = Exercise.objects.using(db).filter(exercise_key__in=exercises)
    # logger.info("DBEXERCISES = ", list( dbexercises.values_list('exercise_key', flat=True) ) )
    task_id = workqueue.enqueue_task("Custom results", excel_custom_results_pipeline, dbexercises, course=dbcourse)
    return Response({"task_id": task_id})


@permission_required("exercises.view_statistics")
@api_view(["GET"])
def progress_custom_result_excel(request, task):
    subdomain, db = get_subdomain_and_db(request)
    dbtask = QueueTask.objects.using('default').get(pk=task)
    return Response({"status": dbtask.status, "progress": dbtask.progress, "done": dbtask.done})


@permission_required("exercises.view_statistics")
@api_view(["GET"])
def get_activity_exercise(request, exercise):
    # print(f"GET ACTIVITY EXERCISE")
    subdomain, db = get_subdomain_and_db(request)
    answers = Answer.objects.using(db).filter(question__exercise__pk=exercise)
    # print(f"ANSWSERS = {answers}")

    answer_list = answers.values_list("date", flat=True)
    if not answer_list:
        return Response({"answers_histogram": [], "bins": []})

    to_timestamp = numpy.vectorize(lambda x: x.timestamp())
    answer_ts_array = to_timestamp(answer_list)
    nbins = int((numpy.max(answer_ts_array) - numpy.min(answer_ts_array)) / (2 * 60 * 60)) + 1
    bins = []
    histogram = []
    if nbins > 0:
        histogram, bins = numpy.histogram(answer_ts_array, bins=nbins)
    return Response({"answers_histogram": histogram, "bins": bins})
