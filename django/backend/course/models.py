import os
import logging
import datetime
import uuid
from django.core.exceptions import ValidationError

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from django.core.mail import EmailMessage, EmailMultiAlternatives
import pytz
from django.conf import settings
import exercises.paths as paths
from django.conf import settings
from django.core.mail import get_connection
from django.conf import settings
logger = logging.getLogger(__name__)
from django.contrib import messages


EMAIL_VALIDATOR = EmailValidator()


def send_email_object(email,host,username,password):
    if  hasattr(settings, 'USE_CUSTOM_SMTP_EMAIL')  or ( host and username and password ):
        with get_connection(
            host=host,
            port='587',
            username=username,
            password=password,
            use_tls=True,
        ) as connection:
            email.connection = connection
        try:
            n_sent = email.send()
            logger.info('send_email_object success' + " (" + str(n_sent) + " delivered)")
        except Exception as e:
            logger.error(str(e))
            raise e
    else:
        try:
            n_sent = email.send()
            logger.info('send_email_object success' + " (" + str(n_sent) + " delivered)")
        except Exception as e:
            logger.error('send_email_object fail' + str(e))
            raise e
    return n_sent




class Course(models.Model):
    course_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course_name = models.CharField(max_length=255,default='OpenTA')
    lti_key = models.UUIDField(unique=True, default=uuid.uuid4)
    lti_secret = models.UUIDField(unique=True, default=uuid.uuid4)
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
    difficulties  = models.CharField(max_length=512, blank=True, null=True, default='+:Recommended,*:Easy,**:Medium,***:Hard')
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
    use_email = models.BooleanField(default=False)


    def __str__(self):
        return self.course_name + ' - ' + self.course_long_name

    def get_exercises_path(self):
        return os.path.join(paths.EXERCISES_PATH, self.get_exercises_folder())

    def get_student_assets_path(self):
        return os.path.join(paths.STUDENT_ASSETS_PATH, self.get_exercises_folder())

    def get_student_asset_path(self):
        return os.path.join(paths.STUDENT_ASSETS_PATH, self.get_exercises_folder())

    def get_student_answerimages_path(self):
        return os.path.join(paths.STUDENT_ANSWERIMAGES_PATH, self.get_exercises_folder())

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


    def docheck( self ) :
        course = Course.objects.filter(pk=self.pk)
        old_value = course.values('use_email').get()['use_email']
        nocheck = True
        for field in ['email_host_user','email_reply_to','email_host_password','email_host','use_email'] :
            nocheck = nocheck and  getattr(self,field) == course.values(field).get()[field] 
            print("NOCHECK FIELD  ", field , " ", nocheck )
        check = not nocheck
        return check

        


    def clean(self):
        course = Course.objects.filter(pk=self.pk)
        body = " email_reply_to = " + str(self.email_reply_to ) + "\n email_host: " + str( self.email_host ) + "\n email_host_user: " +  str( self.email_host_user ) 
        print("BODY =  ", body )
        if self.use_email   and self.docheck()  and ( settings.EMAIL_BACKEND ==  'django.core.mail.backends.smtp.EmailBackend') :
            try:
                email_object = EmailMessage(
                    subject='EMAIL VERIFICATION TEST from ' + self.email_host  ,
                    body  = body ,
                    from_email=self.email_host_user,
                    to=[self.email_reply_to],
                    reply_to=[self.email_reply_to],
                )
                n_sent = send_email_object(email_object,self.email_host,self.email_host_user,self.email_host_password)
                assert n_sent == 1
            except Exception as e :
                 raise ValidationError({'use_email':  "PARAMETERS USED: " + body + "ERROR" + str(e) + "HINT: remember that google passwords must be of type app-password" } ,
                     code='invalid' )

    