# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from datetime import time, tzinfo
from course.models import Course, pytztimezone,tzlocalize
from django.conf import settings
import datetime

tz = pytztimezone(settings.TIME_ZONE)


def before_deadline(course, date_time, deadline_date):
    deadline_time = time(hour=23, minute=59, second=59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    deadline_tz_date = tzlocalize(datetime.datetime.combine(deadline_date, deadline_time))
    return date_time < deadline_tz_date
