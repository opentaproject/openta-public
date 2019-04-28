#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#  Based on django-auth-lti
#  Copyright (c) 2018 Rohit Jose
#
from django.template.response import TemplateResponse
from django.views.decorators.clickjacking import xframe_options_deny, xframe_options_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin
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

# from backend.views import set_persistent_lang
from django.contrib.auth import authenticate
from .apps import LTIAuth
from django.contrib.auth import login as loginbase
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.shortcuts import render, redirect
from .forms import EditProfileForm
import re
import io

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)



#def get_reverse(objs):
#    try:
#        return reverse(objs)
#    except:
#        pass
#    raise Exception("We got a URL reverse issue: %s." % str(objs))

def dprint(*args,**kwargs) :
    txt = "OPENTLTI.VIEWS: "
    for value in  list(args ):
        txt = txt + ( str(value) )
    logger.info( txt)


# @csrf_exempt
@xframe_options_exempt
def denied(r):
    return render(r, "denied.html")


@csrf_exempt
@xframe_options_exempt
def root(request, course_pk=None):
    #try:
    #    request.session['lti_login']  = not request.session['lti_login']
    #except:
    #    request.session['lti_login'] = False
    dprint("ROOT course_pk" )
    #tdprint("lti_login = ", request.session['lti_login'] )
    if course_pk is None:
        course = Course.objects.order_by("-published", "-pk")[0]
        course_pk = course.pk
    if request.method == "POST":
        dprint("PASS TO LTI_MAIN")
        lti_main(request, course_pk)
    dprint("PASS TO BAKCEND_VIEWS_MAIN")
    return backendviews.main(request, course_pk)


# @csrf_exempt
@xframe_options_exempt
def lti_main(request, course_pk):
    #
    # MUST PARSE THE POST REQUEST TO EXTRACT KEYS
    # IN ORDER TO DECIDE ACTION  AND PREPARE AUTHORIZATION
    # THE RESULT OF ALL THIS IS TO MODIFY THE REQUEST
    # AND TO CALL auth
    #
    dprint("LTI_MAIN course_pk = ", course_pk)
    assert ( not course_pk == None )
    course = Course.objects.get(pk=course_pk)
    course_key = str(course.course_key)
    dprint("secret1 = ", course.lti_key)
    dprint("secret2 = ", course.lti_secret)
    params = {key: request.POST[key] for key in request.POST}
    try:
        dprint("PARAMS launch_presentation_return_url = ", params["launch_presentation_return_url"])
        request.session["lti_login"] = True
        request.session["launch_presentation_return_url"] = params["launch_presentation_return_url"]
        # request.session['launch_presentation_return_url'] = "/logout"
    except:
        request.session["launch_presentation_return_url"] = "/logout"
        dprint("PARAM NOT DEFINED")
    # consumers = settings.PYLTI_CONFIG['consumers']
    consumers = {str(course.lti_key): {"secret": str(course.lti_secret)}}
    dprint("CONSUMERS = ", consumers)
    url = request.build_absolute_uri()
    headers = request.META
    dprint("HANDLE POST REQUEST ")
    dprint("HEADERS = ", headers["PATH_INFO"])
    #
    # FIRST CHECK POST CONTAINS SECRET
    # 
    try:
        verify_request_common(consumers, url, request.method, headers, params)
    except LTIException as e:
        raise LTIException("B: " + "LTI request failed. Check key and secret ")
    #
    #  IF USER DOES NOT EXIST CREATE AND RETURN USER
    #  IF USER DOES EXIST RETURN IT
    #  SHOULD NOT FAIL
    try:
        print("GET OR CREATE")
        user = LTIAuth.ltiauth(LTIAuth, request)
    except LTIException as e:
        raise LTIException("A: REQUESTED COURSE DOES NOT EXIST")
    dprint("NEXT LOGIN BASE")
    # NEXT SET UP SESSION DATA USING THE AUTHENTICATION IN LTIAUTU
    try:
        dprint("CALL LOGINBASE")
        loginbase(request, user, backend="opentalti.apps.LTIAuth")
    except AttributeError as e:
        raise AttributeError("C + login failed ")
    # AFTER LOGIN HAS BEEN ACHIEVED AND SESSION SET UP
    # PASS TO MAIN
    dprint("CALL MAIN")
    return backendviews.main(request)
    #return redirect( reverse('main') )
    #login_method_hook = settings.PYLTI_CONFIG.get("method_hooks", {}).get("valid_lti_request", None)
    #next_url = "/"
    #try:
    #    if login_method_hook:
    #        # If there is a return URL from the configured call the redirect URL
    #        # is updated with the one that is returned. This is to enable redirecting to
    #        # constructed URLs
    #        dprint("LTIAUTH SUCCEEDED")
    #        update_url = import_string(login_method_hook)(params, request)
    #        if update_url:
    #            next_url = update_url
    #except:
    #    pass
    #dprint("OPENTLTI VIEWS next_url = ", next_url)
    #return HttpResponseRedirect(next_url)


