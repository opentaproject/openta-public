# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json
from django.core.cache import caches
from django.views.decorators.csrf import csrf_exempt
import datetime

from copy import deepcopy
from exercises.applymacros import macrolist_to_dict
from backend.views import get_sidecar_count
import html
import os
import re
from django.shortcuts import redirect
import shutil
import tempfile
import time
import traceback
from exercises.utils.checks import get_extradefs
import urllib.parse

from aggregation.models import (
    Aggregation,
    agkeys,
    get_cache_and_key,
    stypes,
    t_cache_and_key,
)
from course.models import Course
from exercises import parsing
from exercises.applymacros import (
    MacroError,
    apply_macros_to_exercise,
    apply_macros_to_node,
)
from exercises.models import (
    Answer,
    Exercise,
    ExerciseMeta,
    ImageAnswer,
    Question,
    function_qtype
)
from exercises.question import QuestionError
from exercises.serializers import (
    AnswerSerializer,
    ExerciseSerializer,
    ImageAnswerSerializer,
)
from exercises.utils.string_formatting import declash
from pdf2image import convert_from_path
from PIL import UnidentifiedImageError
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from translations.models import Translation
from translations.views import fromString, translate_xml_language
from users.models import User

import django
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.transaction import TransactionManagementError
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import etag

upload_storage = FileSystemStorage(location=settings.VOLUME, base_url="/")
from utils import get_subdomain, get_subdomain_and_db, get_subdomain_and_db_and_user

# def get_subdomain(request ):
#    return request.META['HTTP_HOST'].split('.')[0]

def contains_symlink(path):
    # Resolve the absolute path and split into individual components
    abs_path = os.path.abspath(path)
    components = abs_path.split(os.sep)

    # Traverse through the path one directory at a time
    for i in range(2, len(components) + 1):  # Start from 2 to skip empty string for root
        sub_path = os.sep.join(components[:i])
        if os.path.islink(sub_path) and i > 2 :
            return True, f"{i} {sub_path}" # Found a symlink, return it
    return False, None  # No symlink found



def get_json(obj):
    return json.loads(json.dumps(obj, default=lambda o: getattr(o, "__dict__", str(o))))


# from exercises.questiontypes.dev_linear_algebra.string_formatting import (
#    absify,
#    insert_implicit_multiply,
#    ascii_to_sympy,
#    matrixify,
#    braketify,
#    declash,
# )

import datetime
import hashlib
import json
import logging
import os
import os.path
import re as reg
import time

import exercises.paths as paths
import exercises.question as question_module
import pypdf
from django_ratelimit.decorators import ratelimit
from exercises.folder_structure.modelhelpers import exercise_folder_structure
from exercises.modelhelpers import exercise_test, serialize_exercise_with_question_data, get_selectedExercisesKeys, set_selectedExercisesKeys
from exercises.parsing import (
    exercise_xml_to_json,
    question_json_get_from_raw_json,
)
from exercises.question import (
    get_combined_usermacros,
    get_usermacros,
)
from exercises.questiontypes.dev_linear_algebra.linear_algebra import (
    linear_algebra_compare_expressions,
)
from exercises.questiontypes.symbolic.symbolic import symbolic_compare_expressions
from exercises.questiontypes.basic import compare_expressions as basic_compare_expressions
from exercises.questiontypes.matrix import compare_expressions as matrix_compare_expressions
from exercises.questiontypes.default import compare_expressions as default_compare_expressions

from exercises.time import before_deadline
from exercises.util import deep_get, get_hash_from_string
from exercises.utils.variableparser import (
    getallglobalvariables,
    parse_xml_functions,
    parse_xml_variables,
)
from exercises.views.file_handling import serve_file
from lxml import etree
from PIL import Image
from utils import response_from_messages

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.cache import cache, caches
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, StreamingHttpResponse
from django.template import loader
from django.template.response import TemplateResponse
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache

compare_function = {}
compare_function["symbolic"] = symbolic_compare_expressions
compare_function["basic"] = basic_compare_expressions
compare_function["default"] = default_compare_expressions
compare_function["matrix"] = matrix_compare_expressions
compare_function["devLinearAlgebra"] = linear_algebra_compare_expressions
compare_function["linearAlgebra"] = linear_algebra_compare_expressions
compare_function["compareNumeric"] = linear_algebra_compare_expressions
compare_function["Numeric"] = linear_algebra_compare_expressions

validate_question_function = {};




logger = logging.getLogger(__name__)


