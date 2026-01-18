# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from selenium import webdriver
from django.core.mail import get_connection
from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.core.mail import send_mass_mail
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib import messages
from django.conf import settings
import pathlib
import shutil
from django.contrib.auth import update_session_auth_hash
import os
from django.core.cache import cache, caches
from zoneinfo import ZoneInfo
from datetime import datetime
from contextvars import ContextVar
db_info_var = ContextVar('db_info',default=None)
user_info_var = ContextVar('user_info',default=None)



from course.models import Course

logger = logging.getLogger(__name__)

#def pytztimezone( t ):
#    tz = ZoneInfo( settings.TIME_ZONE)
#    return tz


def get_subdomain(request):
    subdomain,db = get_subdomain_and_db(request);
    return subdomain;

def get_subdomain_and_db_and_user(request):
    if settings.RUNTESTS :
        return ( 'openta','default',request.user)
    (subdomain,db) = get_subdomain_and_db(request)
    if hasattr( request, 'user' ):
        user = request.user
    else :
        if hasattr( request, 'session' ) :
            username = request.session.get('username',user_info_var.get(None) )
        else :
            username = user_info_var.get(None) 
        user = None
        try :
            from exercises.models import User
            user = User.objects.using(db).get(username=username)
        except ObjectDoesNotExist :
            user = None

    return ( subdomain, db, user )


def get_subdomain_and_db(request):
    if settings.RUNTESTS :
            return('openta','default')
    db = None; db_ = None; subdomain = None;
    try :
        if hasattr(request, 'session' ):
            return ( request.session.get('subdomain',db_info_var.get(None) ) , request.session.get('db', db_info_var.get(None) ) )
        db_ = db_info_var.get(None) 
        if db_ == None :
            return get_subdomain_and_db_( request)
        else :
            (db,subdomain) =  get_subdomain_and_db_( request)
            assert (db_,db_) ==  (db,subdomain) , f"XXX CONTEXT db_={db_} not consistent with {db,subdomain}"
            if not db_ :
                db_info_var.set(db_)
                return (db_,db_)
            else :
                logger.error(f"XXX DB = None in get_subdomain_and_db")
    except Exception as e :
        logger.error(f"XXX ERROR IN CONTEXT FOR SUBDOMAIN db={db}, db_={db_}")
        return (subdomain,db)


def get_subdomain_and_db_(request):
    # print(f"SESSION = {request.session.session_key}")
    if settings.RUNTESTS:
        return ("openta", "default")
    subdomain = None
    subdomain2 = None
    try:
        #print(f"USER = {request.user}")
        subdomain2 = request.build_absolute_uri().split('/')[2].split('.')[0]
        subdomain = request.META["HTTP_HOST"].split(".")[0].split(":")[0]
        if not subdomain == subdomain2  and subdomain2 :  # THIS SEEMS NEVER TO BE TRIGGERED
            logger.error(f"XXX SUBDOMAIN = {subdomain} and SUBDOMAIN2={subdomain2}")
            settings.SUBDOMAIN = subdomain2
            settings.DB_NAME = subdomain2
            #username = str( request.user )
            #caches['default'].set(username,subdomain)
            #return (subdomain, subdomain)

    except Exception as e:
        if subdomain2 :
            logger.error(f"XXX GET_SUBDOMAIN_AND_DB_ERROR {str(e)} SUBDOMAIN2={subdomain2} and user={request.user}")
            settings.SUBDOMAIN = subdomain2
            settings.DB = subdomain2
            subdomain = subdomain2
        else :
            subdomain = settings.SUBDOMAIN
    if subdomain  == None or subdomain == '' :
        logger.error(f" XXX SUBDOMAIN IN GET_SUBDOMAIN_AND_DB = {subdomain}")
    db_info_var.set(subdomain)
    return (subdomain,subdomain)







def touch_(subdomain=settings.SUBDOMAIN):
    if settings.MULTICOURSE:
        fname = os.path.join("/%s/" % settings.VOLUME, subdomain, "touchfile")
        if os.path.exists(fname):
            os.utime(fname, None)
        else:
            open(fname, "a").close()


def send_email_object(email):
    print(f"EMAIL = {email}")
    ret = send_email_objects([email])
    return ret

