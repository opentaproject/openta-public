# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json
import logging
import os
import random
import re
from datetime import datetime
import time
import traceback
from utils import get_subdomain, get_subdomain_and_db
from django.core.cache import caches
from users.models import User



from django_ratelimit.core import is_ratelimited
from exercises.models import Answer, Exercise, Question
from exercises.parsing import (
    exercise_xmltree,
    get_questionkeys_from_xml,
    get_translations,
    global_and_question_xmltree_get,
    question_json_get,
    question_xmltree_get,
)
from exercises.serializers import AnswerSerializer
from exercises.util import deep_get
from exercises.views.asset import _dispatch_asset_path
from exercises.question import question_check_dispatch
from exercises.xmljson import BadgerFish
from lxml import etree

from backend.middleware import check_connection
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.translation import gettext as _
from exercises.question import get_usermacros, question_json_hooks, parsehints, get_safe_previous_answers, get_other_answers, get_previous_answers
from exercises.question import answer_class_dispatch

logger = logging.getLogger(__name__)

#question_check_dispatch = {}
#answer_class_dispatch = {};
#validate_question_dispatch = {};
#sensitive_tags = {}
#sensitive_attrs = {}
bf = BadgerFish(xml_fromstring=False)



def answer_class(  hijacked, view_solution_permission, user, user_agent, exercise_key, question_key, answer_data, old_answer_object=None, db=None, answer_class=None):
    return answer_class_( hijacked, view_solution_permission, user, user_agent, exercise_key, question_key, answer_data, old_answer_object=old_answer_object, db=db )


def answer_class_( hijacked, view_solution_permission,
    user,
    user_agent,
    exercise_key,
    question_key,
    answer_data,
    old_answer_object=None,
    db=None,
    answer_class=None,
):
    # print(f"VIEW_SOLUTION_PERMSSION = {view_solution_permission}")
    assert db != None, "_QUESTION_CHECKE DB=None"
    before_date = None
    check_connection(db)
    dbquestion = (
        Question.objects.using(db)
        .select_related("exercise", "exercise__meta", "exercise__course")
        .get(exercise__exercise_key=exercise_key, question_key=question_key)
    )
    qtype = dbquestion.qtype()
    dbexercise = dbquestion.exercise
    meta = dbexercise.meta
    course = dbexercise.course
    feedback = dbexercise.meta.feedback
    user = User.objects.using(db).get(username='super')
    studentassetpath = _dispatch_asset_path(user, dbexercise)
    try:
        usermacros = get_usermacros(user, exercise_key, question_key=question_key, before_date=before_date, db=db)
    except ObjectDoesNotExist:
        usermacros = {}
    usermacros["@call"] = "question_check"
    usermacros["@is_staff"] = user.is_staff
    tbeg = time.time()
    tbeg = time.time()
    if not settings.RUNTESTS and settings.DEBUG_PLUS:
        course_key = course.course_key
        exercise_path = dbexercise.path
        alternative_full_path = os.path.join(settings.VOLUME, db, "exercises", str(course_key), exercise_path)
        if not dbexercise.get_full_path() == alternative_full_path:
            logger.error(f"QUESTION_CHECK {dbexercise.get_full_path()} alternative_full_path={alternative_full_path} ")
    question_json = question_json_get(dbexercise.get_full_path(), question_key, usermacros,db)

    try:
        expression = question_json.get("expression").get("$")
    except Exception as e:
        expression = ""
    question_json = question_json_hooks[qtype]( question_json, question_json, dbquestion.pk, user.pk, exercise_key, feedback)
    xmltree = exercise_xmltree(dbexercise.get_full_path(), usermacros)
    # print("TIME3 = ",  ( time.time() - tbeg ) *1000 )
    question_xmltree = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0]
    if question_xmltree.xpath("macros") and settings.REFRESH_SEED_ON_CORRECT_ANSWER:
        refreshable_macros = True
    else:
        refreshable_macros = False
    [global_xmltree, question_xmltree] = global_and_question_xmltree_get(xmltree, question_key, usermacros)
    question_xmltree.append(etree.fromstring("<exercisekey>" + exercise_key + "</exercisekey>"))
    question_xmltree.set("exerciseseed", usermacros["@exerciseseed"])
    question_xmltree.set("questionseed", usermacros["@questionseed"])
    question_xmltree.set("exercise_key", exercise_key)
    question_xmltree.set("path", os.path.join(course.get_exercises_path(db), dbexercise.path))
    question_xmltree.set("user", str(user))

    studentassetpath = _dispatch_asset_path(user, dbexercise)
    exerciseassetpath = os.path.join(course.get_exercises_path(db), dbexercise.path)  ## NEED THIS
    question_xmltree.set("studentassetpath", studentassetpath)  ## NEED THIS
    question_xmltree.set("exerciseassetpath", exerciseassetpath)  ## NEED THIS
    global_xpath = '/exercise/global'
    try :
        global_xmltree = (xmltree.xpath(global_xpath))[0]
    except IndexError as e :
        global_xmltree = etree.fromstring("<global/>")
    runtime_element = etree.Element("runtime")
    runtime_element.append(etree.fromstring("<exercisekey>" + exercise_key + "</exercisekey>"))
    runtime_element.set("exercise_key", exercise_key)
    runtime_element.set("path", os.path.join(course.get_exercises_path(db), dbexercise.path))
    runtime_element.set("user", str(user))
    exerciseassetpath = os.path.join(course.get_exercises_path(db), dbexercise.path)
    runtime_element.set("studentassetpath", studentassetpath)
    runtime_element.set("exerciseassetpath", exerciseassetpath)
    question_xmltree.append(runtime_element)
    result = answer_class_dispatch[qtype]( question_json, question_xmltree, answer_data, global_xmltree)
    return result

