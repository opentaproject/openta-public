from django.db import models
from django.utils.translation import ugettext_lazy as _
import datetime
import pytz


class CourseManager(models.Manager):
    def course_name(self):
        course = self.first()
        if course is not None:
            return course.course_name
        else:
            return "OpenTA"

    def course_url(self):
        course = self.first()
        if course is not None:
            return course.url
        else:
            return ""

    def deadline_time(self):
        course = self.first()
        if course is not None and course.deadline_time is not None:
            return course.deadline_time
        else:
            return datetime.time(23, 59, 0, tzinfo=pytz.timezone('Europe/Stockholm'))

    def registration_domains(self):
        course = self.first()
        if course is not None and course.registration_domains is not None:
            return list(map(lambda s: s.strip(), course.registration_domains.split(',')))
        else:
            return None


class Course(models.Model):
    course_name = models.CharField(max_length=255)
    course_long_name = models.CharField(max_length=255, default='')
    registration_password = models.CharField(
        _('Registration password'), max_length=255, null=True, default=None, blank=True
    )
    registration_by_password = models.BooleanField(default=False, blank=True)
    deadline_time = models.TimeField(null=True, default=None, blank=True)
    url = models.CharField(max_length=255, blank=True, null=True, default=None)
    registration_domains = models.CharField(max_length=255, blank=True, null=True, default=None)
    registration_by_domain = models.BooleanField(default=False, blank=True)
    languages = models.CharField(max_length=255, blank=True, null=True, default=None)
    objects = CourseManager()

    def __str__(self):
        return self.course_name + ' - ' + self.course_long_name
