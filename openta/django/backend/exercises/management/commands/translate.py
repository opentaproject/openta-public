# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import glob
import re
import time
import sys, traceback
import ast
from translations.views import exercise_translate_raw
from backend.middleware import verify_or_create_database_connection, create_connection
from exercises.question import _question_check, get_usermacros
from exercises.models import Exercise, Answer, Question
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
from django.core.cache import caches



from course.models import Course

logger = logging.getLogger(__name__)

BIN_LENGTH = settings.BIN_LENGTH
logdir = "tmp"


class Command(BaseCommand):

    help = "recalculate answers"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("--exercise", default=None, type=str, help="Name of exercise")
        parser.add_argument("--subdomain",  dest="subdomain" , type=str, default="", help="subdomain")
        parser.add_argument("--action",  dest="action" , type=str, default="", help='translate,remove,changedefaultlanguage')
        parser.add_argument("--language",  dest="language" , type=str, default="en", help='language, en,sv,no ')

    def handle(self, *args, **kwargs):
        subdomain = kwargs.get("subdomain")
        action = kwargs.get("action")
        language = kwargs.get("language")
        verify_or_create_database_connection(subdomain)
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        create_connection(subdomain)
        verify_or_create_database_connection( subdomain )
        results_directory = f"/tmp/{settings.SUBDOMAIN}/translate"
        # print("KWARGS = ", kwargs)
        exercise = kwargs.get("exercise",None)
        dbexercises = Exercise.objects.using(subdomain).all()
        caches['default'].set("temporarily_block_translations",False)
        if exercise :
            dbexercises = dbexercises.filter(name=exercise)
        for dbexercise in dbexercises :
            print(f"NAME={dbexercise.name} {language} {action} ")
            res = exercise_translate_raw(subdomain,dbexercise,language,'translate')
            res = exercise_translate_raw(subdomain,dbexercise,language,'changedefaultlanguage')
            res = exercise_translate_raw(subdomain,dbexercise,'all','remove')
            print(f"RES = {res}")
