from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import ugettext as _
import datetime
import pytz
from django.utils import timezone


class CourseManager(models.Manager):
    def course_name(self):
        course = self.first()
        if course is not None:
            return course.course_name
        else:
            return "OpenTA"

    def deadline_time(self):
        course = self.first()
        if course is not None:
            return course.deadline_time
        else:
            return datetime.time(23, 59, 0, tzinfo=pytz.timezone('Europe/Stockholm'))


class Course(models.Model):
    course_name = models.CharField(max_length=255)
    course_long_name = models.CharField(max_length=255, default='')
    registration_password = models.CharField(
        _('Registration password'), max_length=255, null=True, default=None, blank=True
    )
    registration_by_password = models.BooleanField(default=False, blank=True)
    deadline_time = models.TimeField(null=True, default=None, blank=True)
    objects = CourseManager()

    def __str__(self):
        return self.course_name + ' - ' + self.course_long_name
