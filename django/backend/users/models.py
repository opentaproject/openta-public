from django.db import models

from django.contrib.auth.models import User

from course.models import Course


class OpenTAUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)
