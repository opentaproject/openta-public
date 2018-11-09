import pytz
import datetime
from course.models import Course
from django.conf import settings

tz = pytz.timezone(settings.TIME_ZONE)


def before_deadline(course, date_time, deadline_date):
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    deadline_tz_date = tz.localize(datetime.datetime.combine(deadline_date, deadline_time))
    return date_time < deadline_tz_date
