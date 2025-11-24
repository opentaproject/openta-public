# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os

from django.conf import settings
import sys

TEMPLATE_EXERCISE_PATH = "../../exercise_templates"
TRASH_PATH = "z:Trash"
STUDENT_ASSETS_PATH = settings.VOLUME + "/" + settings.SUBDOMAIN + "/media/studentassets"
STUDENT_ANSWERIMAGES_PATH = settings.VOLUME + "/" + settings.SUBDOMAIN + "/media/answerimages"
EXERCISE_XML = "exercise.xml"
EXERCISE_XSD = "./exercises/exercise.xsd"
EXERCISES_PATH = settings.VOLUME + "/" + settings.SUBDOMAIN + "/exercises"
DEFAULT_TRANSLATION_DICT_XML = "translations/translationdict.xml"
EXERCISE_KEY = "exercisekey"
EXERCISE_HISTORY = "history"
EXERCISE_THUMBNAIL = "thumbnail.png"


def dynamic_exercises_path():
    return settings.VOLUME + "/" + settings.SUBDOMAIN + "/exercises"


def _subpath(**kwargs):
    caller = sys._getframe().f_back.f_code.co_name
    return ""


def get_student_asset_path(user, exercise):
    subdomain = settings.SUBDOMAIN
    course_key = exercise.course.course_key
    if not settings.RUNTESTS:
        multipath = settings.VOLUME + "/" + subdomain+ "/media/studentassets"
    else:
        multipath = settings.VOLUME + "/" + "openta" + "/media/studentassets"
    return os.path.join(multipath, str(course_key), user.username, exercise.pk)


def get_exercise_asset_path(user, exercise):
    exercise.course.course_key
    return exercise.get_full_path()
