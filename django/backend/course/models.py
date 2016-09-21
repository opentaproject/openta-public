from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import ugettext as _


class Course(models.Model):
    course_name = models.CharField(max_length=255)
    registration_password = models.CharField(
        _('Registration password'), max_length=255, null=True, default=None, blank=True
    )
    registration_by_password = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.course_name
