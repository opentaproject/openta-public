# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from exercises.models import Exercise, ExerciseMeta
from rest_framework.decorators import api_view
from utils import get_subdomain_and_db

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic.edit import UpdateView
import logging

logger = logging.getLogger(__name__)




class ExerciseMetaUpdate(UpdateView):
    model = ExerciseMeta
    fields = [
        "deadline_date",
        "solution",
        "difficulty",
        "required",
        "bonus",
        "image",
        "allow_pdf",
        "published",
        "sort_key",
        "feedback",
        "student_assets",
        "locked",
        "allow_ai",
    ]

    def get_object(self, queryset=None):
        request = self.request
        (subdomain, db) = get_subdomain_and_db(request)
        obj = self.model.objects.using(db).get(pk=self.kwargs["pk"])
        if "difficulties" in self.kwargs:
            fields = obj._meta.fields
            difficulty = list(filter(lambda x: str(x.attname) == "difficulty", fields))[0]
            difficulty.choices = self.kwargs["difficulties"]
        obj.fullpath = self.kwargs.get("fullpath")
        cache = caches["aggregation"]
        exercise = Exercise.objects.using(db).get(exercise_key=self.kwargs["exercise"])
        course = exercise.course
        subdomain = course.opentasite
        course_key = course.course_key
        cache.delete_pattern(f"*{subdomain}*")
        cache.delete_pattern(f"*{course_key}*")
        return obj

    model = ExerciseMeta

    def get_success_url(self, **kwargs):
        logger.info(f'GET SUCCESS_URL')
        _, db = get_subdomain_and_db(self.request)
        obj = self.model.objects.using(db).get(pk=self.kwargs["pk"])
        old_meta = self.kwargs["old_meta"]
        for exerciseKey in self.kwargs["exercisekeys"]:
            exercise = Exercise.objects.using(db).get(exercise_key=exerciseKey)
            meta = ExerciseMeta.objects.using(db).get(exercise=exercise)
            for field in self.fields:  # ONLY MAP CHANGED FIELDS IN BULK
                if not field in ["sort_key", "difficulty"]:
                    if not getattr(old_meta, field) == getattr(obj, field):
                        setattr(meta, field, getattr(obj, field))
            meta.save(using=db)
        return "/exercise/" + self.kwargs["exercise"] + "/editmeta"


def split_or_repeat(txt):
    txt = txt.strip("\r\n")
    pieces = txt.split(":")
    if len(pieces) < 2:
        pieces = [txt, txt]
    return tuple(pieces)


def split_or_repeat(txt):
    txt = txt.strip("\r\n")
    pieces = txt.split(":")
    if len(pieces) < 2:
        pieces = [txt, txt]
    return tuple(pieces)


@api_view(["POST", "GET"])
@xframe_options_exempt
@permission_required("exercises.administer_exercise")
def ExerciseMetaUpdateView(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    #exercisekeys = request.session.get("selectedExercises", [])
    # dbexercise = Exercise.objects.using(db).select_related('meta').get(exercise_key=exercise)
    method = request.method
    try:
        meta, created = (
            ExerciseMeta.objects.using(db)
            .select_related("exercise", "exercise__course", "exercise__course")
            .get_or_create(exercise__exercise_key=exercise)
        )
        dbexercise = meta.exercise
        metaid = meta.id
        allow_ai = meta.allow_ai
    except ObjectDoesNotExist as e:
        messages.add_message(
            request,
            messages.ERROR,
            "Meta could not be updated. Try again; if necessary log out and in again. If this does not solve the problem make a bug report. ",
        )
        return render(request, "base_failed.html")

    try:
        difficultieslist = meta.exercise.course.difficulties.split(",")
        difficulties = tuple(split_or_repeat(str(v)) for v in difficultieslist)
    except Exception as e:
        logger.error(f"EXERCISEMETAUPDATEVIEW {type(e).__name__}")
        difficulties = None
    # difficulties = tuple( {('B' + v, v) for k,v in enumerate( difficultieslist ) })
    fullpath = request.get_full_path()
    uri = request.build_absolute_uri()
    result = ExerciseMetaUpdate.as_view()(
        request,
        pk=metaid,
        exercise=exercise,
        difficulties=difficulties,
        exercisekeys=exercisekeys,
        old_meta=meta,
        fullpath=fullpath,
        allow_ai=allow_ai,
    )
    if request.method == 'POST' :
        result.set_cookie("submitted", "true")
    return result
