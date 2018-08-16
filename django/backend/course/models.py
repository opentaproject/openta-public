import os
import datetime
import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
import pytz
from django.conf import settings
import exercises.paths as paths


EMAIL_VALIDATOR = EmailValidator()


class Course(models.Model):
    course_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course_name = models.CharField(max_length=255)
    icon = models.ImageField(default=None, null=True, blank=True, upload_to='public')
    motd = models.CharField(max_length=1024, default='', blank=True)
    course_long_name = models.CharField(max_length=255, default='')
    registration_password = models.CharField(
        verbose_name='Registration password', max_length=255, null=True, default=None, blank=True
    )
    registration_by_password = models.BooleanField(default=False, blank=True)
    deadline_time = models.TimeField(null=True, default=None, blank=True)
    url = models.CharField(max_length=255, blank=True, null=True, default=None)
    registration_domains = models.CharField(max_length=255, blank=True, null=True, default=None)
    registration_by_domain = models.BooleanField(default=False, blank=True)
    languages = models.CharField(max_length=255, blank=True, null=True, default=None)
    email_reply_to = models.CharField(
        max_length=255, blank=True, null=True, default="", validators=[EMAIL_VALIDATOR]
    )
    email_host = models.CharField(
        max_length=255, blank=True, null=True, default=settings.EMAIL_HOST
    )
    email_host_user = models.CharField(
        max_length=255, blank=True, null=True, default=settings.EMAIL_HOST_USER
    )
    email_host_password = models.CharField(
        max_length=255, blank=True, null=True, default=settings.EMAIL_HOST_PASSWORD
    )
    published = models.BooleanField(default=False)
    owners = models.ManyToManyField(User, limit_choices_to={'is_staff': True})
    use_auto_translation = models.BooleanField(default=False)

    def __str__(self):
        return self.course_name + ' - ' + self.course_long_name

    def get_exercises_path(self):
        return os.path.join(paths.EXERCISES_PATH, self.get_exercises_folder())

    def get_exercises_folder(self):
        return str(self.course_key)

    def get_registration_domains(self):
        if self.registration_domains is not None:
            return list(map(lambda s: s.strip(), self.registration_domains.split(',')))
        else:
            return None

    def get_deadline_time(self):
        if self.deadline_time is not None:
            return self.deadline_time
        else:
            return datetime.time(23, 59, 0, tzinfo=pytz.timezone(settings.TIME_ZONE))

    def get_languages(self):
        if self.languages is not None:
            return list(map(str.strip, self.languages.split(',')))
        else:
            return None
