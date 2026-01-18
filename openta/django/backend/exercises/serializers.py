# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
from django.core.exceptions import ObjectDoesNotExist
import glob
import json
import logging
from utils import db_info_var


from course.models import Course, pytztimezone
from exercises.models import (
    Answer,
    AuditExercise,
    AuditResponseFile,
    Course,
    Exercise,
    ExerciseMeta,
    ImageAnswer,
    Question,
)
from rest_framework import serializers

from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")


class ExerciseMetaSerializer(serializers.ModelSerializer):
    deadline_time = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = ExerciseMeta
        fields = "__all__"
        # fields = (
        #    'published',
        #    'deadline_date',
        #    'deadline_time',
        #    'solution',
        #    'difficulty',
        #    'required',
        #    'image',
        #    'bonus',
        #    'server_reply_time',
        #    'sort_key',
        #    'allow_pdf',
        #    'feedback',
        #    'student_assets',
        #    'locked',
        # )

    def get_thumbnail(self, obj):
        try:
            p = obj.exercise.get_full_path() + "/thumbnail*.png"
            thumbs = glob.glob(p)
            if len(thumbs) > 0:
                thumb = thumbs[-1].split("/")[-1]
            else:
                thumb = "thumbnail.png"
        except Exception as e:
            thumb = "thumbnail.png"
        return thumb

    def get_deadline_time(self, obj):
        return str(datetime.time(23, 59, 59, tzinfo=pytztimezone(settings.TIME_ZONE)))
        try:
            er = ""
            exercise = obj.exercise
            er = "0"
            course = Course.objects.using(settings.SUBDOMAIN).get(id=exercise.course_id)
            er = "a"
            if course is not None and course.deadline_time is not None:
                er = "b"
                return str(course.deadline_time)
            else:
                er = "c"
                return str(datetime.time(23, 59, 59, tzinfo=pytztimezone(settings.TIME_ZONE)))
        except Exception as e:
            logger.error(f" er = {er} GET DEADLINE TIME ERROR {type(e).__name__}")
            return str(datetime.time(23, 59, 59, tzinfo=pytztimezone(settings.TIME_ZONE)))


class ExerciseSerializer(serializers.ModelSerializer):
    meta = ExerciseMetaSerializer()
    translated_name = serializers.SerializerMethodField()
    isbonus = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = (
            "subdomain",
            "exercise_key",
            "name",
            "translated_name",
            "path",
            "folder",
            "meta",
            "deadline",
            "isbonus",
        )

    def get_translated_name(self, instance):
        """Return parsed translations for the exercise name.

        - Accepts that the model stores JSON as a string and always returns a dict.
        - If the stored value is empty/invalid, tries a lightweight repair by
          reloading from DB; if still empty, falls back to an empty dict.
        """
        raw = getattr(instance, "translated_name", "{}")

        # Fast path: already a dict
        if isinstance(raw, dict):
            return raw

        # Parse JSON string safely
        try:
            translations = json.loads(raw or "{}")
        except Exception:
            logger.warning("Invalid translated_name JSON for exercise %s", instance.exercise_key)
            translations = {}

        if translations:
            return translations

        # Attempt a best-effort refresh from DB if we have a db alias
        db = db_info_var.get(None)
        if not db:
            return {}
        try:
            exercise = Exercise.objects.using(db).get(exercise_key=instance.exercise_key)
            # If metadata wasn’t populated, try to ensure it exists from disk
            #try:
            #    path = exercise.get_full_path()
            #    dbcourse = exercise.course
            #    Exercise.objects.add_exercise_full_path(path, dbcourse, db)
            #    # Re-fetch and parse again
            #    exercise = Exercise.objects.using(db).get(exercise_key=instance.exercise_key)
            #    refreshed = exercise.translated_name
            #    translations = json.loads(refreshed or "{}") if isinstance(refreshed, str) else (refreshed or {})
            #except Exception:
            #    # If refresh fails, just fall back to empty
            #    translations = {}
        except Exception:
            translations = {}

        return translations

    def get_isbonus(self, instance):
        try:
            meta = instance.meta
        except ObjectDoesNotExist:
            return 'optiona'
        except Exception as e:
            logger.error(f"ISBONUS ERROR1 error={type(e).__name__} self={self} instance={instance} ")
            return 'optional'
        try :
            if meta.bonus:
                ret = "bonus"
                return ret
            elif meta.required:
                ret = "required"
                return ret
            else:
                ret = "optional"
                return ret
        except Exception as e :
            logger.error(f"ISBONUS ERROR2 error={type(e).__name__} self={self} instance={instance} ")
            return "optional"

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("exercise", "question_id")


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ("user", "question", "answer", "grader_response", "correct", "date")


class ImageAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAnswer
        fields = ("user", "exercise", "pk", "date", "filetype")


class AuditResponseFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditResponseFile
        fields = "__all__"


class AuditExerciseSerializer(serializers.ModelSerializer):
    student_username = serializers.SerializerMethodField()
    auditor_data = UserSerializer(source="auditor", read_only=True)
    responsefiles = AuditResponseFileSerializer(many=True)

    class Meta:
        model = AuditExercise
        fields = (
            "pk",
            "student",
            "auditor",
            "auditor_data",
            "exercise",
            "date",
            "message",
            "subject",
            "sent",
            "published",
            "force_passed",
            "student_username",
            "responsefiles",
            "revision_needed",
            "updated",
            "updated_date",
            "modified",
            "points",
            #"questionlist_is_empty",
        )

    def update(self, instance, validated_data):
        instance.points = validated_data.get("points", instance.points)
        instance.message = validated_data.get("message", instance.message)
        instance.subject = validated_data.get("subject", instance.subject)
        instance.published = validated_data.get("published", instance.published)
        instance.updated = validated_data.get("updated", instance.updated)
        instance.revision_needed = validated_data.get("revision_needed", instance.revision_needed)
        instance.force_passed = validated_data.get("force_passed", instance.force_passed)
        instance.auditor = validated_data.get("auditor", instance.auditor)
        #instance.questionlist_is_empty = validated_data.get("questionlist_is_empty", instance.questionlist_is_empty)
        instance.save()
        return instance

    def get_student_username(self, instance):
        try:
            student_name = str(instance.student.pk)
            if hasattr(instance.student, "username"):
                student_name = instance.student.username
        except Exception as e:
            msg = f"ERROR E9900915 {type(e).__name__}  GET USERNAME BROKEN {settings.SUBDOMAIN} "
            logger.error(msg)
            student_name = "ERROR-E990915"
        return student_name