#def send_mass_mail_task( datatuple , auth_user, auth_password) :
#     task_id = workqueue.enqueue_task(
#        "student_results",
#        
#        course=dbcourse,
#        subdomain=subdomain,
#        username='super',
#        )
#
#
#
#
#    logger.error(f"SEND_MASS_EMAIL")
#    send_mass_mail( datatuple, auth_user=auth_user , auth_password=auth_password)
#    logger.error(f"SEN_MASS_EMAIL DONE")

def send_email_objects(emails):
    logger.error(f"SEND_EMAIL_OBJECTS WITH QUEUE {emails} ")
    from workqueue.models import QueueTask
    import workqueue.util as workqueue
    from workqueue.exceptions import WorkQueueError
    dbcourse = Course.objects.first()
    subdomain = dbcourse.opentasite
    n = len( emails )
    task_id = workqueue.enqueue_task(
            "send_emails",
            send_email_objects_,
            emails=emails
    )
    return ( task_id , n )



def send_email_objects_(task, emails):
    print(f" USE_GMAIL = {settings.USE_GMAIL}")
    n_sent = 0
    if True :
        email_host = settings.EMAIL_HOST
        email_host_password = settings.EMAIL_HOST_PASSWORD
        email_host_user = settings.EMAIL_HOST_USER
        email_username = settings.EMAIL_HOST_USER
        email_host_reply_to = settings.EMAIL_REPLY_TO
        n_sent = 0
        email_host = settings.EMAIL_HOST
        email_host_password = settings.EMAIL_HOST_PASSWORD
        email_host_user = settings.EMAIL_HOST_USER
        email_username = settings.EMAIL_HOST_USER
        email_host_reply_to = settings.EMAIL_HOST_USER
        tt = []
        for email in emails :
            if not email == None :
                t = ( email.subject, email.body,email.from_email, email.to)
                tt = tt + [t]
        emails_tuple = tuple( tt )
        print(f"T = {emails_tuple}")
        n = 0
        send_mass_mail( emails_tuple, auth_user=email_host_user, auth_password=email_host_password)
        #connection = get_connection(
        #    host=email_host,
        #    port="587",
        #    username=email_host_user,
        #    password=email_host_password,
        #    email_host_reply_to=email_host_reply_to,
        #    use_tls=True,
        #)
        #connection.open()
        #n = connection.send_messages(emails)
        n_sent = len( emails )
    else :
        try:
            n_sent = 0
            for email in emails:
                n_sent =  n_sent + int( email.send() )
                print("send_email_object success" + " (" + str(n_sent) + " delivered)")
        except Exception as e:
            print("send_email_object fail" + str(e))
            raise e
    return n_sent




def response_from_messages(messages):
    result = dict(status=set())
    result["messages"] = messages
    if len(messages) > 0 :
        for msg in messages:
            result["status"].add(msg)
        if "error" not in result["status"]:
            result["success"] = True
    return result


def get_localized_template(template_name):
    """Get major language version of template."""
    course = Course.objects.first()
    try:
        first_language = course.languages.split(",")[0]
    except AttributeError:
        first_language = "en"
    try:
        template = get_template(template_name + "." + first_language)
    except TemplateDoesNotExist as exception:
        logger.error(template_name + "." + first_language + " does not exist")
        raise exception
    return template


def chown(path, user=None, group=None, recursive=True):  # FIXME: CHOWN unutilized STUB reference exercises.models
    """Change user/group ownership of file

    Arguments:
    path: path of file or directory
    user: new owner username
    group: new owner group name
    recursive: set files/dirs recursively
    """

    ppath = pathlib.Path(path)
    if user is None:
        user = ppath.owner()
    if group is None:
        group = ppath.group()
    # print("USER =  %s " % user )
    # print("GROUP = %s " % group )
    # print("PPATH = %s " % ppath )

    try:
        if not recursive or os.path.isfile(path):
            shutil.chown(path, user, group)
        else:
            for root, dirs, files in os.walk(path):
                shutil.chown(root, user, group)
                for item in dirs:
                    shutil.chown(os.path.join(root, item), user, group)
                    shutil.copymode(path, (os.path.join(root, item)))
                for item in files:
                    shutil.chown(os.path.join(root, item), user, group)
                    shutil.copymode(path, (os.path.join(root, item)))
    except OSError as e:
        raise e
