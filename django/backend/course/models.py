import os
import uuid
from django.core.management import call_command
import logging
import datetime
import uuid
from django.core.exceptions import ValidationError
from opentasites.models import OpenTASite
from django.contrib import admin
from django import forms
import re


from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from django.core.mail import EmailMessage, EmailMultiAlternatives
import pytz
from django.conf import settings
import exercises.paths as paths
from django.conf import settings
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
import tempfile
import io, json
from django.core.validators import RegexValidator


from django.core.mail import get_connection
from django.conf import settings

logger = logging.getLogger(__name__)
from django.contrib import messages


EMAIL_VALIDATOR = EmailValidator()

def patch_credential_string(value):
    return value.strip().lstrip('r').strip("'")



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




def patch_credential_string(value):
    return value.strip().lstrip('r').strip("'")

def send_email_object(email, host, username, password):
    if hasattr(settings, 'USE_CUSTOM_SMTP_EMAIL') or (host and username and password):
        with get_connection(
            host=host, port='587', username=username, password=password, use_tls=True
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

alphanumeric = RegexValidator(r'^[0-9a-z]*$', 'Only lowercase and numbers allowed.')



class Course(models.Model):
    opentasite = models.CharField(max_length=255,default='')
    course_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    course_name = models.CharField(max_length=255, default='OpenTA')
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
    difficulties = models.CharField(
        max_length=512, blank=True, null=True, default='+:Recommended,*:Easy,**:Medium,***:Hard'
    )
    email_reply_to = models.CharField(
        max_length=255, blank=True, null=True, default="", validators=[EMAIL_VALIDATOR]
    )
    email_host = models.CharField(
        max_length=255, blank=True, null=True, default=settings.EMAIL_HOST
    )
    email_host_user = models.CharField(
        max_length=255, blank=True, null=True, default=settings.EMAIL_HOST_USER
    )
    email_username = models.CharField(
        max_length=255, blank=True, null=True, default=settings.EMAIL_HOST_USER
    )
    #
    # TODO  https://pypi.org/project/django-encrypted-model-fields/
    #
    email_host_password = models.CharField(
        max_length=255, blank=True, null=True, default=settings.EMAIL_HOST_PASSWORD
    )
    published = models.BooleanField(default=False)
    owners = models.ManyToManyField(User, limit_choices_to={'is_staff': True})
    use_email = models.BooleanField(default=False)
    use_auto_translation = models.BooleanField( default=False )
    google_auth_string = models.CharField(max_length=4096,blank=True,default='' ) #, validators=[validate_google_auth_string] )


    def save(self, *args, **kwargs):
        subdomain = str(self.opentasite)
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        logger.info("SAVE COURSE SUBDOMAIN = %s  " %  settings.SUBDOMAIN)
        logger.info("ARGS  = %s " % str( args ) )
        logger.info("DB_NAME = %s " %  settings.DB_NAME)
        logger.info("OPENTSITE = %s " %  str( self.opentasite ) )
        f = open(settings.VOLUME + '/' + subdomain + '/dbname.txt' )
        db_name = f.read();
        db_name = re.sub(r"\W", "", db_name)
        f.close()
        logger.info("DB_NAME = %s " % db_name ) 
        opentasite_obj ,_ =  OpenTASite.objects.get_or_create(subdomain=subdomain, db_name=db_name)
        #self.subdomain =  opentasite
        #opentasite.db_name = db_name
        opentasite_obj.save()
        self.opentasite = subdomain
        super().save(*args, **kwargs)  # Call the "real" save() method.
        try :
            defaultuser = User.objects.get_or_create(username='student')
            #opentauser = OpenTAUser.objects.get_or_create(user=defaultuser)
            defaultuser.opentauser.courses.add(self)
        except:
            pass
        #dump_path = paths.EXERCISES_PATH + '/' + str(self.course_key) + ".json" 
        #output = open(dump_path,'w') # Point stdout at a file for dumping data to.
        #call_command('dumpdata','course',format='json',indent=3,stdout=output)
        #output.close()        

    def clean(self):
        if self.use_auto_translation  and self.google_auth_string == '':
            raise ValidationError( {'use_auto_translation': _('Auto translation cannot be enabled with a blank Google auth string.') } ,
                     code='invalid')
        if self.use_auto_translation and ( self.languages == ''  or self.languages == None ) :
            raise ValidationError( {'use_auto_translation': _('Auto translation can only be enabled if Languages is nonempty.') } ,
                     code='invalid')

        if not ( self.google_auth_string.strip()  == ''   ) :
            try:
                 
                 #print("VALUE = ", value)
                 value = self.google_auth_string;
                 credentialstring = patch_credential_string(value)
                 service_account_info = json.load(io.StringIO(credentialstring))
                 credentials = service_account.Credentials.from_service_account_info( service_account_info)
                 translate_client = translate.Client( credentials=credentials)
                 should_be_en = translate_client.detect_language( 'This is a statement in english')['language'] 
                 print("SHOULD BE = ", should_be_en)
                 assert 'en' == should_be_en 
            except :
                 raise ValidationError({'google_auth_string': _('Google Auth string does not pass validation. Set it to blank to avoid error. ') } ,
                     code='invalid' )


    use_email = models.BooleanField(default=False, blank=True)
    use_lti = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.course_name + ' - ' + self.course_long_name

    def get_exercises_path(self):
        res= settings.VOLUME + '/' + str( self.opentasite) +  '/exercises' + '/' + self.get_exercises_folder()  
        #logger.info("COURSE_GET_EXERRCISES_PATH = RETURN %s " % res )
        #logger.info("COURSE_GET_EXERRCISES_PATH = FOLDER %s " % self.get_exercises_folder() )
        return str( res )

    #def get_student_assets_path(self):
    #    return os.path.join(paths.STUDENT_ASSETS_PATH, self.get_exercises_folder())

    #def get_student_asset_path(self):
    #    return os.path.join(paths.STUDENT_ASSETS_PATH, self.get_exercises_folder())

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

    def docheck(self):
        return True
        course = Course.objects.filter(pk=self.pk)
        old_value = course.values('use_email').get()['use_email']
        nochange = True
        for field in [
            'email_username',
            'email_host_user',
            'email_reply_to',
            'email_host_password',
            'email_host',
            'use_email',
        ]:
            nochange = nochange and getattr(self, field) == course.values(field).get()[field]
            print("NOCHECK FIELD  ", field, " ", nochange)
        check = not nochange
        print("CHECK = ", check)
        return check

    def clean(self):
        course = Course.objects.filter(pk=self.pk)
        body = (
            " email_reply_to = "
            + str(self.email_reply_to)
            + "\n email_host: "
            + str(self.email_host)
            + "\n email_host_user: "
            + str(self.email_host_user)
        )
        body = body + "\n email_username: " + str(self.email_username)
        print("BODY =  ", body)
        if self.docheck() and  self.use_email and (
            settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
        ):
            try:
                email_object = EmailMessage(
                    subject='EMAIL VERIFICATION TEST from ' + self.email_host,
                    body=body,
                    from_email=self.email_host_user,
                    to=[self.email_reply_to],
                    reply_to=[self.email_reply_to],
                )
                n_sent = send_email_object(
                    email_object, self.email_host, self.email_username, self.email_host_password
                )
                assert n_sent == 1
            except Exception as e:
                raise ValidationError(
                    {
                        'use_email': "PARAMETERS USED: "
                        + body
                        + "  ERROR"
                        + str(e)
                        + " HINT: remember that google passwords must be of type app-password"
                    },
                    code='invalid',
                )