@permission_required("exercises.reload_exercise")
@api_view(["POST", "GET"])
def exercises_reload_streaming(request, course_pk):
    subdomain, db , user = get_subdomain_and_db_and_user(request)
    try:
        dbcourses = Course.objects.using(db).filter(pk=course_pk)
        dbcourse = dbcourses[0];

    except Course.DoesNotExist:
        logger.error("Requested course does not exist pk: %d", course_pk)
        return Response({"error": "Invalid course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    use_auto_translation = dbcourse.use_auto_translation
    if use_auto_translation :
        dbcourses.update(use_auto_translation=False);
    exercises = Exercise.objects.using(db).sync_with_disc(dbcourse)

    base = loader.get_template("base_streaming.html")

    def next_exercise():
        yield base.render()
        for progress in exercises:
            rendered = loader.render_to_string("reload_progress.html", {"progress": progress})
            yield rendered

    if use_auto_translation :
        dbcourses.update(use_auto_translation=True)

    return StreamingHttpResponse(next_exercise())


@permission_required("exercises.reload_exercise")
@api_view(["POST", "GET"])
def exercises_validate_streaming(request, course_pk):
    subdomain = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    settings.SUBDOMAIN = get_subdomain(request)
    try:
        dbcourses = Course.objects.using(db).filter(pk=course_pk)
        dbcourse = dbcourses[0];

    except Course.DoesNotExist:
        logger.error("Requested course does not exist pk: %d", course_pk)
        return Response({"error": "Invalid course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    use_auto_translation = dbcourse.use_auto_translation
    if use_auto_translation :
        dbcourses.update(use_auto_translation=False);
    exercises = Exercise.objects.validate_all(dbcourse)

    base = loader.get_template("base_streaming.html")

    def next_exercise():
        yield base.render()
        for progress in exercises:
            rendered = loader.render_to_string("validate_progress.html", {"progress": progress})
            yield rendered

    if use_auto_translation :
        dbcourses.update(use_auto_translation=True)

    return StreamingHttpResponse(next_exercise())




@permission_required("exercises.reload_exercise")
@api_view(["POST", "GET"])
def exercises_reload(request, course_pk):
    subdomain = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    i_am_sure = request.data.get("i_am_sure", False)
    try:
        dbcourses = Course.objects.using(db).filter(pk=course_pk)
        dbcourse = dbcourses[0];
    except Course.DoesNotExist:
        logger.error("Requested course does not exist pk: %d", course_pk)
        return Response({"error": "Invalid course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    use_auto_translation = dbcourse.use_auto_translation
    if use_auto_translation :
        dbcourses.update(use_auto_translation=False);

    @transaction.atomic(using="default")
    def sync():
        mess = []
        exercises = Exercise.objects.sync_with_disc(dbcourse, i_am_sure)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    if use_auto_translation :
        dbcourses.update(use_auto_translation=True);
    return render(request._request, "exercises_reload.html", {"progress": mess})

@permission_required("exercises.reload_exercise")
@api_view(["POST", "GET"])
def exercises_validate(request, course_pk):
    subdomain = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    i_am_sure = True
    try:
        dbcourses = Course.objects.using(db).filter(pk=course_pk)
        dbcourse = dbcourses[0];
    except Course.DoesNotExist:
        logger.error("Requested course does not exist pk: %d", course_pk)
        return Response({"error": "Invalid course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic(using="default")
    def sync():
        mess = []
        exercises = Exercise.objects.validate_all(dbcourse, i_am_sure)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    return render(request._request, "exercises_validate.html", {"progress": mess})





@api_view(["POST", "GET"])
def exercises_reload_json(request, course_pk):
    #print(f"RELOAD_JSON")
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    db = subdomain
    settings.SUBDOMAIN = subdomain
    settings.DB = subdomain
    if not request.user.has_perm("exercises.reload_exercise"):
        raise PermissionDenied(_("Permission denied"))
    i_am_sure = request.data.get("i_am_sure", False)
    try:
        dbcourses = Course.objects.using(db).filter(pk=course_pk)
        dbcourse = dbcourses[0]
        logger.info(f"DBCOURSE = {dbcourse}")
    except Course.DoesNotExist:
        logger.error("Requested course does not exist pk: %d", course_pk)
        return Response({"error": "Invalid course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    use_auto_translation = dbcourse.use_auto_translation
    if use_auto_translation :
        dbcourses.update(use_auto_translation=False);

    @transaction.atomic(using=subdomain)
    def sync():
        mess = []
        exercises = Exercise.objects.sync_with_disc(dbcourse, i_am_sure=True, db=subdomain)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    if use_auto_translation :
        dbcourses.update(use_auto_translation=True);
    return Response(mess)


@api_view(["POST", "GET"])
def exercises_validate_json(request, course_pk):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    db = subdomain
    settings.SUBDOMAIN = subdomain
    settings.DB = subdomain
    if not request.user.has_perm("exercises.reload_exercise"):
        raise PermissionDenied(_("Permission denied"))
    i_am_sure = request.data.get("i_am_sure", False)
    try:
        dbcourses = Course.objects.using(db).filter(pk=course_pk)
        dbcourse = dbcourses[0]
        logger.info(f"DBCOURSE = {dbcourse}")
    except Course.DoesNotExist:
        logger.error("Requested course does not exist pk: %d", course_pk)
        return Response({"error": "Invalid course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #use_auto_translation = dbcourse.use_auto_translation
    #if use_auto_translation :
    #    dbcourses.update(use_auto_translation=False);

    @transaction.atomic(using=subdomain)
    def sync():
        mess = []
        exercises = Exercise.objects.validate_all(dbcourse, i_am_sure=True, db=subdomain)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    #if use_auto_translation :
    #    dbcourses.update(use_auto_translation=True);
    return Response(mess)




@never_cache
@api_view(["GET"])
def exercise(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    try :
        er = "A0 - " + settings.SUBDOMAIN
        data = {}
        dbexercise = Exercise.objects.using(db).select_related("meta", "course").get(exercise_key=exercise)
        er += " A1- " + settings.SUBDOMAIN
        hijacked = request.session.get("hijacked", False)
        er += " A2- " + settings.SUBDOMAIN
        data = serialize_exercise_with_question_data(dbexercise, request.user, hijacked, db=db)
        questionlist_is_empty = data['questionlist_is_empty']
        er += " A3- " + settings.SUBDOMAIN
        try :
            sidecar_count = get_sidecar_count( request.user.username, subdomain, exercise=exercise)
        except :
            sidecar_count = -1
        data['sidecar_count'] = str( sidecar_count )
        return Response(data)
    except ObjectDoesNotExist as e:
        logger.error(
            f"ERROR E771100 {er} {type(e).__name__} EXERCISES.API.EXERCISE  {subdomain} {settings.SUBDOMAIN} user={request.user} exercise={exercise}  "
        )
        return Response({"error": "ERROR E771100"}, status.HTTP_404_NOT_FOUND)
    except Exception as e:
        subdomain = get_subdomain(request)
        logger.error(
            f"ERROR E771100 {er} {type(e).__name__} EXERCISES.API.EXERCISE  {subdomain} {settings.SUBDOMAIN} user={request.user} exercise={exercise}  "
        )
        return Response({"error": "ERROR E771100b"}, status.HTTP_404_NOT_FOUND)


def lti_denied(r, msg="", help_url=None):
    if not help_url:
        try:
            help_url = settings.HELP_URL
        except Exception as e:
            logger.error("HELP_URL_NOT_SET {type(e).__name__} ")
            help_url = ""
    return render(r, "denied.html", {"msg": msg, "help_url": help_url})


def get_exercises_etag(request, course_pk):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    subdomain = get_subdomain(request)
    return None
    cachekey = request.user.username + db + 'selectedExercises'
    if caches['default'].get( cachekey ) :
        return None
    # logger.info("GET EXERCISES ETAG =  " )
    if not settings.CACHE_FOLDERS:
        return None
    # logger.info("CHECKING LATEST ETAG")
    user = request.user
    # print(f"EXERCISES_ETAG SUBDOMAIN = {settings.SUBDOMAIN}")
    if settings.MULTICOURSE:
        course = Course.objects.using(db).get(pk=course_pk)  # ,opentasite=settings.SUBDOMAIN)
    else:
        course = Course.objects.using(db).get(pk=course_pk)
    (cache, cachekey) = get_cache_and_key(
        "safe_user_cache:", userPk=str(user.pk), coursePk=course.course_key, subdomain=subdomain
    )
    etag = (hashlib.md5(cachekey.encode()).hexdigest())[0:7]
    if cache.has_key(cachekey) and settings.DO_CACHE :
        # logger.info("RETURNING ETAG = %s " % etag )
        return etag
    else:
        # logger.info("ETAG %s  NOT FOUND " % etag )
        return None


@api_view(["GET"])
@etag(get_exercises_etag)
def exercise_list(request, course_pk):
    subdomain = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    settings.SUBDOMAIN = get_subdomain(request)
    # FOR SOME REASON EVERYONE IS CREDITED WITH
    # OK ON PROBLEM test1 TODO
    # in particular guscaich TODO
    # ALSO CORRECT + UNTRIED GIVES OK
    # CHECK AGGREGATIONS
    # if not request.COOKIES.get('cookieTest'):
    #    return lti_denied(
    #        request,
    #        "LTI: Cannot set necessary 3rd party cookies",
    #    )
    # logger.info("GET EXERCISES ETAG = %s " % request.headers)
    request.session["course_pk"] = course_pk
    hijacked = request.session.get("hijacked", False)
    user = request.user
    course = Course.objects.using(db).get(pk=course_pk)
    # logger.info("GOT TO THE EXERCISE_LIST CACHE STAGE IN SPITE OF EFFORTS")
    # if not ( settings.SUBDOMAIN == course.opentasite ) :
    #    msg = f"ERROR 6682412 SUBDOMAIN={settings.SUBDOMAIN} opentasite={course.opentasite} DB_NAME={settings.DB_NAME}"
    #    logger.error(msg)
    #    assert False , msg
    (cache, cachekey) = get_cache_and_key(
        "safe_user_cache:", userPk=str(user.pk), coursePk=course.course_key, subdomain=subdomain
    )
    etag = (hashlib.md5(cachekey.encode()).hexdigest())[0:7]
    # logger.info("ETAG CORRESPONDING TO THIS IS %s " % etag )
    if settings.USE_RESULTS_CACHE and cache.has_key(cachekey):
        responselist = cache.get(cachekey)
    else:
        responselist = get_exercise_list(user, course_pk, hijacked, False, None, db=db)

        if not user.is_staff:
            if cachekey:
                cache.set(cachekey, responselist, settings.CACHE_LIFETIME)
        else:
            if cachekey:
                cache.set(cachekey, responselist, settings.CACHE_LIFETIME)
    p = f"/subdomain-data/postgres/{settings.OPENTA_SERVER}-error"
    if os.path.exists(p): # REMOVE ERROR FLAG IF THE SERVERLISTS A DIRECTORY
        os.remove(p)
    return Response(responselist)


@never_cache
@api_view(["GET"])
def user_exercise_list(request, course_pk, user_pk):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    try:
        user = User.objects.using(db).get(id=user_pk)
    except User.DoesNotExist:
        return Response({})
    #
    # THIS GENERATES STATISTICS FOR USE BY ADMIN
    # AND THUS dOES NOT HIDE CORRECTNESS OF NO_FEEDBACK QUESTIONS
    # IT HAS ITS OWN CACHE
    #
    if settings.MULTICOURSE:
        course = Course.objects.using(db).get(pk=course_pk, opentasite=settings.SUBDOMAIN)
    else:
        course = Course.objects.using(db).get(pk=course_pk)

    (cache, cachekey) = get_cache_and_key(
        "unsafe_user_cache:", userPk=user_pk, coursePk=course.course_key, subdomain=subdomain
    )
    if settings.USE_RESULTS_CACHE and cache.has_key(cachekey):
        responselist = cache.get(cachekey)
        return Response(responselist)
    responselist = get_exercise_list(user, course_pk, False, True, None, db=db)
    all_exercise_keys = (
        Exercise.objects.using(db)
        .filter(course__pk=course_pk, meta__published=True)
        .values_list("exercise_key", flat=True)
    )
    used_exercise_keys = responselist.keys()
    # for exercise_key in all_exercise_keys:
    #    if not exercise_key in used_exercise_keys:
    #        responselist[exercise_key] = None
    if cachekey:
        cache.set(cachekey, responselist, settings.CACHE_LIFETIME)

    return Response(responselist)


def get_unsafe_exercise_summary(user, course_pk, dbexercises, db,selected=[]):
    assert db != None, "GET_UNSAFE_EXERCISE_SUMMARY DB=None"
    #logger.error(f"GET_UNSAFE_EXERCISE_SUMMARY selected = {selected}")
    # logger.debug("GET_UNSAFE_EXERCISE_SUMMARY for %s %s " % ( settings.DB_NAME, settings.SUBDOMAIN)  )
    cachekey = None
    if dbexercises == None:
        logger.debug("DBEXERCISE = None")
    else:
        logger.debug("DBEXERCISE IS NOT NONE")
    if dbexercises is None and not selected:
        course = Course.objects.using(db).get(pk=course_pk)
        subdomain = course.opentasite
        (cache, cachekey) = get_cache_and_key(
            "get_unsafe_exercise_summary:", userPk=user, coursePk=course.course_key, subdomain=subdomain
        )
        if settings.USE_RESULTS_CACHE and cache.has_key(cachekey) and not  selected  :
            sums = cache.get(cachekey)
            return sums
    else:
        course = Course.objects.using(db).get(pk=course_pk)
    ags = Aggregation.objects.using(db).filter(user=user, course=course_pk, exercise__meta__published=True)
    if not dbexercises is None:
        #logger.error(f"GET_UNSAFE")
        #logger.error(f"COUNT = {dbexercises.count}")
        ags = ags.filter(exercise__in=dbexercises)
        # logger.debug("DBEXERCISES COUNT = " + str(dbexercises.count()))
    else:
        pass
        # logger.debug("DBEXERCISES IS NONE")
    if selected :
        ags = ags.filter(exercise__exercise_key__in=selected)
    sums = {}
    etypes = ["required", "bonus", "optional","aibased"]
    for etype in etypes:
        sums[etype] = {}
        sums[etype][etype] = {}
        sums[etype] = {}
        for stype in stypes:
            sums[etype][stype] = 0

    ags_required = ags.filter(exercise__meta__required=True)
    ags_bonus = ags.filter(exercise__meta__bonus=True)
    ags_optional = ags.filter(exercise__meta__bonus=False, exercise__meta__required=False)
    n_optional = ags_optional.filter(Q(user_is_correct=True) | Q(force_passed=True)).count()

    student = user
    failed_by_audits = ags.filter(audit_needs_attention=True, audit_published=True).count()
    passed_audits = ags.filter(audit_needs_attention=False, audit_published=True).count()
    all_audits = ags.filter(audit_published=True).count()
    passed_manually = ags.filter(force_passed=True).count()
    agt = {}
    agt["required"] = ags_required
    agt["optional"] = ags_optional
    agt["bonus"] = ags_bonus
    for etype in ["required", "optional", "bonus"]:
        for stype, agkey in zip(stypes, agkeys):
            sums[etype][stype] = agt[etype].filter(**{agkey: True}).count()
        sums[etype]["n_correct"] = (
            agt[etype].filter(Q(force_passed=True) | Q(user_is_correct=True), audit_needs_attention=False).count()
        )
        sums[etype]["n_deadline"] = (
            agt[etype].filter(Q(force_passed=True) | Q(correct_by_deadline=True), audit_needs_attention=False).count()
        )
        sums[etype]["n_image_deadline"] = (
            agt[etype].filter(Q(force_passed=True) | Q(complete_by_deadline=True), audit_needs_attention=False).count()
        )
        sums[etype]["n_complete"] = sums[etype]["number_complete_by_deadline"]
        sums[etype]["n_complete_no_deadline"] = sums[etype]["number_complete"]
    sums["n_optional"] = n_optional
    sums["failed_by_audits"] = failed_by_audits
    sums["passed_audits"] = passed_audits
    sums["total_audits"] = all_audits
    sums["manually_passed"] = passed_manually
    sums["total"] = ags.filter(user_is_correct=True).count()
    sums["total_complete_before_deadline"] = ags.filter(
        complete_by_deadline=True
    ).count()  # n_complete_bonus + n_complete_required + n_optional,
    sums["total_complete_no_deadline"] = ags.filter(all_complete=True).count()
    if not cachekey is None and not selected :
        cache.set(cachekey, sums, 120 )
    return sums


def get_exercise_list(user, course_pk, hijacked, force_feedback, dbexercises, db):
    """
    List all exercises
    """
    #
    # THIS IS SENDS THE STUDENT RESULT JSON TO CLIENT
    #
    try:
        course = Course.objects.using(db).get(pk=course_pk)
        subdomain = course.opentasite
    except ObjectDoesNotExist as e:
        logger.error(
            f"ERROR COURSE 1729062 GET_EXERCISES_LIST COURSE DOES NOT EXIST course_pk={course_pk} user={user} "
        )
        return {}
    responselist = {}
    beg = time.time()
    ags = Aggregation.objects.using(db).filter(user=user, course=course_pk)
    ags = ags.filter(exercise__meta__published=True)
    if not dbexercises is None:
        ags = ags.filter(exercise__in=dbexercises)
    sums = {}
    etypes = ["required", "bonus", "optional", "nofeedback"]
    for etype in etypes:
        sums[etype] = {}
        sums[etype][etype] = {}
        for gtype in ["feedback", "nofeedback"]:
            sums[etype][gtype] = {}
            for stype in stypes:
                sums[etype][gtype][stype] = 0
    data = {}
    for ag in ags:
        data = {}
        try :
            exercise = ag.exercise
            if exercise.meta.required:
                etype = "required"
            elif exercise.meta.bonus:
                etype = "bonus"
            else:
                etype = "optional"
            if exercise.meta.published or user.has_perm("exercises.edit_exercise"):
                data = serialize_exercise_with_question_data(exercise, user, hijacked, db=db)
                if data == {}:
                    logger.error(
                        f"ERROR EXERCIS NOT FOUND exercise={exercise} user={user} {settings.SUBDOMAIN} hijacked={hijacked}"
                    )
            # if  not exercise.meta.feedback and not force_feedback and (
            #    not exercise.meta.feedback and (not settings.IGNORE_NO_FEEDBACK) and hijacked
            # ):
            give_feedback_anyway = settings.IGNORE_NO_FEEDBACK or force_feedback or settings.RUNTESTS
            if not exercise.meta.feedback and not give_feedback_anyway:
                sums[etype]["nofeedback"]["number_complete"] += 1
                sums[etype]["nofeedback"]["number_complete_by_deadline"] += 1
                del data["correct"]
                del data["correct_by_deadline"]
                del data["all_complete"]
                del data["complete_by_deadline"]
            else:
                #
                # THESE ARE JUST CUMULANTS OF THE BOOLEANDS IN AGGREGATION
                #
                for stype, agkey in zip(stypes, agkeys):
                    sums[etype]["feedback"][stype] = (
                        (sums[etype]["feedback"][stype] + 1)
                        if data.get(agkey, False)
                        else sums[etype]["feedback"][stype]
                    )
            data["ignore_no_feedback"] = settings.IGNORE_NO_FEEDBACK or force_feedback
            responselist[exercise.exercise_key] = data
        except ObjectDoesNotExist as e:
            pass
        except Exception as e:
            logger.error(f"AGGREGATION ERROR E91762931 MISSING FOR user={user} ")
    responselist["runtests"] = settings.RUNTESTS
    responselist["username"] = user.username

    # THE FOLLOWING WAS REFACTORED FROM results.py
    # AND ADDS DEPENDENT AGGREGATION FIELDS

    # course = Course.objects.get(pk=course_pk)
    exercises = Exercise.objects.using(db).filter(meta__published=True, course=course)
    required_exercises = exercises.filter(meta__required=True)
    bonus_exercises = exercises.filter(meta__bonus=True)
    optional_exercises = exercises.filter(meta__bonus=False, meta__required=False)
    ags_required = ags.filter(exercise__in=required_exercises)
    ags_bonus = ags.filter(exercise__in=bonus_exercises)
    ags_optional = ags.filter(exercise__in=optional_exercises)
    n_optional = ags_optional.filter(Q(user_is_correct=True) | Q(force_passed=True)).count()

    student = user
    failed_by_audits = ags.filter(audit_needs_attention=True, audit_published=True).count()
    passed_audits = ags.filter(audit_needs_attention=False, audit_published=True).count()
    all_audits = ags.filter(audit_published=True).count()
    passed_manually = ags.filter(force_passed=True).count()
    agt = {}
    agt["required"] = ags_required
    agt["optional"] = ags_optional
    agt["bonus"] = ags_bonus
    for etype in ["required", "optional", "bonus"]:
        sums[etype]["feedback"]["n_correct"] = (
            agt[etype].filter(Q(force_passed=True) | Q(user_is_correct=True), audit_needs_attention=False).count()
        )
        sums[etype]["feedback"]["n_deadline"] = (
            agt[etype].filter(Q(force_passed=True) | Q(correct_by_deadline=True), audit_needs_attention=False).count()
        )
        sums[etype]["feedback"]["n_image_deadline"] = (
            agt[etype].filter(Q(force_passed=True) | Q(complete_by_deadline=True), audit_needs_attention=False).count()
        )
        sums[etype]["feedback"]["n_complete"] = sums[etype]["feedback"]["number_complete_by_deadline"]
        sums[etype]["feedback"]["n_complete_no_deadline"] = sums[etype]["feedback"]["number_complete"]
    sums["n_optional"] = n_optional
    sums["failed_by_audits"] = failed_by_audits
    sums["passed_audits"] = passed_audits
    sums["total_audits"] = all_audits
    sums["manually_passed"] = passed_manually
    sums["total"] = ags.filter(user_is_correct=True).count()
    sums["total_complete_before_deadline"] = ags.filter(
        complete_by_deadline=True
    ).count()  # n_complete_bonus + n_complete_required + n_optional,
    sums["total_complete_no_deadline"] = ags.filter(all_complete=True).count()
    responselist["sums"] = sums
    return responselist


def get_folder_etag(request, course_pk, fstring):
    subdomain, db = get_subdomain_and_db(request)
    settings.SUBDOMAIN = subdomain
    selectedExercisesKeys = get_selectedExercisesKeys( request.user, db )
    filterstring = fstring + f"{selectedExercisesKeys}"
    # logger.info("GET_FOLDER_ETAG")
    if not settings.CACHE_FOLDERS:
        return None
    user = request.user
    # print(f"ETAG: get_cache_and_key( 'user_exercise_tree:', userPk={str(user.pk)}, coursePk={course_pk}, subdomain={subdomain},exercise_filter={fstring})")
    (cache, cachekey) = get_cache_and_key(
        "user_exercise_tree:", userPk=str(user.pk), coursePk=course_pk, subdomain=subdomain, exercise_filter=filterstring
    )
    # logger.info("FOLDER CACHEKEY = %s " % cachekey )
    # logger.error(f"CACHEKEY = {cachekey}")
    if cache.get(cachekey):
        etag = cachekey
        return etag
    else:
        return None


@api_view(["GET"])
@never_cache
def exercise_tree(request, course_pk, fstring="11100"):
    # logger.error(f"COURSE_PK= {course_pk}")
    subdomain, db = get_subdomain_and_db(request)
    user = request.user
    #try :
    #    subdomain, db ,user = get_subdomain_and_db_and_user(request)
    #except Exception as e :
    #    logger.error(f"XXX  EXERCISE_TREE RETURNED ERROR  {str(e)}")
    messages = [];
    """
    Get exercise tree
    """
    exercisefilter = {
        "required_exercises": fstring[0] == "1",
        "bonus_exercises": fstring[1] == "1",
        "optional_exercises": fstring[2] == "1",
        "unpublished_exercises": fstring[3] == "1",
        "organize": fstring[4] == "1",
    }
    try:
        dbcourse = Course.objects.using(db).get(pk=course_pk)
    except Course.DoesNotExist:
        logger.error("Requested course does not exist pk: %d", course_pk)
        return Response({"error": f"Invalid course  attempted with {user}  in {db} "}, status=status.HTTP_404_NOT_FOUND)
    selectedExercisesKeys = get_selectedExercisesKeys( request.user, db )
    filterstring = fstring + f"{selectedExercisesKeys}"
    (cache, cachekey) = get_cache_and_key(
        "user_exercise_tree:", userPk=str(user.pk), coursePk=course_pk, subdomain=subdomain, exercise_filter=filterstring
    )
    if settings.CACHE_FOLDERS and settings.DO_CACHE:
        res = cache.get(cachekey)
        if not res == None:
            ret = Response(res)
            return ret
    try:
        folder_structure = exercise_folder_structure(Exercise.objects.using(db), user, dbcourse, exercisefilter,db)
    except Exception as e:
        logger.error(f"ERROR403 E30123 {type(e).__name__} folder_structure fails ")
        return Response({"error": "ERROR E30123 folders not found "}, status.HTTP_403_FORBIDDEN)

    res = get_json(folder_structure)
    try:
        cache.set(cachekey, res, 360)
    except Exception as e:
        logger.error(f"ERROR {type(e).__name__} CACHE ERROR 428234 CANNOT SET CACHE {cachekey}")
    ret = Response(res)
    return ret


@never_cache
@api_view(["GET"])
def other_exercises_from_folder(request, exercise, subdomain):
    # subdomain_in = subdomain
    # print(f"SUBDOMAIN COMING IN AS {subdomain}")
    # settings.SUBDOMAIN = get_subdomain(request)
    # subdomain,db = get_subdomain_and_db(request)
    # if not subdomain  == subdomain_in :
    #    logger.error( f"INCONISTEN OTHER_EXERCISES_FROM_FOLDER SUBDOMAIN subdomain={subdomain} subdomain_in={subdomain_in}" )
    if not settings.RUNTESTS:
        db = subdomain
    else:
        subdomain, db = get_subdomain_and_db(request)
    try:
        A = "a"
        exercise_key = str(exercise)
        dbexercise = Exercise.objects.using(db).select_related("meta").get(exercise_key=exercise_key)
        A = A + "b"
        course_exercises = Exercise.objects.using(db).select_related("course", "meta").filter(course=dbexercise.course)
        A = A + "c"
        other = []
        if request.user.has_perm("exercises.edit_exercise") or request.user.has_perm("exercises.view_unpublished"):
            A = A + "d"
            other = course_exercises.using(db).filter(folder=dbexercise.folder).prefetch_related("meta")
        else:
            A = A + "e"
            other = (
                course_exercises.using(db)
                .filter(folder=dbexercise.folder, meta__published=True)
                .prefetch_related("meta")
            )

        A = A + "f"
        serializer = ExerciseSerializer(other, many=True)
        A = A + "g"
        actions_for_key = [("published", lambda x: str(not x)), ("sort_key", str)]
        A = A + "h"

        def sort_key_func(item):
            return "".join([func(item["meta"][key]) for (key, func) in actions_for_key])

        A = A + "i"
        inorder = sorted(serializer.data, key=sort_key_func)
        A = A + "j"
        return Response(inorder)
    except Exception as e:
        msg = f"ERROR403 OTHER_EXERCISES {A} {type(e).__name__} {db} {request.user} {exercise} "
        logger.error(msg)
        return Response({"error": msg}, status.HTTP_403_FORBIDDEN)


@never_cache
@api_view(["GET"])
def exercise_json(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    cache = caches["default"]
    pathkey = f"{str(db)}-{exercise}"
    # print(f"CACHEKEY = {pathkey}")
    try :
        fpath = cache.get(pathkey)
    except Exception as err :
        logger.info(f"ERROR IN PATH {str(err)}")
        fpath = None
    
    # print(f"DB = {db}")
    x = datetime.datetime.now()
    ip = request.META["REMOTE_ADDR"]
    user = request.user

    # if not ( subdomain == settings.SUBDOMAIN and settings.DB_NAME == subdomain ) :
    #    print(f"request.META={request.META}")
    #    print(f"PATCH DB DB={settings.DB_NAME} subdomain={subdomain} settings.SUBDOMAIN={settings.SUBDOMAIN}")
    #    settings.SUBDOMAIN = subdomain
    #    settings.DB_NAME = subdomain
    try:
        dbexercise = Exercise.objects.using(db).select_related("meta", "course").get(exercise_key=exercise)
        course = dbexercise.course
        feedback = dbexercise.meta.feedback
        # print(f"FEEDBACK EXERCISE_JSON = {feedback}")

    except ObjectDoesNotExist as e:
        x = datetime.datetime.now()
        ip = request.META["REMOTE_ADDR"]
        logger.error(
            "ERROR403 %s %s ERROR 203 EXERCISE_JSON  subdomain=%s key=%s user=%s  type=%s "
            % (x, ip, settings.SUBDOMAIN, exercise, request.user, type(e).__name__)
        )
        logger.error(f"request.META={request.META}")
        return Response({f"Exercise key {exercise} does not exist"}, status.HTTP_403_FORBIDDEN)
    except Exception as e:
        x = datetime.datetime.now()
        ip = request.META["REMOTE_ADDR"]
        path = request.get_full_path()
        t = type(e).__name__
        logger.error(
            "ERROR403 %s %s UNKNOWN ERROR 204 EXERCISE_JSON  subdomain=%s key=%s user=%s  type=%s "
            % (x, ip, settings.SUBDOMAIN, exercise, request.user, type(e).__name__)
        )
        return Response({f"Unknown error for path {path}  results in type {t} error"}, status.HTTP_403_FORBIDDEN)

    (cache, cachekey) = get_cache_and_key(
        "user_exercise_json:", exercise_key=exercise, coursePk=course.pk, userPk=request.user.pk, subdomain=subdomain
    )
    if settings.USE_JSON_CACHE and cache.get(cachekey):
        logger.error("WARNING USING JSON_CACHE in {subdomain}")
        json = cache.get(cachekey)
        return Response(json)

    try :
        errormsg = ""
        hide_answers = not user.has_perm("exercises.view_solution")
        full_path = dbexercise.get_full_path()
        exercise_key = exercise
        course_key = course.course_key
        exercise_path = dbexercise.path
        alternative_full_path = os.path.join(settings.VOLUME, subdomain, "exercises", str(course_key), exercise_path)
        # print(f"GET_FULL_PATH DB={db}")
        # THE EXERCISE IS NOT GETTING FOUND HERE see klog6.txt ilog6.txt
        if not settings.RUNTESTS and not alternative_full_path == full_path:
            logger.error(f"ERROR EXERCISE_JSON INCONSISTENT")
            logger.error(f"ERROR FPATH = {fpath} ")
            logger.error(f"ERROR CONTINUED EXERCISE_JSON FULL_PATH0={full_path}")
            logger.error(f"ERROR CONTINUED EXERCISE_JSON FULL_PATH1={alternative_full_path}")
            logger.error(f"ERROR CONTINUED EXERCISE_JSON FULL_PATH DB={db}")
            if os.path.isdir(alternative_full_path):
                full_path = alternative_full_path
                subdomain, db = get_subdomain_and_db(request)
                logger.error(f"ALTERNATIVE FULL_PATH USED DB={db} ")
            elif not fpath == None and os.path.isdir(fpath):
                logger.error(f"FPATH USED DB={db} ")
                full_path = fpath
            else:
                full_path = None
                logger.error(
                    f"ALL PATHS FAIL full_path={full_path} alternative_full_path={alternative_full_path} fpath={fpath}  AGAIN"
                )
                return Response({"error": "JSON COULD NOT BE FOUND; log out and log back in again"})
        # else :
        #    print(f"EXERCISE_JSON FULL_PATH={full_path}")
        xml = parsing.exercise_xml(full_path)
        # lang = request.COOKIES.get('lang')
        course = dbexercise.course
        course_pk = course.pk
        langs = dbexercise.course.get_languages()
        if settings.DO_CACHE_EXERCISE_XML:
            (cache, cachekey) = t_cache_and_key(course, dbexercise)
            if cache.has_key(cachekey):
                xml = cache.get(cachekey)
            else:
                xml = translate_xml_language(xml, langs, course_pk, dbexercise, False)
                cache.set(cachekey, xml, 120)
        er = "B"
        if True or "@" in str(xml):
            er = er + "0"
            usermacros = get_usermacros(user, exercise, question_key=None, before_date=None, db=db )
            er = er + "1"
            usermacros["@call"] = "exercise_json"
            usermacros["@combined_user_macros"] = get_combined_usermacros(exercise, xml, user, before_date=None, db=db)
        else:
            usermacros = {}  # if usermacros = {} then no macroparsing is done
            usermacros['validation'] = False
        er = er + "C"
        try:
            root = etree.fromstring(xml)
            is_hijacked = len(  request.session.get('hijack_history',[] )  ) > 0 
            if not request.user.is_staff and not  settings.RUNNING_MANAGEMENT_COMMAND  and not is_hijacked :
                alltags = root.findall(".//*")
                for t in alltags :
                    if 'hidden' in t.attrib :
                        parent = t.getparent()
                        parent.remove(t)
            root = apply_macros_to_node(root, usermacros)
            xml = etree.tostring(root)
        except MacroError as e:
            extype = type(e).__name__
            errormsg = extype + str(e)
        except Exception as e:
            extype = type(e).__name__
            errormsg = extype
            logger.error(f"XML ERROR ROOT CANNOT BE FOUND {extype} XML={xml} ")
        er = er + "C"
        full_exercisejson = parsing.exercise_xml_to_json(xml)
        full_exercisejson["exercise"]["exercise_key"] = exercise
        full_exercisejson["exercise"]["db"] = db
        full_exercisejson["exercise"]["subdomain"] =  subdomain
        full_exercisejson['exercise']['sidecar_count'] = '49723'
        hide_tags = question_module.get_sensitive_tags()
        # logger.info("HIDE_TAGS = %s " % hide_tags)
        # logger.info("META = %s " % dbexercise.meta.feedback )
        # if not dbexercise.meta.feedback :
        #    hide_tags = {key: val + ['correct']   for (key,val) in hide_tags.items()  }
        # logger.info("HIDE_TAGS NOW = %s " % hide_tags)
        hide_attrs = question_module.get_sensitive_attrs()
        safe_exercisejson = parsing.exercise_xml_to_json(
            xml, hide_answers=hide_answers, sensitive_tags=hide_tags, sensitive_attrs=hide_attrs
        )
        er = er + "D"
        # def question_json_get(path, question_key, usermacros={}):

        # if 'question' in safe_exercisejson['exercise']:
        #    safe_and_full = zip(safe_exercisejson['exercise']['question'],
        #                        full_exercisejson['exercise']['question'])
        #    safe_exercisejson['exercise']['question'] = []
        #    for safe_question, full_question in safe_and_full:
        #        question_key = deep_get(full_question, '@attr', 'key')
        #        dbquestion = Question.objects.filter(
        #            exercise=dbexercise, question_key=question_key).first()
        #        full_question['exercise_key'] = exercise
        #        modified_question = question_module.question_json_hook(
        #            safe_question, full_question, dbquestion.pk, request.user.pk)
        #        safe_exercisejson['exercise']['question'].append(modified_question)
        # def question_json_get_from_raw_json(raw_json, exercise_key, question_key, usermacros={}):
        er = er + "E"
        exercise_key = exercise
        if "question" in safe_exercisejson["exercise"]:
            safe_and_full = zip(safe_exercisejson["exercise"]["question"], full_exercisejson["exercise"]["question"])
            safe_exercisejson["exercise"]["question"] = []
            for safe_question, full_question in safe_and_full:
                question_key = deep_get(full_question, "@attr", "key")
                usermacros['@question_key'] = question_key ;
                dbquestion = Question.objects.using(db).filter(exercise=dbexercise, question_key=question_key).first()
                full_question = question_json_get_from_raw_json(full_exercisejson, exercise_key, question_key, usermacros,db)
                full_question["exercise_key"] = exercise
                full_question["question_key"] = question_key
                full_question["subdomain"] = subdomain
                full_question["db"] = db
                qtype = function_qtype(db,exercise_key, question_key)
                #qtype = dbquestion.qtype();
                full_question["qtype"] = qtype
                #print(f"FULL_QUETION_JSON QTYPE = {subdomain} {exercise_key} {exercise} {qtype}")
                try:
                    # print(f"MODIFIED_QUESTION TRIED")
                    hookfunc = question_module.question_json_hook
                    logger.info(f"HOOKFUNC = {hookfunc}")
                    modified_question = hookfunc(
                        safe_question, full_question, dbquestion.pk, user.pk, exercise, feedback,db=db
                    )
                except Exception as e:
                    modified_question = full_question
                    errormsg = (
                        errormsg
                        + f" There are serious format errors in question {question_key} which must be fixed! Go back to a previous version in the History if necessary."
                    )
                    logger.error(
                        f"ERROR 989 JSON_HOOK {subdomain} {exercise} {dbexercise.name}  {type(e).__name__} { str(e) } "
                    )
                safe_exercisejson["exercise"]["question"].append(modified_question)
        # #logger.info("SAFE EXERCISE_JSON = %s " % safe_exercisejson)
        er = "F"
        if errormsg:
            safe_exercisejson["error"] = errormsg
        else:
            json = safe_exercisejson
            cache.set(cachekey, json, 120)
        return Response(safe_exercisejson)
    except parsing.ExerciseParseError as e:
        logger.error(f"ERROR 206a parsing EXERCISE_JSON subdomain={settings.SUBDOMAIN} type={type(e).__name__} full_path={full_path} ")
        return Response({"error" : f"Exercise {full_path} parsing error: Look over xml"})
    except AttributeError :
        return Response({"error" : f"Exercise {dbexercise.name} in {settings.SUBDOMAIN}  not found "})
    except Exception as e :
        logger.error(f"ERROR 206b {e} UNCAUGHT_EXERCISE_JSON  subdomain={settings.SUBDOMAIN} type={type(e).__name__} full_path={full_path} ")
        return Response({"error" : f"Exercise {dbexercise.name} in {settings.SUBDOMAIN}  not found "})


@permission_required("exercises.view_xml")
@never_cache
@api_view(["GET"])
def exercise_xml(request, exercise):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    try:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    except ObjectDoesNotExist as e:
        return Response({})
    xml = parsing.exercise_xml(dbexercise.get_full_path())
    return Response({"xml": xml})
    #oldxml = xml;
    #root = etree.fromstring(xml);
    ##print(f" ROOT IS COMPUTED {root}")
    #try :
    #    root = parsing.denest(root)
    #    #print(f"SUCCESSFULE DENEST")
    #except Exception as err:
    #    xml = oldxml
    #    logger.error(f" {type(err).__name__} { str(err)}  ERROR DENESTING XML {oldxml}")
    #    return Response({"xml": oldxml })
    #xml = etree.tostring(root, encoding='UTF-8' ).decode();
    #print(f"EXERCISE_XML")
    #return Response({"xml": xml})


def validate_exercise_globals(xml, user, exercise, extradefs):
    #
    # CHECK EXERCISE GLOBALS AND QUESTIONS IF GLOBALS CHANGE
    # DONT BOTHER CHECKING QUESTIONS IF QUESTIONS CHANGE
    # SINCE AUTHOR TYPICALLY CHECKS THIS ANYWAY
    #
    #print(f"VALIDATE_EXERCISE_GLOBALS")
    db = settings.DB_NAME
    messages = []
    cache_seconds = 5 * 60
    parser = etree.XMLParser(recover=True, remove_comments=True)
    root = etree.fromstring(xml)
    if len( root.xpath("//global")  ) == 0 :
        return  []
    if True or "@" in str(xml):
        usermacros = get_usermacros(user, exercise, db=db, )
        usermacros["@exerciseseed"] = settings.DEFAULT_EXERCISESEED
        usermacros["@questionseed"] = settings.DEFAULT_QUESTIONSEED
        usermacros["@call"] = "exercise_json"
        usermacros["@combined_user_macros"] = get_combined_usermacros(exercise, xml, user, before_date=None, db=db)
    else:
        usermacros = {}  # if usermacros = {} then no macroparsing is done
    root = apply_macros_to_exercise(root, usermacros)
    global_xpath = '/exercise/global[@type="{type}"] | /exercise/global[not(@type)] | /exercise/global'
    try :
        global_xmltree = (root.xpath(global_xpath) ) [0]
        has_globals =  len( global_xmltree) > 0  or len( global_xmltree.text ) > 0 
    except ( IndexError, TypeError ) as e :
        global_xmltree = None;
        has_globals = False
    # full_exercisejson = parsing.exercise_xml_to_json(xml)
    # #logger.info("FULL_EXERCISE_JSON = ", full_exercisejson)
    if has_globals :
        globalhash = get_hash_from_string(str(etree.tostring(global_xmltree, encoding=str)))
    else :
        globalhash = None
    messages = []
    # if settings.DO_CACHE :
    #    messages = cache.get(globalhash)
    #    if messages is not None:
    #        return messages
    if has_globals :
        xml_variables = parse_xml_variables(global_xmltree)
        funcsubs = parse_xml_functions(global_xmltree)
    else :
        xml_variables = [];
        funcsubs = [];
    obj = exercise_xml_to_json(xml)
    #print(f"XML = {xml}")
    if not "question" in obj["exercise"]:
        return []
    questions = obj["exercise"]["question"]
    types_to_check = []
    for question in questions:
        qtype = question["@attr"]["type"]
        #print(f" FOUND TYPE {qtype}")
        types_to_check = types_to_check + [question["@attr"]["type"]]
    all_types_to_check = set(["devLinearAlgebra", "symbolic", "compareNumeric", "linearAlgebra", "numeric","basic","matrix","qm"])
    types_to_check = list(set(types_to_check).intersection(all_types_to_check))
    uses_numeric_evaluation = set( ["devLinearAlgebra", "compareNumeric", "linearAlgebra", "numeric","basic","matrix"] )
    needs_globals =  len( list( set( types_to_check).intersection( uses_numeric_evaluation) ) ) > 0 
    if len(types_to_check) == 0:
        return []
    if  ( not has_globals ) and  ( not needs_globals  ) :
        return []
    expressions = [x["name"] + " == " + x["value"] for x in xml_variables]
    # logger.info("EXPRESSIONS = ", expressions)
    units = ["kg", "meter", "second", "kelvin", "mole", "candela"]
    unitvariables = [{"name": item, "value": 1} for item in units]
    variablelist = [item["name"] for item in xml_variables]
    duplicates = list(set([x for x in variablelist if variablelist.count(x) > 1]))
    if len(duplicates) > 0:
        messages.append(("error", "Duplicate definitions of %s " % str(" and ".join(duplicates))))
        return messages
    for question_type in types_to_check:
        symex = compare_function[question_type]
        #print(f"API-SYMEX TYPE={question_type}  SYMEX= {symex}")
        variables = unitvariables + xml_variables
        funcsubs = parse_xml_functions(global_xmltree)
        precision = 1.0e-6
        result = {}
        # logger.info("NOW DO", question_type)
        names = []
        # logger.error(f"EXPRESSIONS = {expressions}")
        for expression in expressions:
            name = (expression.split("==")[0]).strip()
            if name in names:
                messages.append("Variable %s  has duplicate definition" % name)
                return messages
            else:
                names = names + [name]
            # logger.info("NAME = ", name )
            expr = "\n Error in global definitions: "
            # logger.error("variables = ", variables)
            # logger.error("CHECK OUT expression ", expression)
            result = symex(
                precision,
                variables,
                expression,
                "0 == 0",
                True,
                [],
                [],
                funcsubs,
                extradefs,
                validate_definitions=True,
                source="SYM1",
            )
            if (not result.get("correct")) or result.get("error"):
                msg = "Error 667: Expression: " + str(expression) + expr + result.get("error", "")
                msg = reg.sub(r"[\'<>]", "", msg)
                if "dummy" in msg:  # Catch dummy variable error in sympify with custom
                    msg = f"Error 667: {result.get('error')}"
                messages.append(("error", msg))
                # logger.info("MESSAGES = ", messages )
                return messages

        question_xmltrees = root.findall('./question[@type="{type}"]'.format(type=question_type))

    if "@" in str(xml):
        usermacros = get_usermacros(user, exercise, db=db)
        usermacros["@call"] = "exercise_json"
        usermacros["@combined_user_macros"] = get_combined_usermacros(exercise, xml, user, before_date=None, db=db)
    else:
        usermacros = {}  # if usermacros = {} then no macroparsing is done
    root = etree.fromstring(xml)
    root = apply_macros_to_node(root, usermacros)
    xml = etree.tostring(root)
    # logger.info("XML = ", xml)
    #if root.xpath("/exercise/macros"):
    #    messages.append(("warning", "No question validation is done when using macros. "))
    #    return messages
    for question_xmltree in question_xmltrees:
        result = {}
        ret = getallglobalvariables(global_xmltree, question_xmltree, assign_all_numerical=False)
        # logger.info("RET = ", ret )
        used_variables = list(ret["used_variables"])
        variables = ret["variables"]
        funcsubs = ret["functions"]
        authorvariables = ret["authorvariables"]
        blacklist = ret["blacklist"]
        correct_answer = ret["correct_answer"]
        precision = 1.0e-6
        # logger.info("QUESTION TYHPE LOC1 = %s " % question_xmltree.attrib['type'] )
        question_type = question_xmltree.attrib["type"]
        symex = compare_function[question_type]
        # #logger.info("USERMACROS = ", usermacros)
        # #logger.info("TRY CORRECT UNMACROD CORRECT ANSWER ", correct_answer)
        # #logger.info(
        #    "TRY CORRECT ANSWER ",
        #    apply_macros_to_string('<txt>' + str(correct_answer) + '</txt>', [usermacros]),
        # )
        # correct_answer  = apply_macros_to_string( str( correct_answer ), usermacros )
        # #logger.info("TRY CORRECT ANSWER ", correct_answer )
        try:
            expr = declash(correct_answer + "  ")
            # logger.info("API correct_answer ", expr)
            # logger.info("API VARIABLES = ", variables)
            # logger.info("API USED_VARIABLES ", used_variables)
            # expr = "sin( variablebeta) "
            # used_variables = ['variablebeta']
            # variables = [{'name': 'variablebeta', 'value': '2 pi / 28.7', 'tex': 'variablevariablebeta'}, {'name': 'x', 'value': 'sin(variablebeta)', 'tex': 'x'}]
            # print(f"AUTHORVARIABLES = {authorvariables}")
            # print(f"USED_VARIABLES = {used_variables}")
            result = symex(
                precision,
                authorvariables,
                expr,
                expr,
                True,
                [],
                used_variables,
                funcsubs,
                extradefs,
                validate_definitions=True,
                source="SYM2",
            )
            if result.get("error"):
                msg = "Error in question with answer " + expr + ":   " + result.get("debug", "")
                msg = reg.sub(r"[\'<>]", "", msg)
                messages.append(("error", msg))
                # logger.info("VARIABLES = ", variables )
                # logger.info("USED_VARIABLES = ", used_variables)
                # logger.info("MESSAGE2 = ",  correct_answer)
                # logger.info("MESSAGE3 = ", messages )
                return messages
            else:
                pass

        except Exception as e:
            msg = f"Error in question with answer {expr} : {result.get('debug', '')}"
            msg = reg.sub(r"[\'<>]", "", msg)
            messages.append(("error", msg))
            return messages
    if not messages:
        cache.set(globalhash, messages, cache_seconds)
    messages.append(("success", "globals ok"))
    return messages

def validate_exercise_xml(xml, user, exercise_key,db):
    try :
        varhash =  get_hash_from_string( 'validate-exericse-xml' + str( exercise_key )  + str( xml )  )
        cache = caches["default"]
        res = cache.get(varhash )
        if  res  and settings.DO_CACHE  : # CACHING EXERCISE_VALIDATION 
            (success,msg) = res[0];
            if success == 'success' :
                return res
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        db = dbexercise.course.opentasite;
        exerciseassetpath = dbexercise.exercise_asset_devpath("")
        extradefs = get_extradefs(exerciseassetpath)
        if os.path.exists(os.path.join(exerciseassetpath, "customfunctions.py")):
           extradefs["customfunctions"] = "customfunctions.py"
        try :
            res = validate_exercise_xml_( xml, user , exercise_key, db, exerciseassetpath, extradefs )
            cache.set(varhash, res , 3600 )
        except Exception as e :
            res = [('error' , str(e) )]
    except Exception as err :
        if cache.get( varhash ) :
            cache.delete(varhash)
        raise(err) 
    if re.search(r"&lt;\S" ,xml ) :
        res = [('warning', "There must be a space after &amp;lt; in order to interpet the less than sign correctly.")]
    return res

def validate_exercise_xml_(xml, user, exercise_key, db, exerciseassetpath, extradefs):
    messages = []
    try:
        before_date = None
        #   extradefs["customfunctions"] = "customfunctions.py"

        def apply_macros_to_exercise_xml( xml, user, exercise, db, exerciseassetpath, extradefs ):
            from exercises.applymacros import apply_macros_to_exercise
            from exercises.question import get_usermacros
            usermacros = get_usermacros(user, exercise_key, question_key=None, before_date=before_date, db=db)
            usermacros['@questionseed'] = settings.DEFAULT_QUESTIONSEED
            parser = etree.XMLParser(recover=True)
            root = etree.fromstring(xml, parser=parser)
            root = apply_macros_to_exercise(root, usermacros)
            newxml = etree.tostring( root, ).decode('utf-8')
            return newxml 

        xml = apply_macros_to_exercise_xml(  xml, user, exercise_key , db, exerciseassetpath, extradefs )
        xmlschema = etree.XMLSchema(etree.parse(os.path.join( settings.BASE_DIR , 'exercises', 'exercise.xsd') ) )
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(xml, parser=parser)
        tag = "ignore"
        tags = root.xpath(f"//{tag}")
        for tag1 in  tags :
            if any(tag1.iter(tag)):
                for nested in list(tag1.iter(tag))[1:]:
                    parent = nested.getparent()
                    parent.remove(nested)
        #for hidden in hiddens :
        #    root.remove(hidden)
        #path = dbexercise.get_full_path()
        path = exerciseassetpath
        questions = root.xpath("//question")
        macrolist = root.xpath("//macros")
        globals_ = root.xpath("//global")
        base = root.xpath("//exercise")
        for g in base :
            tags = set( [ str( child.tag  ) for child in g ] )
            allowed_tags = set( ['question','exercisename','text','global','macros','studentasset','solution','figure','hidden','right','asciimath','qmath','ignore','hide','instructions','querypath'] )
            disallowed =  ",".join( list( tags - allowed_tags  ) )
            if  disallowed :
                assert False,  f"tags {disallowed} is not allowed in exercise " 


        if globals_ :
            for g in globals_ :
                globalxml = etree.tostring(g ).decode()
                assert globalxml.find('&')  < 0 ,  "Illegal character & in global"
                tags = set( [ child.tag for child in g ] )
                allowed_tags = set( ['hint','var','vars','ops','op','func','blacklist','func','oneforms','funcs'] )
                disallowed =  ",".join( list( tags - allowed_tags  ) )
                if  disallowed :
                    assert False,  f"tags {disallowed} is not allowed in global " 
        texts = root.xpath("//text") 
        if texts :
            for t in texts :
                tags = set( [child.tag for child in t ] )
                for i in ['text'] :
                    if i in tags :
                        assert False , f" tag {i} is not allowed as a subtag of text"

        if not isinstance( macrolist, list ) :
            macrolist = [macrolist]
        try :
            d = macrolist_to_dict( macrolist)
        except Exception as e :
            raise e
        keys = [ key for (key,val) in d.items() ]
        for key in keys :
            result =  list( filter(lambda x: key in x , keys ) ) 
            assert len(result) == 1 , f'Ambiguous key {key} occurs in {str(result)}. The longer key will be parsed using the shorter one, so rename them. '
        number_of_webworks = 0;
        qtypes = [ item.attrib.get("type",settings.DEFAULT_QUESTION_TYPE ) for item in questions ];
        #if len( root.xpath('//global')  ) > 0  :
        #    messages = validate_exercise_globals(xml, user, exercise, extradefs)
        for question in questions:
            qtype = question.attrib.get("type")
            if not qtype :
                qtype = settings.DEFAULT_QUESTION_TYPE
            if qtype == 'webworks' :
                number_of_webworks = number_of_webworks + 1;
                tags = question.xpath("./*")
                for tag in tags :
                    if not tag.tag  in  ["source" ]:
                        messages.append(("error",  f"webworks cannot have have a tag {tag.tag}"))
                        break;
            key = question.attrib['key']
            if not settings.RUNTESTS :
                skip = False 
                try :
                    dbquestion = (
                        Question.objects.using(db)
                        .select_related("exercise", "exercise__meta")
                        .get(exercise__exercise_key=exercise_key, question_key=key)
                    )
                except  ObjectDoesNotExist :
                    skip = True
                if not skip :
                    try :
                        r = (dbquestion.validate_xml(xml) );
                    except AssertionError as e :
                        msg = f"Error in {key}: " + html.unescape( str(e) )
                        messages.append( ('error', msg ) )
                        return messages
                    except Exception as e:
                        messages.append(('error' , f"Cannot validate {key} {str(e)} "))
                        return messages
                        #raise e
            else :
                try :
                    from exercises.models import validate_question_xml 
                    question_key = key 
                    username = 'super'
                    xml = xml.encode('utf-8')
                    r = validate_question_xml(  db , exercise_key, question_key, username, xml )
                except Exception as e:
                    messages.append(('error' , f"Cannotb validate {key}"))
                    return messages
                    #raise e


        if number_of_webworks > 1 :
            messages.append(("error",  f"You can only have one webwork question in an exercise"));
        figures = root.xpath("//figure")
        for figure in figures:
            fil = f"{figure.text}".strip()
            filename = os.path.join(path, fil)
            if not "@" == filename[0]:
                if not os.path.isfile(filename):
                    messages.append(
                        (
                            "error",
                            f"file {fil} in figure does not exist. Check assets and note that your figure file you uploaded may have been renamed by OpenTA.",
                        )
                    )
                filetype = (fil.split(".")[-1]).lower()
                if filetype in ["pdf"]:
                    messages.append(("error", f" PDF is not allowed in figure file"))
                elif not filetype in ["jpg", "jpeg", "png","gif"]:
                    messages.append(("error", f"only filetypes jpg,jpeg,png allowed in figure"))
        assets = root.xpath("//asset")
        for asset in assets:
            fil = f"{asset.text}".strip()
            filename = os.path.join(path, fil)
            if not "@" == filename[0]:
                if not os.path.isfile(filename):
                    msg = f"asset file {filename} does not exist"
                    messages.append(("error", msg))
        xmlschema.assert_(root)
    except etree.XMLSyntaxError as err:
        messages.append(("error", "Parsing Error:{0}".format(err)))
    except AssertionError as err:
        logger.error(f"ASSERTION {str(err)}")
        formatted_lines = traceback.format_exc()
        #logger.error(f"FORMATTED_LINES {formatted_lines}")
        #logger.error(f"ASSERT ERROR {str(err)} ")
        msg = "{0}".format(err)
        if 'not expected' in msg :
                msg = msg.split('Element')[1] 
        etype = "error"
        if "Element 'code'" in msg:
            msg = "Wrap the content of the &lt;code&gt;  ... &lt;/code&gt; tag as &lt;code&gt;&lt;![CDATA[ ... ]]&gt;&lt;/code&gt;"
        elif "The attribute 'type'" in msg:
            msg = 'external scripts must include the attribute type="module" i.e. &lt;script type="module"&gt; ... &lt;/script&gt;  for javascript files or type="text/javascript" for text script'
            etype = "warning"
        elif  "hidden" in msg and  "Character content other than whitespace is not allowed " in msg :
            msg = f"  Hint: content of &lt;hidden&gt; needs to be valid xml. Wrap character content with &lt;text&gt; tag "
        elif "Element 'pre'" in msg:
            msg = "Wrap the content of the &lt;pre&gt;  ... &lt;/pre&gt; tag as &lt;pre&gt;&lt;![CDATA[ ... ]]&gt;&lt;/pre&gt;"
        elif "Element 'text': This element is not expected" in msg:
            msg = "The &lt;text&gt; tag is not expeced. \n Is it nested? \n It should not be:  Suggested fix: Change  for instance &lt;text&gt; string1 &lt;text&gt; string2 &lt;/text&gt; string3 &lt;/text&gt; to &lt;text&gt; string1 &lt;/text&gt;&lt;text&gt; string2 string3 &lt;/text&gt; "
            etype = "warning"
        elif "Element 'exercise': Character content other than whitespace is not allowed " in msg:
            msg = "The &lt;exercise&gt; tag should not contain character content; Suggestion: wrap the desired character content with &lt;text&gt ... &lt;/text&gt; so that &lt;text&gt; is a direct child of &lt;exercise&gt;"
        elif "Element 'qmath': This element is not expected" in msg:
            msg = msg + " You may need to wrap the element with &lt;text&gt tag "
            etype = "warning"
        elif "Element 'asciimath': This element is not expected" in msg:
            msg = msg + " You may need to wrap the element with &lt;text&gt tag "
            etype = "warning"
        elif "NCName" in msg:
            msg = (
                msg
                + " Hint: You have unpermitted character such as a blank in a filename. It is fragile but may work, but you will keep getting nagged until it is fixed."
            )
            etype = "warning"
        #elif "not expected" in msg:
        #    msg = (
        #        msg
        #        + ".  Unanticipated error. Possible reason for the error is not wrapping text blocks with &lt;text&gt; tags."
        #    )
        #    etype = "warning"
        messages.append((etype, "XML Error: " + msg))
    #except NameError as e:
    #    messages.append(("error", "Error 780: From validate_exercise_xml: " + type(e).__name__ + "  :  " + str(e)))
    except AttributeError as e:
        logger.error(f"ATTRIBUTE ERROR")
        if 'NoneType' in f"{str(e)}" :
            messages.append(("error", "expression tag cannot be empty "))
        else :
            messages.append(("error", "Cannot validate expression : error 798"))
            formatted_lines = traceback.format_exc()
            logger.error(f"FORMATTED_LINES {formatted_lines}")
    except TypeError as err:
        logger.error(f"TYPE ERROR")
        formatted_lines = traceback.format_exc()
        logger.error(f"f{formatted_lines}")
        msg = "{0}".format(err)
        if "NoneType" in msg:
            msg = "Validation error of exercise xml: Probably missing global: Put in empty global tag after &lt;/exercisename&gt  &lt;global/&gt; "
        if "Cannot convert symbols to int" in msg:
            msg = f"Probably boolean error (using istrue instead of iscorrect?)";
        messages.append(("error", "Error 791: " + msg))
    except IndexError as err :
        logger.error(f"IndexError")
        formatted_lines = traceback.format_exc()
        logger.error(f"f{formatted_lines}")
        messages.append(("error","Did you forget globals"))
    except FileNotFoundError as e:
        logger.error(f"FileNotFouindError")
        messages.append(("error",f"File not found error. This exercise may be corrupted. {str(e)}  "))

    except MacroError as e:
        logger.error(f"MacroError")
        messages.append(("error",str(e)))
    except ObjectDoesNotExist as e :
        formatted_lines = traceback.format_exc()
        logger.error(f"FORMATTED_LINES {formatted_lines}")
        messages.append(('error' , "Validation skipped on key change. Save again to validate. "))
    except Exception as e:
        logger.error(f"UNCAUGHT ERROR")
        formatted_lines = traceback.format_exc()
        logger.error(f"UNCAUGHT FORMATTED_LINES {formatted_lines}")
        messages.append(
            (
                "error",
                "Error 794: Uncaught exception from validate_exercise_xml: " + type(e).__name__ + "  :  " + str(e),
            )
        )
    return messages


#@permission_required("exercises.edit_exercise")
@csrf_exempt
@api_view(["POST","GET"])
def exercise_set_selected_exercises(request, instruction):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    if not "selectedExercises" in request.data.keys():
        return Response({})
    exercise_keys = request.data["selectedExercises"]
    #cachekey = request.user.username + db + 'selectedExercises'
    #caches['default'].set( cachekey ,exercise_keys)
    set_selectedExercisesKeys( request.user, db, exercise_keys)


    data = []
    for exercise_key in exercise_keys:
        exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        meta = ExerciseMeta.objects.using(db).get(exercise=exercise)
        logger.info("META IMAGE IS %s " % meta.image)
        etype = "obligatory" if meta.required else ("bonus" if meta.bonus else "optional")
        data.append(
            {
                "exercise_key": exercise_key,
                "name": exercise.name,
                "type": etype,
                "published": meta.published,
                "deadline": str(meta.deadline_date),
                "locked": meta.locked,
                "difficulty": meta.difficulty,
                "feedback": meta.feedback,
                "solution": meta.solution,
                "image": meta.image,
                "allow_pdf": meta.allow_pdf,
                "student_assets": meta.student_assets,
            }
        )
    # data = [{'exercise_key' : item } for item in request.data['selectedExercises']  ]
    return Response(data)


@permission_required("exercises.edit_exercise")
@api_view(["GET","POST"])
@csrf_exempt
def exercise_save(request, exercise):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    messages = []
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    # CHECK IF THERE ARE SYMLINKS IN THE PATH; IF SO REFUSE TO SAVE

    #### FIX THIS PATH IF DIRECTORY DOES NOT EXIST 
    path = dbexercise.get_full_path()
    issymlink, symlink = contains_symlink(path)
    if issymlink:
        messages.append(("warning", "You cannot save edits to this exercise since it is not rooted in your course"))
        #result = response_from_messages(messages)
    backup_name = "{:%Y%m%d_%H:%M:%S_%f_}".format(now()) + request.user.username + ".xml"
    xml = request.data["xml"]
    try:
        parser = etree.XMLParser(recover=True, remove_comments=True)
        root = etree.fromstring(xml)
    except Exception as e:
        messages = [("error", f"Refusing to save due to fatal xml syntax error: {type(e).__name__} {str(e)} ")]
        return Response(response_from_messages(messages))
    dbname = db
    try :
        #print(f"VALIDATE_EXERCISE_SAVE IN EXERCISE")
        msg = validate_exercise_xml(xml, request.user, exercise,db)
    except Exception as e :
        logger.error(f"ERROR SAVING {str(e)} ")
        backup_name = None
    #if 'error' in dict(msg) :
    #    backup_name = None
    #if backup_name == None :
    #    print(f"REFUSING TO BACK UP ")

    try:
        if not issymlink :
            messages += parsing.exercise_save(path, xml, backup_name, request.user.username,"EXERCISE_SAVE_IN_API")
    except IOError as e:
        messages.append(("error", str(e)))



    @transaction.atomic(using=db)
    def update_exercise(db=settings.DB_NAME):
        #root = fromString(xml)
        #elems = root.findall(".//alt")
        #for elem in elems:
        #    logger.info("ELEM TXT = %s " % elem.text)
        #    try:
        #        if "hashkey" in elem.attrib and not elem.text.strip()  == '' :
        #            hsh = elem.attrib["hashkey"]
        #            # logger.info("HSH = %s " % []hsh )
        #            language = elem.attrib["lang"]
        #            # logger.info("LANG = %s " % language)
        #            tr = Translation.objects.using(db).get_or_create(
        #                hashkey=hsh, language=language, exercise=dbexercise
        #            )
        #            # logger.info("TRANSLATED TEXT = %s " % elem.text )
        #            tr.translated_text = str(elem.text)
        #            tr.save(using=db)
        #            logger.info("TR SAVED %s " % tr)
        #    except Exception as e:
        #        logger.info(f"ERROR {type(e).__name__} EXERCISES_API HASHKEY %s NOT FOUND " % hsh)

        return Exercise.objects.add_exercise_full_path(dbexercise.path, dbexercise.course, db=db)

    try:
        messages += update_exercise(db=db)
    except parsing.ExerciseParseError as e:
        messages.append(("warning", str(e)))
    except Exception as e :
        messages.append(("warning", 'w13: ' + str(e)))
        result = response_from_messages(messages)
        return Response( result )
    #msg = [ (k,v) for  k,v in dbexercise.validate().items() ]
    try :
        messages = messages + validate_exercise_xml(xml, request.user, exercise,db)
    except Exception as e :
        logger.error(f" {messages} =  messages + validate_exercise_xml(xml, request.user, exercise,db) failed in api.py with exception {str(e)} ")
        messages.append(("error", str(e)))

    #keys = [ key for (key,val) in messages if key not in  ['info', 'success' ] ]
    #if len( keys ) == 0  and not issymlink :
    #    messages.append(('warning' , 'Exercise saved'))
    #print(f"keys = {keys}")
    msgdict = dict( messages )
    # ON KEY CHANGE, TRANSACTION ATOMIC DOES NOT WRITE
    # THEREFORE REDO  IF THAT FAILS THE FIRST TIME
    if 'error' in msgdict :
        if 'key change' in msgdict['error'] :
            messages = []
            newmsg = update_exercise(db=db)
            logger.error(f"NEWMSG = {newmsg}")
            messages  +=  validate_exercise_xml(xml, request.user, exercise,db) 
    result = response_from_messages(messages)
    return Response(result)


def custom_key(group,request):
    # Use the user's ID if authenticated, otherwise fallback to IP
    if request.user.is_authenticated:
        if request.user.is_staff :
            key = str( datetime.datetime.now() ) # BOGUS KEY FOR STAFF; DON'T ENFORCE RATELIMT
            return key
        return str(request.user.id)
    else :
        return request.META.get('REMOTE_ADDR', '')

@ratelimit(key=custom_key , rate=settings.RATE_LIMIT , block=True)
@api_view(["POST", "GET"])
def exercise_check(request, exercise, question):
    subdomain, db = get_subdomain_and_db(request)
    if db == None :
        db = request.META["HTTP_HOST"].split(".")[0];
        subdomain = db ;
    user = request.user
    username = user.username
    # if ( not subdomain == settings.SUBDOMAIN  ) and (not subdomain == '' ) :
    #   logger.error(f"EXCERCISE_CHECK SUBDOMAIN INCONSISTENT {subdomain} {settings.SUBDOMAIN}")
    #  settings.SUBDOMAIN = subdomain
    #    settings.DB_NAME = subdomain
    try:
        result = {"error" : 'Unknown error'}
        dbquestion = "dbquestion"
        exercise_name = "exercise_name"
        answer_data = ""
        A = ""
        answer_data = request.data["answerData"]
        A = A + "1"
        exercise_key = str(exercise)
        A = A + "2"
        fails = True
        for tries in [0, 1]:
            try:
                if fails:
                    dbquestion = (
                        Question.objects.using(db)
                        .select_related("exercise", "exercise__meta")
                        .get(exercise__exercise_key=exercise_key, question_key=question)
                    )
                qtype = dbquestion.type
                fails = False
            except TransactionManagementError as e:
                logger.error(f" ERROR 19799123a tries = {tries} {type(e).__name__} {str(e)} ")
                time.sleep(1.0)
            except Exception as e:
                logger.error(f" ERROR 19799123b tries = {tries} {type(e).__name__} {str(e)} ")
                time.sleep(1.0)
        if fails:
            return Response({"error": f"Database busy; try again with {answer_data}"})
        dbexercise = dbquestion.exercise
        meta = dbexercise.meta
        published  = meta.published
        A = A + "3"
        if not settings.RUNNING_MANAGEMENT_COMMAND and not published and not user.has_perm("exercises.edit_exercise"):
            logger.error(f"ERROR403 ERROR 1285")
            return Response({"error": _("Exercise not activated.")}, status.HTTP_403_FORBIDDEN)
        A = A + "4"
        if getattr(request, "limited", False) and not request.user.is_staff and not settings.RUNNING_DEVSERVER:
            return Response({"error": _("You are limited to ") + "5" + _(" exercise check tries per minute.")})

        A = A + "5"
        agent = request.META.get("HTTP_USER_AGENT", "unknown")
        A = A + "6"
        exercise_name = str( dbexercise.name ).strip();
        qtype = dbquestion.type
        A = A + "7"
        msg = f"EXERCISE_CHECK  {A} subdomain={subdomain}   user={request.user}  name={exercise_name} question={question} db={db}"
        isin = str(qtype) in ['aibased','textbased']
        result = question_module.question_check(request, db, user, agent, exercise_key, question, answer_data)
        A = A + "8"
        msg = f"EXERCISE_CHECK  {A} subdomain={subdomain}   user={request.user}  name={exercise_name} question={question} db={db}"
        msg = ( "OK " + msg + f" answer_data={answer_data}  correct=>{result.get('correct','') }< error=>{result.get('error','')}< warning=>{result.get('warning','') }< key={exercise_key} ").replace("\n",' ')
        res = Response(result)
        syntax_error = not "correct" in result
        if syntax_error:
            res["corrected"] = "false"
        else:
            res["corrected"] = "true"
        return res
    except Exception as e:
        formatted_lines = traceback.format_exc()
        logger.error(
            f"ERROR 221934a IN EXCERCISE_CHECK {A} {type(e).__name__} subdomain={subdomain} user={request.user} exercise={exercise} question={question} type={qtype} answer_data={answer_data}  {formatted_lines}  "
        )
        formatted_lines = traceback.format_exc()
        logger.error(f"ERROR 221934b IN EXCERCISE_CHECK {A} {type(e).__name__} subdomain={subdomain} user={request.user} exercise={exercise_name} question={question}  type={qtype} answer_data={answer_data} ")
        logger.error(f"FORMATTED_LINES {formatted_lines}")
        return Response({"error": f"Unknknown error {type(e).__name__}"})
    #    return Response({'error': f"EXERCISE_CHECK 221934 {str(e)  }"} )


@never_cache
@api_view(["GET"])
def question_last_answer(request, exercise, question):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    dbquestion = Question.objects.using(db).get(exercise=dbexercise, question_key=question)
    dbanswer = Answer.objects.using(db).filter(user=request.user, question=dbquestion).latest("date")
    serializer = AnswerSerializer(dbanswer)
    return Response(serializer.data)


def upload_pdf(file, name, dbexercise, user,db):
    try :
        if not dbexercise.meta.allow_pdf:
            return Response({"error" : "PDF upload not allowed"})
    except Exception as err :
        logger.error(f" ERROR E8109199924  File upload error while uploading {file} by {user} for exercise {dbexercise} ")
        return Response({"error" : "Unknown error. Try again. If propblem persists, contact examiner"})

    # convert_from_path(file, output_folder="/tmp", fmt="png", size=(1024,None), output_file="outy" )
    # convert_from_bytes(file )
    # print(f"API UPLOAD_PDF user={user} file={file} {vars(file)}")

    try:
        pypdf.PdfReader(file, strict=True)
        image_answer = ImageAnswer(
            user=user,
            exercise=dbexercise,
            # exercise_key=exercise,
            pdf=file,
            filetype=ImageAnswer.PDF,
        )
        image_answer.save(using=db)
        logger.error( f"SUCCESS : PDF_UPLOAD Upload  user={user} {db} exercise={dbexercise.name} {image_answer.pk} ")
        return Response({})
    except Exception as e:
        logger.error(f" File upload error while uploading {file} by {user}. Reason {str(e)}. ")
        if not 'Urkund' in str(e) :
            msg =  f"Invalid image file. Upload failed. Hint: { str(e) } Workaround: If you can't figure out the problem, print and save the file, view the new file on your computer, and then upload the new file."
        else :
            msg = str(e)
        return Response(
            {
                "error": msg
            }
        )


def upload_image(file, name, dbexercise, user, subdomain):
    extension = name.split(".")[-1]
    # print(f"UPLOAD IMAGE NAME = {name} {extension}")
    # print(f"UPLOAD IMAGE FILE = {type(file)}  {file} {vars(file)}")
    db = 'default' if settings.RUNTESTS else subdomain
    if not extension in ["pdf", "PDF"]:
        try:
            trial_image = Image.open(file)
            trial_image.verify()
            image_answer = ImageAnswer(
                user=user,
                exercise=dbexercise,
                # exercise_key=exercise,
                image=file,
                filetype=ImageAnswer.IMAGE,
            )
            extension = image_answer.image.path.split(".")[-1]
            image_answer.save(using=db)
            # if  not 'tif' in extension :
            image_answer.compress()
            if settings.USE_URKUND and os.path.exists(f"/subdomain-data/{subdomain}/urkund.py") :
                r  = {"error" : "You are required to submit a pdf. This file cannot be handled by urkund."};
            else :
                r = {"warning" : "Saved"}
            logger.error( f"SUCCESS : IMAGE_UPLOAD Upload  user={user} {subdomain} exercise={dbexercise.name} {image_answer.pk}  ")
            return Response(r)
        except UnidentifiedImageError as e:
            msg = f"ERROR: {user.username} {settings.SUBDOMAIN} tried {file.name} upload and was rejected"
            logger.error(msg)
            return Response(
                {"error": f"Uploaded file {name} is not acceped. File is either  damaged or not of type png or jpg"}
            )
        except Exception as e:
            logger.error(
                f"ERROR: FILE_UPLOAD EXCEPTION: Upload error {type(e).__name__} user={user} exercise={exercise} "
            )
            if extension.lower()  not in ["png", "PNG", "jpg", "JPG", "JPEG",'jpeg']:
                return Response({"error": f"file image of type {extension}. Use jpg or png"})
            else:
                return Response(
                    {
                        "error": f"file image error in file of type {extension}. The file appears damaged "
                    }
                )
    else:
        return Response(
            {
                "error": f"file image error-2 in file of type {extension}. Either the file is damaged or it is of type jpg or png"
            }
        )


@api_view(["GET"])
@parser_classes((MultiPartParser,))
def upload_blob(request, exercise):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    body = request.body.decode("utf-8")
    # print("GET BLOB BODY ", request.body)
    return Response({})


@api_view(["POST"])
@parser_classes((MultiPartParser,))
@never_cache
def reupload_answer_image(request, exercise, action, asset):
    # print(f"REUPLOAD action={action} asset={asset} ")
    subdomain, db, user = get_subdomain_and_db_and_user(request)
    try:
        user = request.user
        image_answer = ImageAnswer.objects.using(db).get(pk=asset)
        try:
            file = request.FILES["file"]
        except Exception as e:
            logger.error(" FILES_REQUEST_TRACEBACK  %s %s  %s " % (str(e), type(e).__name__))
            return Response(
                {
                    "error": "Unknown error in file upload; pdf, png or jpg only \n If you are consistenly unable to upload one of these filetypes, send an email to opentaproject@gmail.com"
                }
            )
        # print(f" FILE OBTAINED")
        try:
            dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        except ObjectDoesNotExist as e:
            msg = f"ERROR E77193652 {settings.SUBDOMAIN} {request.user} {exercise} EXERICSE_DOES_NOT_EXIST"
            logger.error(msg)
            return Response({"error": "Unknown error in upload; reload and try again"})

        if file.size > 14e6:
            return Response(
                {
                    "error": _(
                        "File upload failed. File larger than 14mb, please try to reduce the size "
                        "and upload again. (For images try to reduce the resolution"
                        " and for pdf files the problem is most likely large embedded images.)"
                        " There is actually no good reason to upload files of any type larger than approx 3mb."
                    )
                }
            )

        extension = file.name.split(".")[-1]
        # print(f"EXTENSION = ", extension)
        # print(f"PDF IS ", image_answer.pdf)
        if extension == "pdf":
            name = image_answer.pdf.name
        else:
            name = image_answer.image.name
        # print(f"NAME = ", name)
        # print(f" UPLOADED FILE NAME = {file.file.name}  ")
        # print(f" OLD FILE NAME = {image_answer.image.name}")
        student_filename = settings.VOLUME + "/" + name
        hashtag = (hashlib.md5(student_filename.encode()).hexdigest())[0:7]
        safekeep_filename = student_filename + "." + hashtag
        # print(f" SAVED COPY AS {safekeep_filename}")
        # time.sleep(.5)
        if action == "save":
            logger.error(f"safekeep={safekeep_filename} student_filename={student_filename}")
            if not os.path.exists(safekeep_filename):
                shutil.copy2(student_filename, safekeep_filename)
            os.remove(student_filename)
            shutil.copy2(file.file.name, student_filename)
            os.chmod(student_filename, 0o755)
            return Response({"warning": "Student image replaced!"})
        elif action == "reset":
            if os.path.exists(safekeep_filename):
                shutil.copy2(safekeep_filename, student_filename)
                os.remove(safekeep_filename)
            return Response({"warning": "Student image restored!"})
        else:
            return Response({"error": " no action defined"})
    except Exception as e:
        return Response({"error": f"Failed to replace image: { type(e).__name__}   {str(e)} "})


@api_view(["POST"])
@parser_classes((MultiPartParser,))
def upload_answer_image(request, exercise):
    # print("upload_answer_image")
    subdomain, db, user = get_subdomain_and_db_and_user(request)
    username = user.username
    allow_pdf = True
    try:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        assert bool( dbexercise )  , "DBEXERCISE IS EMPTY!"
        allow_pdf = dbexercise.meta.allow_pdf

    except ObjectDoesNotExist as e:
        msg = f"ERROR E77193652 {settings.SUBDOMAIN} {request.user} {exercise} EXERICSE_DOES_NOT_EXIST"
        logger.error(msg)
        return Response({"error": "(E12181) Unknown error in upload; reload and try again"})
    except AssertionError as e:
        msg = f"ERROR E77193654 {settings.SUBDOMAIN} {request.user} {exercise} dbexercise was not available"
        logger.error(msg)
        return Response({"error": "(E12182) Unknown error in upload; reload and try again"})
    # logger.info("REQUEST IN API.PY UPLOAD_ANSWER_IMAGE %s " % request)
    try:
        file = request.FILES["file"]
    except Exception as e:
        logger.error(" FILES_REQUEST_TRACEBACK  %s %s  %s " % (str(e), type(e).__name__))
        return Response(
            {
                "error": "Unknown error in file upload; pdf, png or jpg only \n If you are consistenly unable to upload one of these filetypes, send an email to opentaproject@gmail.com"
            }
        )




    if file.size > 14e6:
        return Response(
            {
                "error": _(
                    "File upload failed. File larger than 14mb, please try to reduce the size "
                    "and upload again. (For images try to reduce the resolution"
                    " and for pdf files the problem is most likely large embedded images.)"
                    " There is actually no good reason to upload files of any type larger than approx 3mb."
                )
            }
        )

    extension = file.name.split(".")[-1]
    name = file.name
    # convert_from_path("tmp.pdf", output_folder="/tmp", fmt="png", size=(1024,None), output_file="outy" )
    # print(f"FILE = {file}  type={type(file)} {vars(file)}" )
    # print(f"EXTENSION = {extension}")
    if extension in ["pdf", "PDF"]:
        pdf_name = name
        tname = file.file
        pdf_path = file.file.name
        pdf_dir = os.path.dirname(pdf_path)
        output_file = file.name.split(".")[0]
        if not allow_pdf :
            image_files = convert_from_path(
                pdf_path, output_folder=pdf_dir, fmt="png", size=(1024, None), output_file=output_file, paths_only=True
            )
            # print(f"IMAGE_FILES = {image_files}")
            for image_file in image_files:
                tempfile.tempdir = "/tmp"
                prefix = image_file.split("/")[-1].split(".")[0]
                temp = tempfile.NamedTemporaryFile(prefix=prefix, suffix=".png", delete=False)
                shutil.copy2(image_file, temp.name)
                name = temp.name.split("/")[-1]
                size = os.path.getsize(image_file)
                if not size == 0:
                    ifile = django.core.files.uploadedfile.TemporaryUploadedFile(
                        content_type="image/png", charset="None", size=size, name=name
                    )
                    ifile.file = temp
                    upload_image(ifile, name, dbexercise, user, subdomain)
                    os.remove(image_file)
            return Response(
                {"error": f"Converted {pdf_name} to png"}
            )  # THIS SHOULD NOT BE ERROR BUT I CANT GET OTHER TO GENERATE ALERT
        else:
            return upload_pdf(file, pdf_name, dbexercise, user,db)
    else:
        return upload_image(file, name, dbexercise, user, db)


# @api_view(['GET']) Allow answer image to viewed from another device provided student is logged in
@never_cache
def answer_image_view(request, image_id):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    if not request.user.is_authenticated:
        # ALLOW POST REQUESTS SO A STUDENT CAN PULL UP THE ASSET ON ANOTHER DEVICE
        return HttpResponse("<h3> (E9918) You must be logged in to see this asset </h3>")

    subdomain = settings.SUBDOMAIN
    try:
        image_answer = ImageAnswer.objects.using(db).get(pk=image_id)
        if image_answer.user == request.user or request.user.is_staff:
            if image_answer.filetype == "IMG":
                dev_path = str(image_answer.image.path)
                prod_path = dev_path
                #dev_path = dev_path.replace(settings.VOLUME, ("%s/" % settings.VOLUME) + subdomain + "/media")
                prod_path = prod_path.replace("/%s" % settings.VOLUME, "")
                devpath = urllib.parse.unquote(str(image_answer.image.path))
                accel_xpath = urllib.parse.unquote(re.sub(r"^%s" % settings.VOLUME, "", str(image_answer.image.path)))
                vol = (settings.VOLUME).lstrip("/")
                old_devpath = re.sub(f"{vol}/answerimages", f"{vol}/{settings.SUBDOMAIN}/media/answerimages", devpath)
                if os.path.exists(devpath):
                    pass
                    # logger.info(f"ORIG PATH EXISTS: {devpath}  ")
                elif os.path.exists(old_devpath):
                    # logger.info(f"LEGACY DEV PATH EXISTS: {devpath}  ")
                    path = re.sub(f"{settings.VOLUME}/", "", old_devpath)
                    image_answer.image = re.sub("^/", "", path)
                    image_answer.save(using=db)
                else:
                    pass
                    # logger.info(f"NEITHER   PATH EXISTS : {devpath} ")

                return serve_file(
                    prod_path,
                    os.path.basename(image_answer.image.name),
                    content_type="image/jpeg",
                    dev_path=devpath,
                    source="answer_image_view_img",
                    devpath=devpath,
                    accel_xpath=accel_xpath,
                )
            if image_answer.filetype == "PDF":
                dev_path = ("%s/" % settings.VOLUME) + str(image_answer.pdf.name)
                prod_path = str(image_answer.pdf.name)
                devpath = dev_path
                devpath = dev_path # f"{settings.VOLUME}/{image_answer.pdf.name}"
                accel_xpath = prod_path
                # accel_xpath = f"{subdomain}/{accel_xpath}"
                return serve_file(
                    prod_path,
                    os.path.basename(image_answer.pdf.name),
                    content_type="application/pdf",
                    dev_path=devpath,
                    source="answer_image_view_pdf",
                    devpath=devpath,
                    accel_xpath=accel_xpath,
                )
        else:
            return HttpResponse("<h3> You must be asset owner to to view the asset </h3>")
    except ObjectDoesNotExist:
        return HttpResponse("<h3> The requested image does not exist </h3>")


@api_view(["GET"])
def answer_image_thumb_view(request, image_id):
    subdomain, db , user = get_subdomain_and_db_and_user(request)
    settings.SUBDOMAIN = subdomain
    er = ""
    try:
        image_answer = ImageAnswer.objects.using(db).select_related("user", "exercise").get(pk=image_id)
        # logger.info(f"IMAGE_ANSWSER = {image_answer}")
        image_thumb = image_answer.image_thumb
        # logger.info(f"IMAGAE THUMB = {image_thumb}")
        devpath = urllib.parse.unquote(str(image_answer.image.path))
        vol = (settings.VOLUME).lstrip("/")
        old_devpath = re.sub(f"{vol}/answerimages", f"{vol}/{subdomain}/media/answerimages", devpath)
        # logger.info(f"ANALYZE {devpath}")
        # LEGACY LOCATION OF images need to be fixed on demand
        if os.path.exists(devpath):
            # logger.info(f"ORIG PATH EXISTS: {devpath}  ")
            pass
        elif os.path.exists(old_devpath):
            logger.error(f"LEGACY DEV PATH EXISTS at  {old_devpath}  ")
            # settings.IMAGEKIT_CACHEFILE_DIR = path
            path = re.sub(f"{settings.VOLUME}/", "", old_devpath)
            image_answer.image = re.sub("^/", "", path)
            image_answer.save(using=db)
            logger.error("UPDATED!")
        else:
            logger.error(f"NEITHER   PATH EXISTS : {devpath} {old_devpath} ")
        # thumb_file=  '/ubdomain-data/' + urllib.parse.unquote( re.sub(r"^/media","/ubdomain-data", str( image_answer.image_thumb.url ) ) )
        # logger.info(f"IMAGE_THUMB = {thumb_file}")
        # full_image = image_answer.image
        # try :
        #    image_answer.image_thumb.generate()
        #    logger.info(f"SUCCEEDED REGENERATE IMAGE_THUMB for {image_id}")
        # except Exception as e :
        #    logger.info(f"FAILED REGENERATE IMAGE_THUMB for {image_id}")
        # logger.info(f"image_thumb.url = {image_answer.image_thumb.url}")
        if image_answer.user == user or user.is_staff :
            # logger.info("ANSWSER IMAGE THUMB VIEW %s " % image_answer.image_thumb.url)
            er = er + "1"
            dev_path = settings.VOLUME + "/" + subdomain + str(image_answer.image_thumb.url)
            er = er + "2"
            dev_path = urllib.parse.unquote(re.sub(r"^/media", settings.VOLUME, str(image_answer.image_thumb.url)))
            er = er + "3"
            #dev_path = re.sub(r"%s" % settings.VOLUME, f"{settings.VOLUME}/CACHE", dev_path)
            #er = er + "4"
            dev_path = urllib.parse.unquote(dev_path)
            er = er + "5"
            # accel_xpath = urllib.parse.unquote( re.sub(r"^/media","", image_answer.image_thumb.url ) )
            accel_xpath = urllib.parse.unquote(re.sub(r"^/media", "", image_answer.image_thumb.url))
            er = er + "6"
            # logger.info("ANSER IMAGE THUMB VIEW DEV_PATH %s" % str( dev_path) )
            devpath = settings.VOLUME + accel_xpath
            er = er + "7"
            return serve_file(
                urllib.parse.unquote("/" + subdomain + image_answer.image_thumb.url),
                os.path.basename(image_answer.image.name),
                content_type="image/jpeg",
                dev_path=dev_path,
                source="answer_image_thumb_view",
                devpath=devpath,
                accel_xpath=accel_xpath,
            )
            er = er + '8'
        else:
            logger.error(f"ERROR403 {er} ERROR LINE NUMBER 1676")
            return Response({"error": "Not authorized"}, status.HTTP_403_FORBIDDEN)
    except FileNotFoundError as e:
        logger.error(f"ERROR403 FILE IMAGE_THUMB FILE NOT FOUND ERROR LINE 1687 er={er} {devpath}")
        return Response({"error": "FileNotFound"}, status.HTTP_403_FORBIDDEN)
    except ObjectDoesNotExist:
        logger.error(
            f"FILE IMAGE_THUMB OBJECT DOES NOT EXIST ERROR LINE 1690 er={er} {subdomain} {request.user} {image_id}  "
        )
        return Response("invalid answer image id", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        # TODO RETURN AN ICON IF IT IS A PDF
        logger.error(
            f"ERROR403 FILE IMAGE_THUMB UNCAUGHT ERROR ERROR LINE 1695 er={er} {type(e).__name__} subdomain={subdomain} image_id={image_id} user={request.user}  image_answer={vars(image_answer)}  "
        )
        return Response({"error": "FileNotFound"}, status.HTTP_403_FORBIDDEN)


@permission_required("exercises.administer_exercise")
@api_view(["GET"])
def exercise_test_view(request, exercise):
    return Response(exercise_test(exercise))


@permission_required("exercises.administer_exercise")
def exercises_test(request):
    subdomain, db = get_subdomain_and_db(request)

    def format_test(exercise):
        return {
            "exercise": exercise.exercise_key,
            "questions": exercise_test(exercise.exercise_key),
            "exercise_name": exercise.name,
        }

    exercises = Exercise.objects.using(db).all()
    results = [format_test(exercise) for exercise in exercises]
    return TemplateResponse(request, "exercises_test.html", {"results": results})


@api_view(["GET"])
def image_answers_get(request, exercise):
    settings.SUBDOMAIN = get_subdomain(request)
    subdomain, db = get_subdomain_and_db(request)
    image_answers = ImageAnswer.objects.using(db).filter(user=request.user, exercise__exercise_key=exercise)
    image_answers_serialized = ImageAnswerSerializer(image_answers, many=True)
    image_answers_id_list = [image_answer.pk for image_answer in image_answers]
    return Response({"ids": image_answers_id_list, "data": image_answers_serialized.data})


@api_view(["POST"])
def image_answer_delete(request, pk):
    subdomain, db, user = get_subdomain_and_db_and_user(request)
    try:
        image_answer = ImageAnswer.objects.using(db).get(pk=pk)
    except ObjectDoesNotExist as e:
        msg = f"ERROR E76197 ImageAnswer Delete {type(e).__name__} {subdomain} {user} {pk}"
        logger.error(msg)
        return Response({"deleted": 0, "error": "Id not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    try : 
        if not user == image_answer.user and not user.is_staff:
            return Response({"deleted": 0, "error": "Permission denied"})

        submitted_is_before = before_deadline( image_answer.exercise.course, image_answer.date - datetime.timedelta(minutes=10), image_answer.exercise.meta.deadline_date)
        now_is_before = before_deadline( image_answer.exercise.course,   now() , image_answer.exercise.meta.deadline_date)
        if not now_is_before and submitted_is_before  :
            return Response({"deleted": 0, "error": _("You cannot delete a file submitted before the deadline after the deadline has passed.")})

    except Exception as e :
        msg = f"ERROR E76197b ImageAnswer Delete {type(e).__name__} {subdomain} {user} {pk}"
        logger.error(msg)
    try:
        image_answer.remove_file()
    except Exception as e:
        logger.error(f"IMAGE REMOVE ERROR {type(e).__name__}")
    try:
        deleted, deltype = image_answer.delete()
    except Exception as e:
        msg = f"ERROR E76197c ImageAnswer Delete {type(e).__name__} {subdomain} {user} {pk}"
        logger.error(msg)
        return Response({"deleted": 0, "error": f"Id {pk} not found"} )
        
    logger.error(f"Image deleted {subdomain} {user} {pk}")
    return Response({"deleted": deleted})
