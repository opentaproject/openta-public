# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import glob
import re
import time
import sys, traceback
import ast
import datetime
from django.utils import timezone
from backend.middleware import verify_or_create_database_connection, create_connection
from exercises.question import _question_check, get_usermacros
from exercises.models import Exercise, Answer, Question
from aggregation.models import Aggregation
from django.contrib.auth.models import User
from aggregation.models import Aggregation
from course.models import Course
from django.conf import settings
import os
import json
import pickle
from users.models import OpenTAUser
import exercises
import aggregation as ag
import logging
from exercises.parsing import (
    question_json_get,
    exercise_xmltree,
    question_xmltree_get,
    global_and_question_xmltree_get,
    get_questionkeys_from_xml,
)

from random import shuffle, seed


import json
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser

# Suppose this is your view
from exercises.views.api import exercise_check# adjust import

rf = RequestFactory()


from course.models import Course

logger = logging.getLogger(__name__)

BIN_LENGTH = settings.BIN_LENGTH
logdir = "tmp"

#python manage.py submit_answers --subdomain nn-2024 --exercise_key '25cf1503-a5a9-4195-acdc-69bd3f5479e5' --question_key 'ai1'
#python manage.py submit_answers --subdomain chat1 --exercise_key  '0a8afa21-b5d2-4ffb-99ca-ef091d9aa3c1' --question_key 'ai25'
# http://chat1.{settings.OPENTA_SERVER}:8000/exercise/0a8afa21-b5d2-4ffb-99ca-ef091d9aa3c1/question/ai25/check
# python manage.py fix_answers --subdomain nn-2025 --exercise_key  '4a70d7a9-2322-4dfb-9e2b-c2237f7fcd8d' --question_key 'ai1'
class Command(BaseCommand):

    help = "recalculate answers"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("--exercise", default=None, type=str, help="filter by exercise")
        parser.add_argument("--subdomain",  dest="subdomain" , type=str, default="", help="filter by answerpks")
        parser.add_argument("--question_key",  dest="question_key" , type=str, default="", help="filter by answerpks")
        parser.add_argument("--exercise_key",  dest="exercise_key" , type=str, default="", help="filter by answerpks")

    def handle(self, *args, **kwargs):
        # Gather CLI args (do not override with hardcoded values)
        subdomain = (kwargs.get("subdomain") or "").strip()
        exercise_key = (kwargs.get("exercise_key") or "").strip()
        question_key = (kwargs.get("question_key") or "").strip()

        if not subdomain:
            raise CommandError("--subdomain is required (e.g., --subdomain nn-2024)")
        if not exercise_key:
            raise CommandError("--exercise_key is required")
        
        print(f"EXERCISEKEY = {exercise_key}")

        settings.DB_NAME = subdomain
        db = settings.DB_NAME
        settings.SUBDOMAIN = subdomain
        # Ensure the DB alias exists and a connection wrapper is created
        verify_or_create_database_connection(subdomain)
        try:
            exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        except Exercise.DoesNotExist:
            raise CommandError(f"Exercise with key '{exercise_key}' not found in subdomain '{subdomain}'")
        print(f"EXERCISE={exercise}")

        done_students = [];
        if question_key:
            try:
                question = Question.objects.using(db).get(exercise=exercise, question_key=question_key)
            except Question.DoesNotExist:
                raise CommandError(
                    f"Question with key '{question_key}' not found for exercise '{exercise_key}' in subdomain '{subdomain}'"
                )
            done_students = (
                Answer.objects.using(db)
                .filter(question=question)
                .values_list("user_id", flat=True)
                .distinct()
            )
            print(f"QUESTION={question}")
            print(f"STUDENTS_WITH_ANSWERS_FOR_QUESTION = {list(done_students)}")
        aggregation = Aggregation.objects.using(db).filter(exercise=exercise)
        students = aggregation.values_list("user_id", flat=True)
        students = list( set( students) - set( done_students) )
        pks = done_students
        for pk in pks:
            user = User.objects.using(db).get(pk=pk)
            username = user.username
            try :
                print(f"USER = {user}")
                aggregation = Aggregation.objects.using(db).get(user=user,exercise=exercise )
                answer = Answer.objects.using(db).get(user=user,question=question)
                grader_response = json.loads( answer.grader_response )
                grader_response['correct'] = 'true'
                grader_response['status'] = 'correct'
                grader_response['type'] = 'aibased'

                grader_response = json.dumps( grader_response )
                answer.grader_response = grader_response
                answer.correct = True
                answer.date = timezone.make_aware(datetime.datetime(2025, 9, 22))
                answer.save(update_fields=['grader_response','correct','date'])
                #print(f"RESPONSE = {grader_response}")
                course = exercise.course
                #print(f"AGGREGATION  =  {aggregation}")
                aggregation.save(using=db);
            except Exception as err :
                print(f"{type(err)} {str(err)}")
            #rf = RequestFactory()
            #r =  f"/exercise/{exercise_key}/question/{question_key}/check"
            #print(f"R = {r}")
            #req = rf.post( r, data=json.dumps({"answerData": "? Check my submission"}),
            #        content_type="application/json",
            #        # headers → must be prefixed with HTTP_
            #        HTTP_ACCEPT="application/json",
            #        HTTP_ORIGIN=f"http://{subdomain}.{settings.OPENTA_SERVER}",
            #        HTTP_REFERER=f"http://{subdomain}.{settings.OPENTA_SERVER}/",
            #        HTTP_USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/140.0.0.0 Safari/537.36",
            #        HTTP_X_CSRFTOKEN="CpVV7DIntM0JrUGHAybXS5KDhXBL64d5",
            #        HTTP_HOST=f"{subdomain}.{settings.OPENTA_SERVER}",
            #        )
            #    # Attach cookies if your code inspects them
            #req.COOKIES["csrftokenv1600"] = "CpVV7DIntM0JrUGHAybXS5KDhXBL64d5"
            #req.COOKIES["username"] =  username
            #SessionMiddleware(lambda r: None).process_request(req)
            #print(f"USERNAME = {username}")
            #req.session.save()
            #req.user = User.objects.using(db).get(username=username)
            #answer = Answer.objects.using(db).get(user=user,question__pk=pk)
            #old_response = answer.grader_response
            #print(f"RESPONSE = {answer}")
            #response = exercise_check(req, exercise=f"{exercise_key}", question=f"{question_key}")
            #if hasattr(response, "render") and callable(response.render):
            #    response = response.render()
            #print(response.status_code)




