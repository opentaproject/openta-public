# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib.auth.models import User
from rest_framework import serializers
from django.conf import settings
import datetime
from dateutil import tz
from datetime import datetime
from exercises.models import Exercise
from exercises.serializers import ExerciseMetaSerializer

from aggregation.models import Aggregation


class AggregationSerializer(serializers.ModelSerializer):
    date_complete = serializers.SerializerMethodField()
    answer_date = serializers.SerializerMethodField()
    cat = serializers.SerializerMethodField()

    class Meta:
        model = Aggregation
        # fields = '__all__'
        fields = [
            "course",
            "user",
            "exercise",
            "cat",
            "points",
            "user_tried_all",
            "user_is_correct",
            "correct_by_deadline",
            "answer_date",
            "attempt_count",
            'questionlist_is_empty',
            "all_complete",
            "date_complete",
            "complete_by_deadline",
            "audit_published",
            "audit_needs_attention",
            "image_exists",
            "image_by_deadline",
            "force_passed",
            "force_failed",
        ]

    def get_date_complete(self, obj):
        to_zone = tz.gettz(settings.TIME_ZONE)
        # t  = ( obj.date_complete.replace(tzinfo=to_zone) ).astimezone().isoformat()
        if obj.date_complete:
            t = (obj.date_complete).astimezone().isoformat()
        else:
            t = "X"
        return str(t)

    def get_cat(self, obj):
        cat = obj.bonus()
        return cat

    def get_answer_date(self, obj):
        to_zone = tz.gettz(settings.TIME_ZONE)
        if obj.answer_date:
            t = (obj.answer_date).astimezone().isoformat()
        else:
            t = "X"
        # t =  ( obj.answer_date.replace(tzinfo=to_zone)  ).astimezone().isoformat()
        return str(t)
        #    return datetime.time(23, 59, 59, tzinfo=pytztimezone(settings.TIME_ZONE))
