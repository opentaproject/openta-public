"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from course.models import Course


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        for course in Course.objects.all():
            print("{pk}: {name}".format(pk=course.pk, name=course.course_name))
