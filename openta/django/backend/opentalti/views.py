#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

# -*- coding:utf-8 -*-
#
#  Based on django-auth-lti
#  Copyright (c) 2018 Rohit Jose
#
from django.middleware.csrf import get_token
import logging
import random
import time
import os
import re
import tempfile
import traceback

import workqueue.util as workqueue
from course.models import Course
from lti import ToolConsumer
from opentalti.gradebook import canvas_gradebook_pipeline
from pylti.common import LTIException, verify_request_common
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from users.models import OpenTAUser, is_anonymous_student
from utils import get_subdomain_and_db, get_subdomain_and_db_and_user

from backend import views as backendviews
from backend.views import set_persistent_lang
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as loginbase
from django.contrib.auth import logout as syslogout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.models import User
from backend.views import launch_sidecar_new

# from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt

from .apps import LTIAuth
from .forms import EditProfileForm

# Get an instance of a logger
logger = logging.getLogger(__name__)

@csrf_exempt
@xframe_options_exempt
def denied(r, msg="", help_url=None, clobber_cookies=False):
    messages.add_message(r, messages.ERROR, msg)

    if not help_url:
        try:
            help_url = settings.HELP_URL
        except Exception as e:
            logger.error("HELP_URL ERROR %s %s " % (type(e).__name__, str(e)))
            help_url = ""
    response = render(r, "base_failed.html", {"msg": msg, "help_url": help_url})
    if clobber_cookies:
        for cookie in r.COOKIES:
            response.delete_cookie(cookie)
    return response


@csrf_exempt
@xframe_options_exempt
def lti_main(request, course_pk=None):
    requestsave = request
    if request.method == 'POST' :
        referer = request.environ.get('HTTP_REFERER',request.META.get("HTTP_REFERER", "NO_REFERER") )
    subdomain, db = get_subdomain_and_db(request)
    settings.DB_NAME = db
    settings.SUBDOMAIN = subdomain
    debug = settings.DEBUG
    user = request.user
    roles = request.POST.get("roles", "")
    if course_pk == None:
        course = Course.objects.using(db).order_by("-published", "-pk")[0]
    else:
        course = Course.objects.using(db).get(pk=course_pk)
    allow_anonymous_student = course.allow_anonymous_student
    if allow_anonymous_student:
        if not roles == "Guest":
            username = request.user.username
            try:
                user = User.objects.using(db).get(username=username)
            except User.DoesNotExist:
                return denied(
                    request,
                    "User %s does not exist; anonymous user was probably erased" % username,
                )
            groups = list(request.user.groups.values_list("name", flat=True))
        if not is_anonymous_student(user):
            syslogout(request)  # LOGOUT OF ANY OTHER USERS BEFORE AUTHENTICATIN NEW
    else:
        syslogout(request)
    if request.user.is_authenticated:
        return backendviews.main(requestsave, course_pk, exerciseKey=None, passed_subdomain=subdomain)
    if course_pk is None:
        course = Course.objects.using(db).order_by("-published", "-pk")[0]
        course_pk = course.pk
    rolestring = request.POST.get("roles", "") 
    rolestring = re.sub("urn:lti:role:ims/lis/","",rolestring)
    rolestring = re.sub(r"\/", ",", rolestring)
    rolestring = re.sub(r":", ",", rolestring)
    roles = rolestring.split(",")
    roles = [item.strip() for item in roles ];
    valid_roles = (
        settings.VALID_ROLES
    )  # Formerly hardcoded as ['ContentDeveloper', 'Learner', 'Student', 'Instructor', 'Observer']
    proper_role = not set(roles).isdisjoint(valid_roles)
    #if True :
    if not proper_role :
        #logger.error(f"RETURN DENIED")
        return denied(
            request,
            f"LTI : Authentication is broken in role {rolestring} . If you are working with two Canvas courses, instances, close OpenTA before opening the other. If that is not the problem, log out of Canvas and try again.")

    #logger.error("LTI_MAIN course_pk = %s", course_pk)
    course = Course.objects.using(db).get(pk=course_pk)
    logging.debug("secret1 = %s", course.lti_key)
    logging.debug("secret2 = %s", course.lti_secret)
    params = {key: request.POST[key] for key in request.POST}
    try:
        request.session["lti_login"] = True
        if allow_anonymous_student:
            request.session["launch_presentation_return_url"] = "/logout"
        else:
            request.session["launch_presentation_return_url"] = params["launch_presentation_return_url"]
    except KeyError as e:
        logger.error("ERROR LAUNCH PRESENTATION URL %s %s " % (type(e).__name__, str(e)))
    except Exception as e:
        logger.error("ERROR LAUNCH PRESENTATION URL %s %s " % (type(e).__name__, str(e)))
    consumers = {str(course.lti_key): {"secret": str(course.lti_secret)}}
    #logger.error("CONSUMERS = %s", consumers)
    url = request.build_absolute_uri()
    #
    # FIRST CHECK POST CONTAINS SECRET
    #
    if not settings.RUNNING_DEVSERVER and not settings.RUNTESTS:
        headers = request.META
        #logger.error("HANDLE POST REQUEST ")
        #logger.error("HEADERS = %s", headers["PATH_INFO"])
        url = url.replace("http://","https://")
        try:
            verify_request_common(consumers, url, request.method, headers, params)
        except LTIException as e :
            return denied(request, f"LTI: Key and/or secret is probaly wrong {str(e)}  ")
    #
    #  IF USER DOES NOT EXIST CREATE AND RETURN USER
    #  IF USER DOES EXIST RETURN IT
    try:
        user = LTIAuth.ltiauth(LTIAuth, request)
    except Exception as e:
        formatted_lines = traceback.format_exc()
        logger.error("LTIAuth FULL PATH %s " % request.get_full_path())
        logger.error(f"LTIAuth error {request.method} {str(e)} STACKTRACE = {formatted_lines}")
        return denied(request, str(e))
    logging.debug("NEXT LOGIN BASE")
    # NEXT SET UP SESSION DATA USING THE AUTHENTICATION IN LTIAUTU
    try:
        logging.debug("CALL LOGINBASE")
        loginbase(request, user, backend="opentalti.apps.LTIAuth")
    except AttributeError:
        return denied(request, "LTI: Login failed ")
    except Exception as err :
        logging.error(f"ERROR 9271123 in LTI {type(err)} {str(err)}")
        return denied(request, "Authentication error: try again.")
    # AFTER LOGIN HAS BEEN ACHIEVED AND SESSION SET UP
    # PASS TO MAIN
    # logging.debug("CALL MAIN")
    # if not settings.SUBDOMAIN == subdomain:
    #    logger.error(
    #        f"INFO ERROR IN OPENTALTI SUBDOMAIN HAS CHANGED {request.user.username} subdomain={subdomain} settings.SUBDOMAIN={settings.SUBDOMAIN}"
    #    )
    #    settings.SUBDOMAIN = subdomain
    #    settings.DB_NAME = subdomain
    # if debug:
    #    logger.info(f"RETURNING MAIN AT END OF LTI")
    return backendviews.main(requestsave, course.pk, exerciseKey=None, passed_subdomain=subdomain,referer=referer)