# @csrf_exempt
@xframe_options_exempt
def invalid_lti_request(user_payload, request):
    dprint("INVALID LTI REQUEST AGAIN")
    extra = {}
    course = Course.objects.order_by("-published", "-pk")[0]
    course_data = CourseSerializer(course).data
    extra = dict(course=course_data, timezone=settings.TIME_ZONE)
    # lang = set_persistent_lang(course, request)
    dprint("DENIED.HTML")
    response = render(request, "info.html", context=extra)
    # response = render(request, "maintenance.html", content=extra)
    # if settings.CSRF_COOKIE_NAME:
    #    response.set_cookie(key='csrf_cookie_name', value=settings.CSRF_COOKIE_NAME)
    subpath = settings.SUBPATH.strip("/")
    # response.set_cookie(key='subpath', value=subpath)
    # response.set_cookie(key='lang', value=lang)
    dprint("INVALID LTI REQUEST")
    return response


# SEE https://www.edu-apps.org/code.html
@xframe_options_exempt
def edit_profile(request):
    user = request.user
    opentauser, _ = OpenTAUser.objects.get_or_create(user=user)
    dprint("USERNAME = ", opentauser.username())
    dprint("first = ", user.first_name)
    dprint("last = ", user.last_name)
    dprint("email = ", user.email)
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
        dprint("TRY TO SAVE")  # ,request.POST['first_name'] , request.POST['last_name']  )
        dprint("REQUEST.POST = ", request.POST)
        dprint(" action = ", request.POST["action"])
        if form.is_valid():
            cform = form.cleaned_data
            dprint("form cleaned", form.cleaned_data)
            if "save" in request.POST["action"]:
                user.first_name = cform["first_name"]
                user.last_name = cform["last_name"]
                user.email = cform["email"]
                user.username = cform["username"]
                dprint("DO A SAVE")
                user.save()
            dprint("EDIT_PROFILE REDIRECT TO  " + settings.SUBPATH + "lti/")
            return redirect("/" + settings.SUBPATH + "lti/")
        else:
            dprint("ERRORS = ", form.errors)
            return render(request, "edit_profile.html", context)
        return redirect("/" + settings.SUBPATH + "lti/")

    return render(request, "edit_profile.html", context)


@csrf_exempt
@xframe_options_exempt
def config_xml(request, course_name=None):
    dprint("LTI CONFIG_XML", course_name)
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
        dprint("COURSE KEY = ", coursekey)
        dprint("coursename = ", coursename)
        dprint("coursepk = ", coursepk)
    except:
        return HttpResponse("<h1> incorrect configuration </h1>", content_type="text/html")
    # with open('opentalti/config.opentaserver.xml', 'rb') as f:
    #    data = f.read()
    with open("opentalti/config.xml", "rb") as f:
        data = f.read()
    url = "https://" + request.META["HTTP_HOST"] + "/" + settings.SUBPATH + coursepk + "/lti/"
    dprint("URL = ", url)
    domain = (request.META["HTTP_HOST"].split(":"))[0]
    # dprint("DOAMIN = ", domain)
    data = data.decode()
    # data = data.decode()
    data = re.sub(r"OPENTASERVER_LTI", url, data)
    data = re.sub(r"DOMAIN", domain, data)
    data = re.sub(r"COURSE_KEY", coursekey, data)
    data = re.sub(r"OpenTA", coursename, data)
    data = data.encode("utf-8")
    # data = data.encode()
    # dprint("8888")
    # dprint("data = ", data, type( data ) )
    # dprint("DATA = ", data , type(data) )
    # data = data.encode()
    response = HttpResponse(data, content_type="text/xml")
    response["Content-Disposition"] = 'attachment; filename="config.xml"'
    return response


# @csrf_exempt
@xframe_options_exempt
def change_password(request):
    dprint("CHANGE PASSWORD")
    try:
        # user = request.user;
        ##dprint("SESSIONS LAUNCH = ", request.session['launch_presentation_return_url'] )
        # if user.has_usable_password() :
        #    if  request.session['launch_presentation_return_url'] == './logout' :
        #        #passwordform =  PasswordChangeForm
        #        passwordform =  SetPasswordForm
        #    else :
        #        passwordform =  SetPasswordForm
        # else:
        passwordform = SetPasswordForm
        dprint("CHANGE PASSWORD")
        if request.method == "POST":
            form = passwordform(request.user, request.POST)
            dprint("POST: user = ", str(request.user))
            if form.is_valid():
                dprint("PASSWORD FORM VALID")
                if "save" in request.POST["action"]:
                    user = form.save()
                    update_session_auth_hash(request, user)  # Important!
                    messages.success(request, "Passward was reset!")
                dprint("REDIRECT TO ", settings.SUBPATH)
                return redirect("/" + settings.SUBPATH + "lti/")
            else:
                dprint("PASSWORD FORM NOT VALID")
                messages.error(request, "Password not reset.")
                return redirect("/" + settings.SUBPATH + "lti/")
        else:
            form = passwordform(request.user)
        subpath = settings.SUBPATH.strip("/")
        dprint("SUBPATH = ", subpath)
        return render(request, "change_password.html", {"form": form, "subpath": subpath})
    except:
        messages.error(request, "Password not reset.")
        return redirect("/" + settings.SUBPATH + "lti/")
