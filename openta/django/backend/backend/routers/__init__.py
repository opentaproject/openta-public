# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings
import time
from aggregation.models import Aggregation

from course.models import Course
from django.contrib.auth.models import Group, User
from exercises.models import Answer, AuditExercise, ImageAnswer, Question, Answer, ExerciseMeta, Exercise
from django.contrib.sessions.models import Session
from users.models import OpenTAUser
import logging
import sys
from utils import db_info_var, user_info_var


logger = logging.getLogger(__name__)


# change opentasites in settings.py
# reinitialize database opentasites
# migrate opentasites


default_models = ["django_cache", "workqueue", "sites"]
site_models = ["opentasites"]


class AuthRouter:
    """A router to control all database cache operations; see CacheRouter in djangoproject """

    def db_for_read(self, model, **hints):
        db = db_info_var.get(None)
        if settings.RUNTESTS or model._meta.app_label in default_models:
            return "default"
        elif model._meta.app_label in site_models:
            return "opentasites"
        settings.DB_NAME = db
        return db

    def db_for_write(self, model, **hints):
        db = db_info_var.get(None)
        if settings.RUNTESTS or model._meta.app_label in default_models:
            return "default"
        elif model._meta.app_label in site_models:
            return "opentasites"
        settings.DB_NAME = db 
        return db

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        "Only install the cache model on primary"
        if settings.RUNTESTS or app_label == "django_cache":
            return db == "default"
        return True

    def allow_relation(self, obj1, obj2, **hints):
        return True


