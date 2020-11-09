#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#  Based on django-auth-lti
#  Copyright (c) 2018 Rohit Jose
#
from django.template.response import TemplateResponse
from django.views.decorators.clickjacking import xframe_options_deny, xframe_options_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.module_loading import import_string
from django.views.decorators.csrf import csrf_exempt
from pylti.common import LTIException, verify_request_common
from backend import views as backendviews
from users.models import OpenTAUser
from django.contrib.auth.models import Group, User
from course.models import Course
from course.serializers import CourseSerializer
from exercises.modelhelpers import enrollment
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

# from backend.views import set_persistent_lang
from django.contrib.auth import authenticate
from .apps import LTIAuth
from django.contrib.auth import login as loginbase
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.shortcuts import render, redirect
from .forms import EditProfileForm
from django.contrib.auth import logout as syslogout
import re
import io

import workqueue.util as workqueue
from opentalti.gradebook import canvas_gradebook_pipeline
import tempfile

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


@xframe_options_exempt
def denied(r, msg='',help_url=None):
    if not help_url :
        try: 
            help_url = settings.HELP_URL
        except:
            help_url = ''
    return render(r, "denied.html", {'msg': msg,'help_url': help_url})


@csrf_exempt
@xframe_options_exempt
def lti_main(request, course_pk=None):
    #
    # MUST PARSE THE POST REQUEST TO EXTRACT KEYS
    # IN ORDER TO DECIDE ACTION  AND PREPARE AUTHORIZATION
    # THE RESULT OF ALL THIS IS TO MODIFY THE REQUEST
    # AND TO CALL auth
    #
    syslogout(request)  # LOGOUT OF ANY OTHER USERS BEFORE AUTHENTICATIN NEW
    if request.user.is_authenticated:
        return backendviews.main(request, course_pk)
    if course_pk is None:
        course = Course.objects.order_by("-published", "-pk")[0]
        course_pk = course.pk
    rolestring = request.POST.get("roles", '')
    rolestring = re.sub(r"\/",",",rolestring)
    rolestring = re.sub(r":",",",rolestring)
    roles = rolestring.split(',') 
    valid_roles = settings.VALID_ROLES # Formerly hardcoded as ['ContentDeveloper', 'Learner', 'Student', 'Instructor', 'Observer']
    proper_role = not set(roles).isdisjoint(valid_roles)
    if not proper_role:
        return denied(
            request,
            "LTI : The role %s is not valid. You may be logged into the wrong Canvas or not properly registered in the course. Please contact course examiner with an email if you have questions." %  request.POST.get("roles", ''),
        )

    logging.debug("LTI_MAIN course_pk = %s", course_pk)
    course = Course.objects.get(pk=course_pk)
    logging.debug("secret1 = %s", course.lti_key)
    logging.debug("secret2 = %s", course.lti_secret)
    params = {key: request.POST[key] for key in request.POST}
    try:
        logging.debug(
            "PARAMS launch_presentation_return_url = %s", params["launch_presentation_return_url"]
        )
        request.session["lti_login"] = True
        request.session["launch_presentation_return_url"] = params["launch_presentation_return_url"]
    except:
        request.session["launch_presentation_return_url"] = "/logout"
        logging.debug("PARAM NOT DEFINED")
    consumers = {str(course.lti_key): {"secret": str(course.lti_secret)}}
    logging.debug("CONSUMERS = %s", consumers)
    url = request.build_absolute_uri()
    headers = request.META
    logging.debug("HANDLE POST REQUEST ")
    logging.debug("HEADERS = %s", headers["PATH_INFO"])
    #
    # FIRST CHECK POST CONTAINS SECRET
    #
    try:
        verify_request_common(consumers, url, request.method, headers, params)
    except LTIException:
        return denied(request, "LTI: Key and/or secret is probaly wrong ")
    #
    #  IF USER DOES NOT EXIST CREATE AND RETURN USER
    #  IF USER DOES EXIST RETURN IT
    try:
        logging.debug("GET OR CREATE")
        user = LTIAuth.ltiauth(LTIAuth, request)
    except LTIException as e:
        return denied(request, str(e))
    logging.debug("NEXT LOGIN BASE")
    # NEXT SET UP SESSION DATA USING THE AUTHENTICATION IN LTIAUTU
    try:
        logging.debug("CALL LOGINBASE")
        loginbase(request, user, backend="opentalti.apps.LTIAuth")
    except AttributeError as e:
        return denied(request, "LTI: Login failed ")
    # AFTER LOGIN HAS BEEN ACHIEVED AND SESSION SET UP
    # PASS TO MAIN
    logging.debug("CALL MAIN")
    return backendviews.main(request, course.pk)