# SEE https://www.edu-apps.org/code.html
@login_required
@xframe_options_exempt
def edit_profile(request):
    user = request.user
    subdomain, db = get_subdomain_and_db(request)
    opentauser, _ = OpenTAUser.objects.using(db).get_or_create(user=user)
    logging.debug("USERNAME = %s", opentauser.username())
    logging.debug("first = %s", user.first_name)
    logging.debug("last = %s", user.last_name)
    logging.debug("email = %s", user.email)
    form = EditProfileForm(
        request.POST or None,
        initial={
            "username": opentauser.username(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "pk": user.pk,
        },
    )

    exclude = ["pk"]
    if opentauser.lis_person_contact_email_primary:
        exclude = exclude + ["email"]
    if opentauser.lis_person_name_family:
        exclude = exclude + ["last_name"]
    if opentauser.lis_person_name_given:
        exclude = exclude + ["first_name"]
    if user.email == user.username:
        exclude = exclude + ["username", "email"]

    form.Meta.exclude = exclude

    context = {
        "form": form,
    }
    if request.method == "POST":
        logging.debug("TRY TO SAVE")
        logging.debug("REQUEST.POST = %s", request.POST)
        logging.debug(" action = %s", request.POST["action"])
        if form.is_valid():
            cform = form.cleaned_data
            logging.debug("form cleaned %s", form.cleaned_data)
            if "save" in request.POST["action"]:
                user.first_name = cform["first_name"]
                user.last_name = cform["last_name"]
                user.email = cform["email"]
                user.username = cform["username"]
                logging.debug("DO A SAVE")
                user.save(using=db)
            logging.debug("EDIT_PROFILE REDIRECT TO  lti/")
            # logger.error("REDIRECT 4")
            return redirect("/")
        else:
            logging.debug("ERRORS = %s", form.errors)
            return render(request, "edit_profile.html", context)
        # logger.error("REDIRECT5")
        return redirect("/")

    return render(request, "edit_profile.html", context)


def is_org(request):
    try:
        is_org = request.META["HTTP_HOST"].split(".")[2] == "org"
    except KeyError as e:
        is_org = False
    except IndexError as e:
        is_org = False
    return is_org


def is_se(request):
    try:
        is_se = request.META["HTTP_HOST"].split(".")[2] == "se"
    except KeyError as e:
        is_se = False
    except IndexError as e:
        is_se= False
    return is_se



@csrf_exempt
@xframe_options_exempt
def config_xml(request, course_name=None):
    #logger.error("LTI CONFIG_XML %s" % course_name)
    subdomain, db = get_subdomain_and_db(request)
    if course_name is not None:
        try:
            course = Course.objects.using(db).get(course_name__iexact=course_name)
        except Exception as e:
            logger.error("LTI_CONFIG_XML ERROR %s %s " % (type(e).__name__, str(e)))
            return HttpResponse(
                "<h1> Course name " + course_name + " not found </h1>",
                content_type="text/html",
            )
    else:
        try:
            course = Course.objects.using(db).order_by("-published", "-pk")[0]
            #logger.error(f"COURSE PUBLISHED = {course}")
        except IndexError as eouter:
            #logger.error(f"EOUTER = {type(eouter).__name__}")
            try:
                course = Course.objects.using(db).order_by("-pk")[0]
                logger.error(f"FIRST COURSE = {course}")
            except IndexError as e:
                return HttpResponse("<h1> No openta courses exist </h1>", content_type="text/html")
            except Exception as e:
                logger.error("GET COURSE ERROR - opentlti %s %s " % (type(e).__name__, str(e)))
                return HttpResponse("<h1> No openta courses exist </h1>", content_type="text/html")
    try:
        coursekey = "{}".format(course.course_key)
        coursename = "{}".format(course.course_name)
        coursepk = "{}".format(course.pk)
        logging.debug("COURSE KEY = %s", coursekey)
        logging.debug("coursename = %s", coursename)
        logging.debug("coursepk = %s", coursepk)
    except Exception as e:
        logger.error(f"OPENTALTI_ERROR E772291  course = {course} {type(e).__name__}")
        return HttpResponse("<h1> Error E772291 incorrect configuration </h1>", content_type="text/html")

    with open("opentalti/config.xml", "rb") as f:
        data = f.read()
    try:
        host = request.META["HTTP_HOST"]
    except:
        host = "localhost"
    url = "https://" + host + "/" + coursepk + "/lti/"
    logging.debug("URL = %s", url)
    domain = (host.split(":"))[0]
    data = data.decode()
    data = re.sub(r"OPENTASERVER_LTI", url, data)
    data = re.sub(r"DOMAIN", domain, data)
    data = re.sub(r"COURSE_KEY", coursekey, data)
    opentatarget = settings.TARGET_WINDOW
    data = re.sub(r"opentatarget",opentatarget,data)
    if is_org(request):
        data = re.sub(r"OpenTA", f"OpenTA-{subdomain}-alpha", data)
    elif is_se(request):
        data = re.sub(r"OpenTA", f"Backup-OpenTA-{subdomain}", data)
    else :
        data = re.sub(r"OpenTA", f"OpenTA-{subdomain}", data)
    data = data.encode("utf-8")
    response = HttpResponse(data, content_type="text/xml")
    response["Content-Disposition"] = 'attachment; filename="config.xml"'
    return response


@login_required
@xframe_options_exempt
def change_password(request):
    logging.debug("CHANGE PASSWORD")
    subdomain, db = get_subdomain_and_db(request)
    try:
        if "lti_login" in request.session:
            lti_login = request.session["lti_login"]
        else:
            lti_login = False
        passwordform = SetPasswordForm
        if not is_anonymous_student(request.user) and not lti_login:
            passwordform = PasswordChangeForm
        logging.debug("CHANGE PASSWORD")
        if request.method == "POST":
            form = passwordform(request.user, request.POST)
            logging.debug("POST: user = %s", str(request.user))
            if form.is_valid():
                logging.debug("PASSWORD FORM VALID")
                if "save" in request.POST["action"]:
                    user = form.save()
                    update_session_auth_hash(request, user)  # Important!
                    messages.success(request, "Password was reset!")
                logging.debug(
                    "REDIRECT TO %s",
                )
                # logger.error("REDIRECT1")
                return redirect("/")
            else:
                logging.debug("PASSWORD FORM NOT VALID")
                messages.error(request, "Password not reset.")
                # logger.error("REDIRECT2")
                return redirect("/")
        else:
            form = passwordform(request.user)
        return render(request, "change_password.html", {"form": form})
    except Exception as e:
        messages.error(request, "Unknown error and password not reset.")
        formatted_lines = traceback.format_exc()
        logging.error("PASSWORD NOT RESET UNKNOWN ERROR %s  trace: %s " % (str(e), formatted_lines))
        # logger.error("REDIRECT3")
        return redirect("/")


@api_view(["POST"])
@parser_classes((MultiPartParser,))
def amend_canvas_gradebook(request, course_pk):
    subdomain, db = get_subdomain_and_db(request)
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    if not request.user.has_perm("exercises.edit_exercise"):
        return Response({}, status.HTTP_403_FORBIDDEN)
    tempfile.tempdir = f"{settings.VOLUME}/workqueue/taskresults"
    if not os.path.isdir( tempfile.tempdir ):
        os.makedirs(tempfile.tempdir,exist_ok=True)
    _, tmp_filename = tempfile.mkstemp(suffix=".csv")
    with open(tmp_filename, "wb") as destination:
        for chunk in request.FILES["file"].chunks():
            destination.write(chunk)
    logger.error(f"tmp_filename = {tmp_filename}")
    # st = os.stat(tmp_filename )
    # os.chmod(tmp_filename, 0o777)
    # os.chmod(tmp_filename, st.st_mode | stat.S_IRWXO  )
    task_id = workqueue.enqueue_task(
        "canvas_gradebook",
        canvas_gradebook_pipeline,
        course=dbcourse,
        csv_file=tmp_filename,
    )
    return Response({"task_id": task_id})


def get_course_by_name(course_name):
    if course_name is not None:
        try:
            course = Course.objects.get(course_name__iexact=course_name)
        except Exception as e:
            logger.error("GET COURSE NAME ERROR - opentlti %s %s " % (type(e).__name__, str(e)))

            return None
    else:
        try:
            course = Course.objects.order_by("-published", "-pk")[0]
        except Exception as e:
            logger.error("GET COURSE  BY NAME ERROR 1 opentlti %s %s " % (type(e).__name__, str(e)))
            try:
                course = Course.objects.order_by("-pk")[0]
            except Exception as e2:
                logger.error("GET COURSE  BY NAME ERROR 2 opentlti %s %s " % (type(e2).__name__, str(e2)))
                return None
    return course


# https://pypi.org/project/lti/
# def is_anonymous_student( user ):
#     groups = list( user.groups.values_list('name',flat = True)  )


def index(request, course_name=None):
    subdomain, db = get_subdomain_and_db(request)
    if not (subdomain == settings.SUBDOMAIN):
        logger.error(f"ERROR E971691 PATCH OPENTALTI {request.user} {settings.SUBDOMAIN} {subdomain} ")
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
    course = get_course_by_name(course_name)
    set_persistent_lang(course, request)
    if not course:
        return denied(
            request,
            "This course does not exist %s " % str(subdomain).split(".")[0],
        )
    if not course.published:
        return denied(request, "course %s  is not published " % course.course_name)
    if not course.allow_anonymous_student:
        if not "launch_presentation_return_url" in request.session:
            return denied( request, "Authentication is broken. If you are working with two Canvas courses close OpenTA before opening the other. If that is not the problem, log out of Canvas and try again.")
        else:
            return denied(request, "course %s  does not allow anonymous student " % course.course_name)
    else:
        request.session["launch_presentation_return_url"] = "/logout"
    # logger.error("COOKIES = %s " % request.COOKIES)
    username = None
    if "username" in request.COOKIES:
        username = request.COOKIES.get("username")
        return denied(
            request,
            "You are trying to login anonymously to %s but have an account %s. Use the ordinary login window."
            % (username, str(subdomain)),
            clobber_cookies=True,
        )
    if "anonymoususer" in request.COOKIES:
        username = request.COOKIES.get("anonymoususer")
        # logger.error("USERNAME FOUND IN COOKIES", username)
        try:
            user = User.objects.using(db).get(username=username)
            opentauser = OpenTAUser.objects.using(db).get(user=user)
            user_id = opentauser.lti_user_id
            if user.has_usable_password() and not is_anonymous_student(user):
                return denied(
                    request,
                    "User %s has a password in course %s . Login with password is required. "
                    % (username, str(subdomain)),
                    clobber_cookies=True,
                )
        except Exception as e:
            logger.error("GET COURSE USERNAME ERROR - opentlti %s %s " % (type(e).__name__, str(e)))
            return denied(
                request,
                "You are trying to login as %s , a user which does not exist in the course  %s . Cookies will be reset for this site. Copy the username if you need it for any reason.  "
                % (username, str(subdomain)),
                clobber_cookies=True,
            )
        if user_id == None:
            return denied(
                request,
                "Login as user %s failed.  Reset cookies for the site %s and try again. Copy the username if you think you need it. "
                % (username, str(subdomain)),
                clobber_cookies=True,
            )
        groups = list(request.user.groups.values_list("name", flat=True))
        if not is_anonymous_student(user):
            return denied(
                request,
                "%s cannot login anonymously into %s . Use ordinary login" % (username, str(subdomain)),
                clobber_cookies=True,
            )

    else:
        # logger.error("USERNAME NOT FOUND IN SESSION")
        # sername  = 'dummy-username'
        # user,_ = User.objects.get_or_create(username=username)
        # opentauser = OpenTAUser.objects.get_or_create(user=user)
        user_id = str(random.randint(11111, 99999))
    # logger.error("USERNAME = %s " % username )
    # logger.error("USERID = %s " % user_id )
    consumer_key = str(course.lti_key)
    consumer_secret = str(course.lti_secret)
    # logger.error("REQUEST FULL PATH %s " % request.get_full_path())
    # logger.error("REQUEST FULL HOST %s " % get_current_site( request) )
    host = request.META.get("HTTP_HOST", "localhost").split(":")[0]
    if course:
        consumer = ToolConsumer(
            consumer_key=consumer_key,  # '331483c6-8e75-4e69-8b27-6feb100ff0f5',
            consumer_secret=consumer_secret,  # 'a040d59a-8a1b-4d1e-b82c-45f1fadeef63',
            launch_url="https://%s%s/lti/" % (host, settings.PORT),  #'https://v320a.localhost:8000/lti/',
            params={
                "lti_message_type": "basic-lti-launch-request",
                "user_id": user_id,
                "custom_user_id": user_id,
                "roles": "Guest",
                "lti_version": "LTI-1.0",
                "resource_link_id": settings.SUBDOMAIN,
            },
        )

        response = render(
            request,
            "lti_consumer.html",
            {
                "launch_data": consumer.generate_launch_data(),
                "launch_url": consumer.launch_url,
                "course": course,
            },
        )
        return response

    else:
        return denied(request, "course %s  does not exist  " % course_name)


@csrf_exempt
@xframe_options_exempt
def launch_sidecar(request,*args, **kwargs ):
    print(f"LTI LAUNCH SIDECAR {args} {kwargs}")
    return launch_sidecar_new( request,*args,**kwargs)
#    subdomain,db,user = get_subdomain_and_db_and_user(request)
#    groups = list(request.user.groups.values_list("name", flat=True))
#    thecsrftoken = get_token(request)
#    if hasattr( settings ,'SIDECAR_URL'):
#        url = settings.SIDECAR_URL
#    else :
#        return redirect("/" )
#    t = str( int(  time.time() )).encode() ;
#    if request.user.is_staff :
#        groups.append('Admin')
#    roles = ','.join(groups)
#    data = {
#            'destination_url' : url,
#            'lti_message_type': 'basic-lti-launch-request',
#            'lti_version': 'LTI-1p0',
#	        'subdomain':  str( subdomain),
#            'resource_link_id': 'resourceLinkId',
#            'resource_link_title': subdomain,
#	        'custom_canvas_login_id': str( user.username),
#	        'lis_person_name_contact_email_primary': str( user.email),
#            'thecsrftoken' : str( thecsrftoken),
#	        'roles': roles,
#            'lti_roles': roles,
#            'oauth_consumer_key': '889d570f472',
#            'oauth_signature_method': 'HMAC-SHA1',
#            'oauth_timestamp': t,
#            'oauth_version': '1.0'
#        };
#    #response = render(request, 'post_redirect.html', data )
#    response = render(request, 'launch_tool.html', data )
#    #for header, value in response.headers.items():
#    #    print(f'  {header}: {value}')
#
#    return response


