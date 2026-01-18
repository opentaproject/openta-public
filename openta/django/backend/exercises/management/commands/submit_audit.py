# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import glob
import re
import time
import sys, traceback
import ast
from backend.middleware import verify_or_create_database_connection, create_connection
from exercises.question import _question_check, get_usermacros
from exercises.models import Exercise, Answer, Question, AuditExercise
from aggregation.models import Aggregation
from django.contrib.auth.models import User
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
class Command(BaseCommand):

    help = "resave audits"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("--subdomain",  dest="subdomain" , type=str, default="", help="filter by answerpks")
        parser.add_argument("--exercise_key",  dest="exercise_key" , type=str, default="", help="filter by answerpks")

    def handle(self, *args, **kwargs):
        # Gather CLI args (do not override with hardcoded values)
        subdomain = (kwargs.get("subdomain") or "").strip()
        exercise_key = (kwargs.get("exercise_key") or "").strip()

        if not subdomain:
            raise CommandError("--subdomain is required (e.g., --subdomain nn-2024)")
        if not exercise_key:
            raise CommandError("--exercise_key is required")
        
        settings.DB_NAME = subdomain
        db = settings.DB_NAME
        settings.SUBDOMAIN = subdomain
        # Ensure the DB alias exists and a connection wrapper is created
        verify_or_create_database_connection(subdomain)
        print(f"EXERCISE_KEY = {exercise_key}")
        exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        print(f"EXERCISE = {exercise}")
        audits = []
        audits = AuditExercise.objects.using(db).filter(exercise=exercise).all()
        for audit in audits:
            student = audit.student;
            if not audit.points :
                audit.save(update_fields=['points'] );
                print(f"NEW POINT ASSIGNMENT {student} was assigned {audit.points}")
            else :
                print(f"OLD POINT ASSIGNMENT {student} already had points {audit.points}")




