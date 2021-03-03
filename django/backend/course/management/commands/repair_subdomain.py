"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from opentasites.models import OpenTASite
from course.models import Course
from django.conf import settings
import re


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """Remove name and surname from users."""
        print("SETTINGS SUBDOMAIN = %s " % settings.SUBDOMAIN)
        opentasites = []
        #try: 
        #    opentasites =  OpenTASite.objects.all()
        #except:
        f = open(settings.VOLUME + '/' + settings.SUBDOMAIN + '/dbname.txt' )
        db_name = f.read();
        db_name = re.sub(r"\W", "", db_name)
        f.close()
        opentasite, _ = OpenTASite.objects.get_or_create( subdomain=settings.SUBDOMAIN , db_name=db_name )
        #    print("OPENTASITES DID NOT EXIST")
        #    pass
        opentasite.subdomain = settings.SUBDOMAIN
        opentasite.db_label = 'moved from ' + opentasite.db_label 
        opentasite.save()
        print("SUBDOMAIN = %s %s %s %s " % ( opentasite.id, opentasite.subdomain, opentasite.db_name, opentasite.db_label ) )
        opentasite.save()
        print("OPENTASITES = %s " % opentasites)
        opentasite = OpenTASite(subdomain=settings.SUBDOMAIN, db_name=settings.DB_NAME, db_label=settings.SUBDOMAIN)
        opentasite.save()
        courses = Course.objects.all()
        print("COURSES = %s " % len( courses) )
        for course in courses :
            print("SETTINGS SUBDOMAIN = %s for course %s  " % ( settings.SUBDOMAIN,  settings.SUBDOMAIN) )
            course.opentasite = settings.SUBDOMAIN
            course.save()