# SEE https://www.edu-apps.org/code.html
@login_required
@xframe_options_exempt
def edit_profile(request):
    user = request.user
    opentauser, _ = OpenTAUser.objects.get_or_create(user=user)
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

    context = {"form": form, "subpath": "/" + settings.SUBPATH}
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
                user.save()
            logging.debug("EDIT_PROFILE REDIRECT TO  " + settings.SUBPATH + "lti/")
            print("REDIRECT 4")
            return redirect("/" + settings.SUBPATH)
        else:
            logging.debug("ERRORS = %s", form.errors)
            return render(request, "edit_profile.html", context)
        print("REDIRECT5")
        return redirect("/" + settings.SUBPATH)

    return render(request, "edit_profile.html", context)


@csrf_exempt
@xframe_options_exempt
def config_xml(request, course_name=None):
    logging.debug("LTI CONFIG_XML %s", course_name)
    if course_name is not None:
        try:
            course = Course.objects.get(course_name__iexact=course_name)
        except:
            return HttpResponse(
                "<h1> Course name " + course_name + " not found </h1>", content_type="text/html"
            )
    else:
        try:
            course = Course.objects.order_by("-published", "-pk")[0]
        except:
            try:
                course = Course.objects.order_by("-pk")[0]
            except:
                return HttpResponse("<h1> No openta courses exist </h1>", content_type="text/html")
    try:
        coursekey = "{}".format(course.course_key)
        coursename = "{}".format(course.course_name)
        coursepk = "{}".format(course.pk)
        logging.debug("COURSE KEY = %s", coursekey)
        logging.debug("coursename = %s", coursename)
        logging.debug("coursepk = %s", coursepk)
    except:
        return HttpResponse("<h1> incorrect configuration </h1>", content_type="text/html")

    with open("opentalti/config.xml", "rb") as f:
        data = f.read()
    url = "https://" + request.META["HTTP_HOST"] + "/" + settings.SUBPATH + coursepk + "/lti/"
    logging.debug("URL = %s", url)
    domain = (request.META["HTTP_HOST"].split(":"))[0]
    data = data.decode()
    data = re.sub(r"OPENTASERVER_LTI", url, data)
    data = re.sub(r"DOMAIN", domain, data)
    data = re.sub(r"COURSE_KEY", coursekey, data)
    data = data.encode("utf-8")
    response = HttpResponse(data, content_type="text/xml")
    response["Content-Disposition"] = 'attachment; filename="config.xml"'
    return response


@login_required
@xframe_options_exempt
def change_password(request):
    logging.debug("CHANGE PASSWORD")
    try:
        passwordform = SetPasswordForm
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
                logging.debug("REDIRECT TO %s", settings.SUBPATH)
                print("REDIRECT1")
                return redirect("/" + settings.SUBPATH)
            else:
                logging.debug("PASSWORD FORM NOT VALID")
                messages.error(request, "Password not reset.")
                print("REDIRECT2")
                return redirect("/" + settings.SUBPATH)
        else:
            form = passwordform(request.user)
        subpath = settings.SUBPATH.strip("/")
        logging.debug("SUBPATH = %s", subpath)
        return render(request, "change_password.html", {"form": form, "subpath": subpath})
    except:
        messages.error(request, "Password not reset.")
        print("REDIRECT3")
        return redirect("/" + settings.SUBPATH)


@api_view(['POST'])
@parser_classes((MultiPartParser,))
def amend_canvas_gradebook(request, course_pk):
    dbcourse = Course.objects.get(pk=course_pk)
    if not request.user.has_perm('exercises.edit_exercise'):
        return Response({}, status.HTTP_403_FORBIDDEN)

    _, tmp_filename = tempfile.mkstemp(suffix=".csv")
    with open(tmp_filename, 'wb') as destination:
        for chunk in request.FILES['file'].chunks():
            destination.write(chunk)

    task_id = workqueue.enqueue_task("canvas_gradebook", canvas_gradebook_pipeline, course=dbcourse, csv_file=tmp_filename)
    return Response({'task_id': task_id})
