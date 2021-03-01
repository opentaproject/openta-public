"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from opentasites.models import OpenTASite
from course.models import Course
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        print("SETTINGS SUBDOMAIN = %s " % settings.SUBDOMAIN)
        for opentasite in OpenTASite.objects.all():
            print("SUBDOMAIN = %s %s %s " % ( opentasite.subdomain, opentasite.db_name, opentasite.db_label ) )
            opentasite.subdomain = settings.SUBDOMAIN
            opentasite.db_label = 'moved from ' + opentasite.db_label 
            opentasite.save()
        for course in Course.objects.all() :
            course.opentasite = settings.SUBDOMAIN
            course.save

