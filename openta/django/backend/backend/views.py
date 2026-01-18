# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from datetime import timezone
from django.middleware.csrf import get_token
from django.http import JsonResponse

import ssl
import btoa
from django.views.decorators.cache import never_cache
from cryptography.fernet import Fernet
import datetime
from utils import db_info_var
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
import urllib
from pprint import pprint
from glob import glob
import re
import json
from django.core import serializers
from twofactor.utils import create_url_safe_base64, get_safe_ips
from twofactor.utils import delete_otp_secret
from backend.mobiledetect.detection import Detection
from backend.mobiledetect.user_agent import UserAgnet
import hashlib
import base64
from PIL import Image
import logging
import subprocess
import io
import os
import time
import sys,traceback
import shutil
from django.views.decorators.http import etag
import qrcode, pyotp;
import psutil

from course.models import Course, sync_opentasite
from exercises.models import Exercise
from course.serializers import CourseSerializer
from django_ratelimit.decorators import ratelimit
from exercises.modelhelpers import enrollment
from exercises.views.file_handling import serve_file
from invitations.models import Invitation
from invitations.utils import get_invitation_model
from opentalti.apps import create_new_guest_user
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from users.models import OpenTAUser, is_anonymous_student
from utils import get_subdomain, get_subdomain_and_db , get_subdomain_and_db_and_user
from backend.middleware import log_500_error

from backend.forms import (
    CustomPasswordResetForm,
    RegisterWithPasswordForm,
    UserCreateFormDomain,
    UserCreateFormNoPassword,
)
from backend.middleware import verify_or_create_database_connection
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as syslogout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm, UserChangeForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group, User
from django.contrib.auth.views import LoginView, LogoutView
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils import translation
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.generic.edit import CreateView, FormView

# from hijack.signals import hijack_started, hijack_ended

logger = logging.getLogger(__name__)


# from django.db import connections
# from django.db.utils import DEFAULT_DB_ALIAS, load_backend
#
# def create_connection(alias=DEFAULT_DB_ALIAS):
#    connections.ensure_defaults(alias)
#    connections.prepare_test_settings(alias)
#    db = connections.databases[alias]
#    backend = load_backend(db['ENGINE'])
#    return backend.DatabaseWrapper(db, alias)

# def create_error_view(error_code):
#    def custom_error_view(request, *args, **kwargs):
#        print(f"ERROR_CODE = {error_code}")
#        logger.error(f"MY_CUSTOM_ERROR_VIEW FULL_PATH={request.get_full_path()} META={request.META}")
#    return custom_error_view


# def get_all_logged_in_users():
#    # Query all non-expired sessions
#    # use timezone.now() instead of datetime.now() in latest versions of Django
#    sessions = Session.objects.filter(expire_date__gte=timezone.now())
#    uid_list = []
#
#    # Build a list of user ids from that query
#    for session in sessions:
#        data = session.get_decoded()
#        uid_list.append(data.get('_auth_user_id', None))
#
#    # Query all logged in users based on id list
#    return User.objects.filter(id__in=uid_list)


#def log_500_error(txt):
#    filename = "/subdomain-data/errormsg";
#    fp = open(filename, 'a');
#    fp.write(f"{txt}\n");
#    fp.close



@csrf_exempt
def custom_error_403_view(request, exception=None):
    print(f"RENDER 403")
    return render(request, '403.html', status=403)



@csrf_exempt
def custom_error_500_view(request):
    """
    print 500 error
    """
    #try :
    #    shutil.copy('/tmp/gunicorn.err.log', f'/subdomain-data/err.log')
    #except :
    #    pass
    logger.error(f"CUSTOM_ERROR_500_VIEW")
    type, value, tb = sys.exc_info()
    txt = traceback.format_exception(type, value, tb)
    try :
        path = request.build_absolute_uri()
        subdomain  = get_subdomain(request)
        if not os.path.exists(f"/subdomain-data/{subdomain}") :
            logger.error(f"500 PASSED BOGUS XXX SUBDOMAIN {path}  with value={value} {type} and stacktrace = {txt}  request={vars(request)}  ")
        elif '/asset/' in path :
            logger.error(f"500 PASSED ASSET XXX ERROR on path  {path}  with value={value} {type} and stacktrace = {txt}  request={vars(request)}  ")
        else :
            if 'accepted_renderer' in txt :
                logger.error(f"500 accepted_renderer XXX ERROR CAUGHT on path  {path} ")
            else :
                log_500_error(f"500 CAUGHT XXX on path  {path}  with value={value} {type} and stacktrace = {txt}  request={vars(request)}  ")
    except Exception as e :
        logger.error(f"500 ERROR XXX {type(e)} {str(e)} caught and ignored in custom_error_500_view")
        pass
    raise Http404(f"Server error on {path} ")


def get_sidecar_count(username,subdomain,exercise=None,course_pk=None) :
    if not settings.USE_SIDECAR :
        return -1
    try :
        url = f'{settings.SIDECAR_URL}/sidecar_count/'
        data = { 'username' : username, 'subdomain' : subdomain, 'exercise' : str( exercise ) }
        context = ssl._create_unverified_context()
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        r = urllib.request.Request(url , data=encoded_data)
        with  urllib.request.urlopen(r,context=context)  as response :
            response_data = response.read()
            parsed_data = json.loads(response_data.decode('utf-8'))
        return parsed_data
    except Exception as err :
        logger.info(f"GET_SIDECAR_COUNT_ERROR {type(err).__name__} {str(err)}")
        return -1

@login_required
@xframe_options_exempt
def register_anonymous_user(request):
    passwordform = UserChangeForm
    passwordform = SetPasswordForm
    course = Course.objects.get(pk=request.course_pk)
    # if request.method == 'GET' :
    # print("PW_CHANGE GET " , request.GET)
    if request.method == "POST":
        # print("PW_CHANGE POST" , request.POST)
        if request.POST["action"] == "cancel":
            return redirect("/" + "logout/?next=login")
    if True:
        form = passwordform(request.user, request.POST)
        # logging.debug("POST: user = %s", str(request.user))
        if form.is_valid():
            # logging.debug("PASSWORD FORM VALID")
            if "save" in request.POST["action"]:
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                delete_otp_secret( user)
                if settings.USE_OTP :
                    messages.success(request, "Password was reset! You must also reset OTP")
                else :
                    messages.success(request, "Password was reset! ")

            # print("REDIRECT1")
            return redirect("/")
        # else:
        #    logging.debug("PASSWORD FORM NOT VALID")
        #    messages.error(request, "Password not reset.")
        #    #print("REDIRECT2")
    else:
        form = passwordform(request.user)
    return render(request, "change_password.html", {"form": form})


@login_required
@xframe_options_exempt
def pw_change(request):
    passwordform = SetPasswordForm
    # if request.method == 'GET' :
    # print("PW_CHANGE GET " , request.GET)
    if request.method == "POST":
        # print("PW_CHANGE POST" , request.POST)
        if request.POST["action"] == "cancel":
            return redirect("/logout/?next=login")
    if True:
        form = passwordform(request.user, request.POST)
        # logging.debug("POST: user = %s", str(request.user))
        if form.is_valid():
            # logging.debug("PASSWORD FORM VALID")
            if "save" in request.POST["action"]:
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                if settings.USE_OTP :
                    messages.success(request, "Password was reset! You must also reset OTP")
                else :
                    messages.success(request, "Password was reset! ")
                if not settings.RUNTESTS :
                    return redirect("/" ) # + "logout/?next=login")
            # print("REDIRECT1")
            return redirect("/")
        # else:
        #    logging.debug("PASSWORD FORM NOT VALID")
        #    messages.error(request, "Password not reset.")
        #    #print("REDIRECT2")
    else:
        form = passwordform(request.user)
    return render(request, "change_password.html", {"form": form})
    # except:
    #    messages.error(request, "Password not reset.")
    #    #print("REDIRECT3")



def make_owner_if_none_exists(user):
    opentauser = user.opentauser
    course = opentauser.courses.all()[0]
    owners = course.owners.all()
    if 0 == len(owners):
        groupnames = ["Admin", "Author", "View"]
        user.groups.clear()
        for groupname in groupnames:
            group = Group.objects.get(name=groupname)
            user.groups.add(group)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save()
        course.owners.add(user)
        course.save


class ActivateAndReset(FormView):
    """
    View for user activation and password reset. Adds user to group Student.
    """

    template_name = "registration/set_password.html"
    success_url = reverse_lazy("login")

    def get_form(self):
        # print("SELF KWARGS IN ACTIVATE AND RESET", self.kwargs)
        user = self.kwargs.get("user", None)
        # groups = list( user.groups.values_list('name',flat = True)  )
        # rint("GROUPS = %s " % groups )
        studentgroup = Group.objects.get(name="Student")
        user.group = [studentgroup]
        user.save()

        return SetPasswordForm(user, **self.get_form_kwargs())

    def form_valid(self, form):
        super().form_valid(form)
        form.save()
        try:
            group = Group.objects.get(name="Student")
            group.user_set.add(self.kwargs["user"])
        except ObjectDoesNotExist:
            pass
        # logger.info("KWARGS = %s " % self.kwargs)
        self.kwargs["user"].is_active = True
        self.kwargs["user"].save()
        # logger.info("Added and activated user " + str(self.kwargs['user']))
        user = User.objects.get(username=self.kwargs["user"])
        if is_anonymous_student(user):
            if User.objects.filter(username=user.email).exists():
                messages.add_message(self.request, messages.ERROR, "EMAIL %s ALREADY EXISTS" % user.email)
                response = redirect(reverse("login"))
                return response

            user.username = user.email
            user.email
            ag = Group.objects.get(name="AnonymousStudent")
            ag.user_set.remove(user)
            user.save(update_fields=["username", "email"])
            user.email
            if settings.ESCALATE_FIRST_ANONYMOUS_USER_TO_ADMIN:
                make_owner_if_none_exists(user)
            messages.add_message(
                self.request, messages.SUCCESS, "Password is now set, please login as %s." % user.email
            )
            r = self.request
            response = redirect(reverse("login"))
            lang = r.COOKIES.get("lang", settings.LANGUAGE_CODE)
            for cookie in r.COOKIES:
                response.delete_cookie(cookie)
            response.set_cookie(key="username", value=user.email, secure=True, samesite=settings.SAMESITE)
            response.set_cookie(key="lang", value=lang, secure=True, samesite=settings.SAMESITE)
        else:
            self.kwargs["user"]
            messages.add_message(
                self.request, messages.SUCCESS, "Password is now set, please login as %s." % self.kwargs["user"]
            )
            response = redirect(reverse("login"))
        return response


class RegisterUserNoPassword(CreateView):
    """
    View for user registration where password is given at activation time.
    """

    template_name = "register.html"
    form_class = UserCreateFormNoPassword
    success_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        ctx["course"] = CourseSerializer(course).data
        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        super().form_valid(form)
        msg_body = "Registration is almost complete. Check your inbox (or spam folder) for activation mail in order to set a password and possibly spam folder)."
        messages.add_message(
            self.request,
            messages.SUCCESS,
            msg_body,
        )
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        return redirect(reverse("login") + course.course_name)


class RegisterUserDomain(CreateView):
    """View for user registration by domain.

    Password is given at activation time and the email is locked to specific domains.

    """

    template_name = "register.html"
    form_class = UserCreateFormDomain
    success_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        # print("KWARGS = ", kwargs)
        ctx = super().get_context_data(**kwargs)
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        ctx["domains"] = course.get_registration_domains()
        ctx["course"] = CourseSerializer(course).data
        return ctx

    def get_form_kwargs(self):
        # print("GET FORM KWARGS" , self.kwargs)
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        # print("FORM VALID " , self.kwargs )
        super().form_valid(form)
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        return redirect(reverse("login", kwargs=dict(course_name=course.course_name)))


@api_view(["GET", "POST"])
@xframe_options_exempt  # NECESSARY TO KEEP FROM CRASHING IN CANVAS FRAME
def health(request, subdomain="", username="", **kwargs):
    subdomain, db = get_subdomain_and_db( request );
    username = request.user
    dirs = 0
    try :
        dirs  = len( os.listdir("/subdomain-data/auth/templogs/") )
    except Exception as e :
        dirs = str(e)
    #print(f"SUBDOMAIN = {subdomain} USERNAM={username} {dirs}")
    return HttpResponse(f"/health/{subdomain}/{username} {dirs} ")


@api_view(["GET", "POST"])
@xframe_options_exempt  # NECESSARY TO KEEP FROM CRASHING IN CANVAS FRAME
@cache_control(private=True, max_age=settings.MAIN_CACHE_TIMEOUT)
def login_status(request, *args, **kwargs):
    """Get login information for current user.

    Returns:
        JSON {
            username: (string)
            admin: (bool)
            groups: [string]
            }
    """
    request.headers.get("X-CSRFToken", "none")
    er = ""
    tbeg = time.time()
    key = "login-status" + str(request.session.session_key)
    # cache = caches["aggregation"]
    # response = cache.get(key)
    # if response:
    #    return Response(response)
    er = "ER_BEGIN"
    try:
        subdomain, db = get_subdomain_and_db(request)
        groups = []
        er = er + "A1 "
        dbgroups = request.user.groups.all()
        er = er + "A2 "
        for group in dbgroups:
            er = er + f"A3 {group.name}"
            groups.append(group.name)
        er = er + "A4 "
        if request.user.is_superuser:
            groups.append("SuperUser")
        er = er + "A5 "
        lti_login = request.session.get("lti_login", False)
        er = er + "A6 "
        compactview = request.session.get("compactview", request.session.get("lti_login", False))
        er = er + "A8 "
        # print(f"COURSE =  {request.session.get('course','NONE')}")
        backupstatus = {}
        dirpath = os.path.join(settings.VOLUME, subdomain, "admin_activity", request.user.username)
        tags = ["course_exercises_export", "course_export"]
        er = er + "A9 "
        # tags = os.listdir(dirpath)
        er = er + "A10 "
        student_pk = request.session.get("student_pk")
        try:
            course_pk = request.session.get("course_pk")
            course = Course.objects.using(db).get(pk=course_pk)
        except ObjectDoesNotExist:
            course = Course.objects.using(db).first()
            course_pk = course.pk
        # print(f" COURSE = {course}")
        er = er + " A11"
        owners = course.owners.all()
        user = request.user
        try:
            is_owner = request.user in owners
        except:
            is_owner = False
        for b in tags:
            path = os.path.join(dirpath, b)
            try:
                delta = time.time() - os.path.getmtime(path)
            except FileNotFoundError as e:
                delta = settings.TIME_BETWEEN_BACKUPS + 10
            if settings.TIME_BETWEEN_BACKUPS:
                backupstatus.update({b: not (is_owner and delta > float(settings.TIME_BETWEEN_BACKUPS))})
            else:
                backupstatus = {b: True}
        er = er + " A12"

        try :
            sidecar_count = get_sidecar_count(request.user.username,subdomain,exercise=None,course_pk=None)
        except :
            sidecar_count = {'sidecar_count' : -1 }



        response = {
            "subdomain": subdomain,
            "username": request.user.username,
            "user_pk": request.user.pk,
            "admin": request.user.is_staff,
            "groups": groups,
            "lti_login": lti_login,
            "compactview": compactview,
            "backupstatus": backupstatus,
            "student_pk": student_pk,
            "course_pk": course_pk,
            "sidecar_count":  sidecar_count,  ## MAKE SIDCAR COUNT WORK PROPERLY
        }
    except Exception as e:
        logger.error(
            f"LOGGED_IN ERROR user={request.user.get_username()} subdomain={get_subdomain(request)}  error_type={type(e).__name__}  erstring={er}  str(e)={str(e)} "
        )
        return Response({})
    # cache.set(key, response, settings.CACHE_LIFETIME)
    return Response(response)


@ratelimit(key="ip", rate=settings.LOGIN_RATE_LIMIT,block=False)
@never_cache
def login(request, course_name=None):
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        return render(request, "base_failed.html",{"msg": "Too many failed login attempts. Try again in a minute."})
    subdomain, db = get_subdomain_and_db(request) 
    username = request.POST.get('username','')
    if not request.user.is_staff  and caches['default'].get(username,None) == None : # get DV 
        username_ = username.encode('ascii','ignore').decode('ascii')
        caches['default'].set(username_,subdomain , 600 )
    username = request.user.username
    password = request.POST.get('password')
    if request.user.is_staff :
        settings.RATE_LIMIT = '20/m'
    if password :
        password_hash = (hashlib.md5(password.encode() ).hexdigest())[0:16]
        request.session['USER-ENCRYPTION-KEY'] = password_hash 
    ekey = request.session.get('USER-ENCRYPTION-KEY', None )


    if not settings.RUNTESTS : 
        cookiename = (f"{username}_last_login").replace('@','_')
        cookiename2 = 'last_login'
        try :
            last_login_cookie = request.COOKIES.get(cookiename,'') 
        except:
            last_login_cookie = ''
        try :
            user = User.objects.using(db).get(username=username)
            last_login_recorded = user.last_login
            if str( last_login_recorded) == str( last_login_cookie ) :
                request.session['REQUIRE-OTP'] = False
            password = str( request.POST.get('password') )
        except ObjectDoesNotExist as err:
            pass


    if os.path.exists(f"/subdomain-data/{subdomain}/message.html") :
        text = open(f"/subdomain-data/{subdomain}/message.html","r").read()
        r = HttpResponse(f"{text}")
        return r
    if settings.SUPERUSER_PASSWORD == '' :
        return render(request, "base_failed.html",{"msg": "SUPERUSER_PASSWORD MUST BE SET AS ENVIRONMENT VARIABLE"})

    try:
        referer = None
        username = None
        user_ip_address = None
        user_ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "")
        er = "1"
        if user_ip_address:
            ip = user_ip_address.split(",")[0]
            er = "2"
        else:
            ip = request.META.get("REMOTE_ADDR", None)
            er = "3"
        username = request.user.username
        er = "4"
        referer = request.META.get("HTTP_REFERER", None)
        er = "5"
    except Exception as e:
        if not username == None:
            return render(request, "base_failed.html")
    referer = request.META.get("HTTP_REFERER", None)
    if (
        referer == "https://www.edu-apps.org/" and not request.user.is_authenticated
    ):  # REDIRECT TOOL MUST POINT TO /lti/login
        messages.add_message(request, messages.ERROR, "You need to first click on OpenTA to get authenticated")
        return render(request, "base_failed.html")
    referer = request.META.get("HTTP_REFERER", "NO_REFERER")
    if "hijack" in referer:
        logger.error(f"HIJACK3 {request.user}")
        response = main(request, course_pk=1)
        return response
    if request.method == "POST":
        username = request.POST.get("username")
        if username:
            username = username.strip()
            try:
                user = User.objects.using(db).get(username=username)
                if not user.is_active:
                    messages.add_message(request, messages.WARNING, f"User {username} is marked inactive")
            except ObjectDoesNotExist:
                messages.add_message(request, messages.WARNING, f"User with username {username} does not exist ")
    """Login view.

    Returns:
        Login view unless rate limited in which case rate_limit.html
    """
    subdomain, db = get_subdomain_and_db(request)
    if not settings.RUNTESTS :
        detection = Detection(request)
        user_agent = detection.get_user_agent()
        is_mobile = detection.is_mobile(user_agent, request.headers)
        is_tablet = detection.is_tablet(user_agent, request.headers)
        if is_mobile  or is_tablet  or request.session.get("lti_login", False):
            request.session['is_computer'] = False
            request.session.set_expiry( 604800 ) # IF TABLET OR CANVAS ALLOW STAYING ON FOR A WEEK
        else :
            request.session['is_computer'] = True
            request.session.set_expiry(settings.COMPUTER_SESSION_TIMEOUT)        
        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", None) )

    try :
        staff_file = f"/tmp/{subdomain}-staffs.txt"
        if os.path.exists(staff_file ):
            fp = open(staff_file,"r")
            js = fp.read();
            fp.close()
            staffs = json.loads(js)
            #print(f"STAFFS = {staffs}")
            fp.close()
            for s in staffs :
                staff = s['fields']
                groups = staff['groups']
                del staff['groups']
                del staff['user_permissions']
                created = False
                try :
                    user, created = User.objects.using(subdomain).update_or_create(**staff)
                    for gid in groups :
                        group = Group.objects.using(subdomain).get(id=gid)
                        user.groups.add(group)
                    user.save
                except  IntegrityError as e :
                    logger.error(f" {type(e).__name__} {staff['username'] } NOT CREATED = {created} ")

            os.rename(staff_file, f"{staff_file}.bak")
            logger.error("GOT THROUGH THE WHOLE LIST")
    except Exception as e :
        logger.error(f"FAILURE TO RESURRECT STAFF  {type(e).__name__} {str(e)}")
        pass

    #if os.path.exists(f'/subdomain-data/{subdomain}/reload') :
    #    subprocess.run(['touch','./backend/settings.py'])
    #    subprocess.run(['touch','./backend/settings.py'])
    #    subprocess.run(['python','manage.py','clear_cache','--all'])
    #    os.remove(f'/subdomain-data/{subdomain}/reload')
    #    logger.error(f"RESET")
    nlogin = get_number_logged_in(subdomain)
    verify_or_create_database_connection(db)
    if ".env" in request.get_full_path():
        logger.error(
            f"LOGIN ERROR REQUEST contains .env {get_subdomain(request)} username={request.user} {request.get_full_path()} {request.META.get('REMOTE_ADDR')}  "
        )
    if course_name == None:
        course_name = request.COOKIES.get("last_course_name", None)
    course = None
    try:
        #  IF WE DISALLOW COURSE WITH SAME NAME ON CREATION, WE CAN REVERT THIS LINE
        course = Course.objects.using(db).all()[0]  # (course_name__iexact=course_name)
    except Course.DoesNotExist:
        course = Course.objects.order_by("-published", "-pk")[0]
    except Course.MultipleObjectsReturned:
        course = Course.objects.using(db).filter(course_name__iexact=course_name).order_by("-published", "-pk").last()
    except:
        messages.add_message(request, messages.ERROR, f'Database is not configured. {settings.DB_NAME}')
        return render(request, "base_failed.html")

    if not course.allow_anonymous_student and is_anonymous_student(request.user):
        messages.add_message(request, messages.ERROR, "Anonymous student not allowed")
        return render(request, "base_failed.html")

    course_data = CourseSerializer(course).data
    course_key = course.course_key

    lang = set_persistent_lang(course, request)
    if not course.pk:
        request.session["course"] = course.pk
        request.session["course_pk"] = course.pk

    if request.user.is_authenticated:
        response = main(request, course_pk=course.pk)
        response.delete_cookie("anonymoususer")
        response.set_cookie(key="lang", value=lang, secure=True, samesite=settings.SAMESITE)
        return response

    # if course_data['icon'] is not None:
    #    course_data['icon'] = '/' + '/'.join( course_data['icon'].split('/')[2:])
    # if not settings.RUNNING_DEVSERVER :
    #    course_data['icon'] = subdomain + course_data['icon']
    course_data["url"] = request.get_full_path()
    allow_anonymous = course.allow_anonymous_student
    # try:
    #    tst = Group.objects.get(name='AnonymousStudent')
    #    allow_anonymous = True
    # except ObjectDoesNotExist:openta-latest-d86f8b677-4gjss
    #    allow_anonymous = False
    try :
        dirs = os.listdir("/subdomain-data/auth/templogs/") 
        activity_all = len( dirs )
        cdirs = [ i for i in dirs if subdomain in i ]
        activity = len( cdirs)


    except Exception as e :
        activity = 0 
        activity_all = 0


    cpu_usage = psutil.cpu_percent(interval=1)  # interval in seconds
    extra = {
        "course": course_data,
        "openta_version": settings.OPENTA_VERSION,
        "course_name": course.course_name,
        "allow_anonymous": allow_anonymous,
        "nlogin": nlogin,
        "activity_all": activity_all, 
        "activity" : activity, 
        "cpu_usage": cpu_usage,
    }
    if "anonymoususer" in request.COOKIES:
        username = request.COOKIES.get("anonymoususer")
        extra["anonymous_user"] = username
    if "username" in request.COOKIES:
        extra["username"] = request.COOKIES.get("username")
    if not getattr(request, "limited", False) or settings.RUNNING_DEVSERVER:
        context = {"extra_context": extra}
        user = request.user
        try :
            response = LoginView.as_view(**context)(request)
        except  Exception as e :
            logger.error(f"LOGIN ERROR CAUGHT  {request.user} {subdomain} {type(e).__name__} {str(e)}")
            return render(request, "base_failed.html")
        if response.status_code == 302:
            try :

                if request.user.is_staff:
                    student_username = f"student-{request.user.id}"
                    student_user, created = User.objects.using(db).get_or_create(username=student_username)
                    if created:
                        group = Group.objects.using(db).get(name="Student")
                        student_user.groups.add(group)
                        opentauser, _ = OpenTAUser.objects.using(db).get_or_create(user=student_user)
                        opentauser.courses.add(course)
                        student_user.is_active = True
                        opentauser.save()
                        student_user.save()
            except Exception as err :
                logger.error(f"FAILED TO hijack IN FOR STUDENT-VIEW-USER for {request.user}")
                logger.error(f"FAILED TO hijack IN FOR STUDENT-VIEW-USER for {request.user} {student_username}")
                messages.add_message(request, messages.ERROR, "Hijack failed; try again; if problems persist alert admin ")
                return render(request, "base_failed.html")

        headers = request.headers
        # print(f'HEADERS = {headers}')
        cookies = request.COOKIES.get("csrftokenopenta", None)
        if cookies == None and not settings.RUNNING_DEVSERVER and not headers.get("Sec-Fetch-Dest", None) == "document":
            agent = request.META.get("HTTP_USER_AGENT", "no-agent")
            # response = csrf_failure(request,f"unknown cookie failure0. headers = {headers} ")
            # return response
            if "Safari" in agent:
                response = csrf_failure(
                    request,
                    f"CSRF cookie is not set; make sure third-party cookies are allowed, at least from [.*]instructure.com or canvas.gu.se . If using safari or IE , you may have to turn off cross-site tracking protection. If you don't want to do that, use another browswer with more fine-grained security.    ",
                )
            else:
                response = csrf_failure(
                    request,
                    f"the CSRF cookie is not set; make sure third-party cookies are allowed, at least from [.*]instructure.com or canvas.gu.se.   ",
                )

            return response
        # if not 'x-csrftoken' in headers :
        #    response = csrf_failure(request,reason=f"unknown cookie failure1. headers = {headers} cookies = {cookies}")
        #    return response
        # if headers.get('x-csrftoken',None) == None :
        #    response = csrf_failure(request,reason=f"unknown cookie failure2. headers = {headers} cookies = {cookies} ")
        #    return response

        if request.method == "POST":
            # CAPTURE FAILED POST REQUESTS AND CHECK
            # IF THERE I A SAVED PASSWORD FOR THE USER
            # IN THE OPENTASITES DATABASE
            # IF SO SWITCH TO THAT

            # print("POST")
            username = request.POST.get("username")
            if username :
                username = username.strip()
            password = request.POST.get("password")
            if password :
                password = password.strip()

            if response.status_code == 200:
                # print(f"STATUS CODE 200")
                subdomain, db = get_subdomain_and_db(request)
                if username == "super":
                    user = User.objects.using(db).get(username="super")
                    if not user.check_password(settings.SUPERUSER_PASSWORD):
                        messages.add_message(request, messages.WARNING, "password for super has been changed")
                        user.set_password(settings.SUPERUSER_PASSWORD)
                        user.save()
                        # print("USER SAVED")
                opentasite_exists = False
                superusers  = []
                if 'opentasites' in settings.INSTALLED_APPS :
                    from opentasites.models import OpenTASite
                    try:
                        o = OpenTASite.objects.using("opentasites").get(subdomain=subdomain, course_key=course_key)
                        if "superusers" in o.data:
                            superusers = o.data["superusers"]
                        else:
                            superusers = []
                        if "friends" in o.data.keys():
                            friends = o.data["friends"]
                        else:
                            friends = []
                        opentasite_exists = True
                    except Exception as e:
                        friends = []
                        superusers = []
                        logger.error(f"ERROR_IN_OPENTASITE {type(e).__name__} {str(e)}")
                target_users = User.objects.using(db).filter(username=username)
                if target_users.count() == 1:
                    target_user = target_users[0]
                    target_email = target_user.email
                    site_password = [item["password"] for item in superusers if item["email"] == target_email]
                    if len(site_password) == 1:
                        site_password = site_password.pop()
                        ck = check_password(password, site_password)
                        if ck:
                            messages.add_message(
                                request,
                                messages.SUCCESS,
                                f"The password, which is encrypted (!)  will be reset to that from the sites manager. Try again! ",
                            )
                            target_user.password = site_password
                            target_user.save()
                else:
                    target_users = User.objects.using(db).filter(email=username)
                    userlist = " or ".join([item.username for item in target_users])
                    if len(userlist) > 0:
                        messages.add_message(request, messages.SUCCESS, f" Your login is {userlist}")
                if opentasite_exists:
                    friend_emails = [item["email"] for item in friends]
                    if username in friend_emails:
                        site_password = [item["password"] for item in friends if item["email"] == username][0]
                        ck = check_password(password, site_password)
                        if ck:
                            target_user = create_new_guest_user(request, username, course, site_password)
                            messages.add_message(
                                request,
                                messages.SUCCESS,
                                f"You will be let in as friend of {o.creator}. Try  loggin in again",
                            )
                        else:
                            messages.add_message(
                                request,
                                messages.SUCCESS,
                                f"You will be let in as friend of {o.creator} with the same password you logged into manager: Try again",
                            )
                try:
                    Invitation = get_invitation_model()
                    is_invited = Invitation.objects.using(db).filter(email=username).count() == 1
                    if is_invited:
                        messages.add_message(
                            request, messages.SUCCESS, f"Your password was in the invitation message you received."
                        )
                except Exception as e:
                    logger.error(f" INVITATIONS FAILED {type(e).__name__} {str(e)}")

    else:
        response = render(request, "rate_limit.html", context={"rate": "5 times per 30 seconds"})
    try:
        tst = [ i for i in [f"{username}", request.user.username , extra.get('username','') ] if len(i) > 1 ]
        if  tst :
            username_ = tst[0]
            cookiename = ( f"{username_}_last_login" ).replace('@','_')
        else :
            cookiename = 'last_login'
        cookiename2 = 'last_login'


        for cookie in request.COOKIES:





            if not cookie in ["Path", ""]  and not '_last_login' in cookie :
                response.delete_cookie(cookie)
        response.set_cookie(key="lang", value=lang, secure=True, samesite=settings.SAMESITE)
    except Exception as e:
        if not request.user.is_authenticated:
            return Response({}, status.HTTP_403_FORBIDDEN)
        response = csrf_failure(request, "unknown cookie failure. Try reloading webpage and/or deleting all cookies.")
        logger.error(
            f"ERROR: LOGIN_LOGOUT_COOKIE_FAILURE-573  {settings.SUBDOMAIN} {request.user} {type(e).__name__} {str(e)} "
        )
        return response

    agent = request.META["HTTP_USER_AGENT"]
    if ("bingbot" in agent) or ("facebookexternalhit" in agent):
        return Response({}, status.HTTP_403_FORBIDDEN)

    if not settings.RUNNING_DEVSERVER:
        try:
            request.META["CSRF_COOKIE"]
        except Exception:
            if not request.user.is_authenticated:
                return redirect("/")
            if is_anonymous_student(request.user) and not course.allow_anonymous_student:
                return HttpResponseNotFound("<h3>Anonymous student disallowed </h3>")
            x = datetime.datetime.now()
            ip = request.META.get("REMOTE_ADDR", "REMOTE_ADDR NOT FOUND")
            if not is_anonymous_student(request.user) and request.user.is_authenticated:
                logger.error(
                    "%s %s CSRF FAIL for %s %s  %s %s "
                    % (x, ip, settings.SUBDOMAIN, request.user, request.get_full_path(), agent)
                )
            if "Safari" in agent:
                logger.error("CSRFB")
                response = csrf_failure(
                    request,
                    "CSRF cookie is not set; make sure third-party cookies are allowed, at least from [.*]instructure.com. If using safari or IE , you may have to turn of cross-site tracking protection. If you don't want to do that, use another browswer with more fine-grained security. ",
                )
            else:
                logger.error("CSRFC")
                response = csrf_failure(
                    request,
                    "CSRF cookie is not set; make sure third-party cookies are allowed, at least from [.*]instructure.com. ",
                )
    if request.user.is_authenticated :
        logger.error(f"SUCCEEDED LOGIN: USER {username} into {subdomain}  on IP={ip} AUTHENTICATED = {request.user.is_authenticated} ")
    else :
        logger.error(f"FAILED LOGIN: USER {username} into {subdomain}  on IP={ip} AUTHENTICATED = {request.user.is_authenticated} ")
    return response


def activate(request, username, token):
    """User activation where the password was supplied at registration time.

    Returns:
        Login view if successful, otherwise activation_failed.html.
    """
    subdomain,db = get_subdomain_and_db( request)
    try:
        key = "%s:%s" % (username, token)
        TimestampSigner().unsign(key, max_age=60 * 60 * 24 * 10)  # Valid for 2 days
        user = User.objects.using(db).get(username=username)
        user.is_active = True
        user.save()
    except (BadSignature, SignatureExpired):
        return render(request, "activation_failed.html")
    messages.add_message(request, messages.SUCCESS, "Activation successful, please login.")
    res = LoginView.as_view()(request)
    res.delete_cookie("anonymoususer")
    return res


def set_persistent_lang(course, request):
    course_languages = course.get_languages()
    if course_languages is None:
        lang = settings.LANGUAGE_CODE
    else:
        lang = request.COOKIES.get("lang", course_languages[0])

    translation.activate(lang)  # SEE https://docs.djangoproject.com/en/2.1/topics/i18n/translation/
    # request.session[translation.LANGUAGE_SESSION_KEY] = lang
    return lang


# def set_persistent_lang(course, request):
#    course_languages = course.get_languages()
#    if course_languages is None:
#        lang = 'en'
#    else:
#        lang = request.COOKIES.get('lang', course_languages[0])
#
#    translation.activate(lang)  # SEE https://docs.djangoproject.com/en/2.1/topics/i18n/translation/
#    request.session[translation.LANGUAGE_SESSION_KEY] = lang
#    return lang


def course_activate_and_reset(request, course_name, username, token):
    return activate_and_reset(request, username, token)


def activate_and_reset(request, username, token):
    """User activation with a form for choosing a password.

    Returns:
        Password form if successful, otherwise activation_failed.html.
    """
    subdomain,db = get_subdomain_and_db( request)
    try:
        key = "%s:%s" % (username, token)
        TimestampSigner().unsign(key, max_age=60 * 60 * 24 * 10)  # Valid for 2 days
    except (BadSignature, SignatureExpired):
        return render(request, "activation_failed.html")
    try:
        user = User.objects.using(db).get(username=username)
        if not is_anonymous_student(user) and user.is_active:
            messages.add_message(request, messages.WARNING, "User %s is already activated " % username)
            return render(request, "activation_failed.html")
    except User.DoesNotExist:
        messages.add_message(request, messages.WARNING, "Activating user %s which  does not exist" % username)
        return render(request, "activation_failed.html")

    return ActivateAndReset.as_view()(request, user=user)


@xframe_options_exempt  # NECESSARY TO KEEP FROM CRASHING IN CANVAS FRAME
@login_required
def view_toggle(request, course_pk=None):
    # logging.debug("VIEW TOGGLE")
    request.session["compactview"] = not request.session.get("compactview", request.session.get("lti_login", False))
    return main(request, course_pk)

def sidecar_count( request, *args, **kwargs ) :
    subdomain,db,user = get_subdomain_and_db_and_user(request)
    url = 'http://localhost:8080/sidecar_count'
    data = { 'username' : user.email }
    encoded_data = parse.urlencode(data).encode('utf-8')
    req = request.Request(url, data=encoded_data)
    try:
        with request.urlopen(req) as response:
            response_data = response.read()
            import json
            parsed_data = json.loads(response_data.decode('utf-8'))
    except Exception as e:
        logger.error(f'An error occurred: in sidecar {e}')








def launch_sidecar_new(request,*args,**kwargs) :
    next_url = request.session.get('referer',request.COOKIES.get("launch_presentation_return_url", "/") )
    logger.error(f"NEXT_URL = {request.path}")
    filter_key = request.GET.get('filter_key',None)
    subdomain,db,user = get_subdomain_and_db_and_user(request)
    if not filter_key == None :
        try :
            dbexercise =  Exercise.objects.using(db).get(exercise_key=filter_key)
            course_pk = dbexercise.course.pk
            exercise_name = dbexercise.name
            exercise_name = re.sub(r'\s+',' ', exercise_name)
        except ObjectDoesNotExist  as e :
            course_pk = 479234
            exercise_name = ''
    else :
        exercise_name = ''
    groups = list(request.user.groups.values_list("name", flat=True))
    thecsrftoken = get_token(request)
    if hasattr( settings ,'SIDECAR_URL'):
        url = settings.SIDECAR_URL
    else :
        return redirect("/" )
    t = str( int(  time.time() )).encode() ;
    if request.user.is_staff :
        groups.append('Admin')
    roles = ','.join(groups)
    if hasattr( request.user ,'email') :
        email = request.user.email
    else :
        email = ''
    uri = re.sub(r"launch_sidecar.*",'', str( request.build_absolute_uri() ) )
    referer = request.session.get('referer',uri)
    port = ':8000' if 'localhost' in settings.OPENTA_SERVER else ''
    server = f"{settings.HTTP_PROTOCOL}://{subdomain}.{settings.OPENTA_SERVER}{port}"
    filter_key_ = json.dumps( {filter_key: exercise_name})
    data = {
            'destination_url' : url,
            'lti_message_type': 'basic-lti-launch-request',
            'lti_version': 'LTI-1p0',
	        'subdomain':  str( subdomain),
            'resource_link_id': 'resourceLinkId',
            'resource_link_title': subdomain,
	        'custom_canvas_login_id': str( user.username),
	        'lis_person_name_contact_email_primary': email,
            'thecsrftoken' : str( thecsrftoken),
	        'roles': roles,
            'oauth_consumer_key': '889d570f472',
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': t,
            'oauth_version': '1.0',
            'filter_key' : filter_key_,
            'referer' : str( referer ),
            'filter_title' : str( exercise_name ),
            'category_selected' : 'All',
            'server' : server,
            'course_pk' : course_pk,
            'oauth_secret' : settings.OAUTH_SECRET,
        };
    #print(f"LAUNCH_DATA = {data}")
    #response = render(request, 'post_redirect.html', data )
    response = render(request, 'launch_tool.html', data )
    #logger.error(f"RESPONSE CONTENT = {response.content}")
    #for header, value in response.headers.items():
    #    logger.error(f'  {header}: {value}')
    return response


def test500(request):
    raise RuntimeError("test500 failure")


def get_number_logged_in(subdomain):
    ca = caches["aggregation"]
    keypat = f"logged-in-{subdomain}-*"
    ca.delete_pattern("logged-in-*-")  # hack to get rid of spurious cache key
    keys = ca.keys(keypat)
    return len(keys)


def user_has_insecure_password(user, db):  # THIS WAS EXTREMELY SLOW SO USE CACHING
    if user.is_anonymous:
        return True
    tbeg = time.time()
    s = db + user.username
    if hasattr(user, "password"):
        s = s + str(user.password)
    key = (hashlib.md5(s.encode()).hexdigest())[0:7]
    cache = caches["aggregation"]  # USE aggregation cache to avoid race with default cache
    rc = cache.get(key)
    if not rc == None:
        return rc
    r = user.check_password(user.username)
    if user.email:
        r = r or user.check_password(user.email)
    if settings.USE_INVITATIONS:
        from invitations.models import Invitation  # REMOVED_INVITATIONS

        try:
            invite = Invitation.objects.using(db).get(email=user.email)
            ikey = invite.key
            r = r or user.check_password(ikey)
        except ObjectDoesNotExist:
            pass
        except Exception as e:
            logger.error(f"INVITATIONS UNCAUGHT EXCEPTION")
    delta = (time.time() - tbeg) * 1000
    cache.set(key, r, settings.CACHE_LIFETIME)
    return r

def get_main_etag(request, course_pk=None, exerciseKey=None, passed_subdomain=None,referer=None):
    if request.session.get('hijacked',False ):
        logger.error(f"HIJACK ATTEMPTED {request.username}")
        return False
    try :
        r = request.session;
        if r.get('is_computer',True)  :
            request.session.set_expiry(settings.COMPUTER_SESSION_TIMEOUT )        # IF COMPUTER, TERMINATE SESSION ON BROWSER CLOSE
    except  Exception as e:
        if not request.session.get("lti_login", False) :
            messages.warning(request, f"You were logged out after {settings.COMPUTER_SESSION_TIMEOUT} seconds  of inactivity  !")

    subdomain, db = get_subdomain_and_db(request)
    try :
        s = str(request.session.session_key) + str( course_pk) + str(db)
        etag = (hashlib.md5(s.encode()).hexdigest())[0:7]
    except Exception as e:
        etag = None
    return etag




@xframe_options_exempt  # KEEPS FROM CRASHING FOR PASSWSORD CHANGE
@ensure_csrf_cookie
@cache_control(private=True,max_age=180)
@etag(get_main_etag)
def main(request, course_pk=None, exerciseKey=None, passed_subdomain=None,referer=None):
    #ss = open("backend/allsettings.py","r").read()
    ##print(f"{dir(settings)}")
    #f = open("/tmp/sets.py","w")
    #for setting in dir(settings):
    #    if setting.isupper() and setting in ss :
    #        if isinstance( getattr( settings, setting), str ):
    #            f.write(f"{setting} = \"{getattr(settings, setting)}\"\n" )
    #        else :
    #            f.write(f"{setting} = {getattr(settings, setting)}\n" )
    #f.close()
    subdomain, db = get_subdomain_and_db(request)
    cachekey = request.user.username + db + 'selectedExercises'
    caches['default'].set( cachekey ,[])
    action = request.POST.get('ACTION',None)
    #request.session['selectedExercises'] = []
    #for k in request.session.keys() :
    #    print(f"K = {k}")
    hijacked =  'hijack_history' in request.session.keys()
    return_url = '/logout/?next=login'
    #referer =  "https://chalmers.instructure.com/courses/8481/external_tools/1915?display=borderless"
    if not referer == None :
        request.session['referer'] = referer
        return_url = referer
        if 'instructure' in referer :
            return_url = '/'.join( referer.split('/')[0:5] )+'/'
    if not hijacked  and not settings.RUNTESTS :
        if str( action) == 'CONTINUE-WITH-QRCODE' :
            request.session['OTP-IN-PROGRESS'] = False 
    
        if action and str( action ) == 'CANCEL-QRCODE'  :
            delete_otp_secret( request.user )
            return redirect("/" + "logout/?next=login")
    
        if request.session.get('OTP-IN-PROGRESS',False ) :
            delete_otp_secret( request.user )
            return redirect("/" + "logout/?next=login")
    


    key = "main-" + str(request.session.session_key)
    cache = caches["aggregation"]
    if exerciseKey == None :
        response = cache.get(key)
        if response:
            return response

    tbeg = time.time()
    delta = int(1000 * (time.time() - tbeg))
    referer = request.META.get("HTTP_REFERER", None)
    user = request.user
    username = user.username
    forwarded_host = request.META.get("HTTP_X_FORWARDED_HOST", None)
    hostname = request.META.get("HTTP_HOST", None)
    subdomain, db = get_subdomain_and_db(request)
    verify_or_create_database_connection(db)
    ca = caches["aggregation"]
    cachekey = f"logged-in-{subdomain}-{user.username}"
    ca.set(cachekey, "is-logged-in", 3600)
    # s = request.user.username + str( course_pk)  + db
    # etag = (hashlib.md5(s.encode()).hexdigest())[0:7]
    # ca.set(etag,

    # for key in ca.keys('logged-in*') :
    #    val = ca.get(key)
    #    exp = ca.ttl(key)
    #    print(f"key={key} val={val} {exp}")
    get_number_logged_in(subdomain)
    if not username == "":
        if not user.is_active:
            raise Http404("You are marked as inactive in the course")
        if len(list(user.groups.all())) == 0 and not request.user.username == "super":
            raise Http404("You are not assigned to a group. Contact admin")

    if request.user.username == "super":
        if not user.check_password(settings.SUPERUSER_PASSWORD):
            messages.add_message(request, messages.WARNING, "password for super has been changed")
            user.set_password(settings.SUPERUSER_PASSWORD)
            user.save()
    path = request.get_full_path()
    delta = int(1000 * (time.time() - tbeg))
    d =  os.path.join(settings.VOLUME, subdomain) 
    if os.path.exists(d) :
        os.utime( os.path.join(settings.VOLUME, subdomain) )
    else :
        return HttpResponseNotFound(f"<h1> Course {subdomain} not found </h1>")
    try:
        if (
            not settings.RUNTESTS and request.user.is_superuser and not course_pk is None
        ):  # and not request.user.username == 'super' :
            course = Course.objects.using(db).get(pk=str(course_pk))
            course_key = str(course.course_key)
            touchfile = "last_admin_activity"
            if 'opentasites' in settings.INSTALLED_APPS :
                from opentasites.models import OpenTASite
                opentasite = OpenTASite.objects.using("opentasites").get(
                    subdomain=str(subdomain), course_key=str(course_key)
                )
                data = opentasite.data
            else :
                data = course.data
            if isinstance( data , str ):
                description = data
            else :
                description = data.get("description", "")
            if description == "":
                addurl = f"https://{subdomain}.{settings.SERVER}/{settings.ADMINURL}opentasites/opentasite/"
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        f"A course description is missing. As soon as possible go to  {addurl}   and add a description. It is seen on the login page when the info icon is clicked. "
                    ),
                )
        elif request.user.is_staff or request.user.is_superuser:
            touchfile = "last_admin_activity"
        else:
            touchfile = "last_student_activity"
        fname = os.path.join(settings.VOLUME, subdomain, touchfile)
        if os.path.exists(fname):
            os.utime(fname, None)
        else:
            dname = os.path.join(settings.VOLUME, subdomain)
            if os.path.exists(dname):
                open(fname, "a").close()
            else:
                logger.error(f"LOGIN_ATTEMPT_FAILED_1  {subdomain} {path} ")
                return HttpResponseNotFound(f"<h1> Course {subdomain} not found </h1>")

    except Exception as e:
        logger.error(
            f"LOGIN_ATTEMPT_FAILED_2  subdomain={subdomain} path={path} type={type(e).__name__} error={str(e)}  traceback={traceback.format_exc()}"
        )
        messages.add_message(request, messages.WARNING, "OpenTASite is not yet defined")
        # return HttpResponseNotFound(f"<h1> Course {subdomain} not found </h1>")

    delta = int(1000 * (time.time() - tbeg))
    if referer == None and not (forwarded_host == hostname) and (not user.is_authenticated):
        path = request.get_full_path()
        if not settings.RUNTESTS and not (path == "/" or path == ""):
            x = datetime.datetime.now()
            ip = request.META.get("REMOTE_ADDR", None)
            msg = f"{x} REFERER_IS_NONE = ip={ip} hostname={hostname} user={request.user} forwarded_host={forwarded_host} path=>{path}<"
            logger.error(msg)
            if path.find("?") > 0:
                if settings.DEBUG:
                    return HttpResponse(f"<h1> Query parameter disallowed  in {path} </h1>")
                else:
                    msg = f"{x} REFERER_IS_NONE and path contain query ip={ip} hostname={hostname} user={request.user} forwarded_host={forwarded_host} path=>{path}<"
                    with open(f"{settings.VOLUME}/CACHE/requests.txt", "a+") as f:
                        f.write(msg + "\n")
                        f.write(f"{x} REFERER REQUEST={vars(request)}\n")
                    raise Http404("Not authorized")
            elif not user.is_authenticated :
                from_sidecar_session =  len( path.split('/') ) == 4 
                messages.add_message(request, messages.WARNING, 'Your OpenTA session expired; log in again ')
                if from_sidecar_session :
                    return redirect('/')

    """The main frontend view.

    Returns:
        The frontend app in base_main.html if authorized, otherwise login screen.
    """

    delta = int(1000 * (time.time() - tbeg))
    # print(f"MAIN4  {delta}")
    if request.get_full_path().find("?") > 0:
        if settings.DEBUG:
            return HttpResponse(f"<h1> Query parameter disallowed  in {request.get_full_path()} </h1>")
        else:
            raise Http404("Not authorized")
        # return HttpResponse(f'<h1> Query parameter disallowed  in {request.get_full_path()} </h1>')
    # print("A1  %s " % ( time.time() - tbeg ) )
    # logger.error(f"MAIN REQUEST USER = {request.user.username}")
    subdomain, db = get_subdomain_and_db(request)
    # logger.error(f"SUBDOMAIN = {subdomain}" )
    if not (subdomain == "localhost" or subdomain == "openta"):
        if not subdomain == settings.SUBDOMAIN:
            logger.debug(
                f"RACE CONDITION CAUGHT subdomain not equal to settings.SUBDOMAIN {subdomain} {settings.SUBDOMAIN} {settings.DB_NAME} {request.user}"
            )
            settings.SUBDOMAIN = subdomain
            settings.DB_NAME = subdomain
    if passed_subdomain:
        if not passed_subdomain == settings.SUBDOMAIN:
            logger.debug(
                f"RACE CONDITION CAUGHT passed_subdomain {subdomain} {passed_subdomain} {settings.SUBDOMAIN} {settings.DB_NAME} {request.user}"
            )
            settings.SUBDOMAIN = passed_subdomain
            settings.DB_NAME = passed_subdomain

    delta = int(1000 * (time.time() - tbeg))
    # print(f"MAIN4  {delta}")

    if "anonymoususer" in request.COOKIES:
        username = request.COOKIES.get("anonymoususer")
        user = User.objects.using(db).get(username=username)
    else:
        user = request.user

    ######################
    delta = int(1000 * (time.time() - tbeg))
    if not settings.RUNTESTS :
        password_reset = request.session.get('RESET-PASSWORD', False )
        if password_reset :
            return redirect("/" + "pw_change/")
    if not user.username == "super":
        A = "1"
        try:
            # if  is_anonymous_student( user )  and user.groups.count()  == 1 :
            u = user_has_insecure_password(user, subdomain)
            if hasattr(request.user, "email"):
                A = A + "2"
                email = request.user.email
                A = A + "3"
                if settings.USE_INVITATIONS:
                    A = A + "4"

                    try:
                        A = A + "5"
                        invite = Invitation.objects.using(db).get(email=email)
                        A = A + "6"
                        invite.key
                        A = A + "7"
                        # if user.check_password( key )  or user.check_password( request.user.username ) :
                        if u:
                            messages.add_message(request, messages.WARNING, "Your password must be changed")
                            return redirect("/" + "pw_change/")
                        A = A + "8"
                    except Invitation.DoesNotExist:
                        A = A + "9"
                    except Exception as e:
                        logger.error(f"INVITATIONS FAILED ERROR {type(e).__name__} {A}")
                A = A + "a"
                # if user.check_password( request.user.email )  or user.check_password( request.user.username ) :
                if u:
                    messages.add_message(request, messages.WARNING, "Your insecure password must be changed")
                    return redirect("/pw_change/")
                A = A + "b"
        except Exception as e:
            logger.error(f"{type(e).__name__} {str(e)} {A} Error E1291153 {traceback.format_exc()}")
        try:
            if not user.is_authenticated and not is_anonymous_student(user):
                res = redirect(request.get_full_path() + "login/")
                return res
        except ImproperlyConfigured:
            logger.error(f"IMPROPERLY CONFIGURED")
            messages.add_message(request, messages.ERROR, "The course %s does not exist" % settings.DB_NAME)
            return render(request, "base_failed.html")
        # print("A3  %s " % ( time.time() - tbeg ) )
        # try:
        #    if user.check_password( request.user.email ) :
        #        messages.add_message(request,messages.WARNING,"Password must be changed from email") )
        # except:
        #    pass

    delta = int(1000 * (time.time() - tbeg))
    # print(f"MAIN6  {delta}")
    if course_pk is None or course_pk == 0 :
        course_pk = request.session.get("course_pk")

    ################

    # print("A3b  %s " % ( time.time() - tbeg ) )

    try:
        if course_pk is not None:
            course = Course.objects.using(db).get(pk=course_pk)
        else:
            if Course.objects.count() == 0:
                messages.add_message(request, messages.WARNING, "No courses yet")
                return redirect(reverse("login"))
            course = Course.objects.using(db).order_by("-published", "-pk")[0]
            course_pk = course.pk
    except ObjectDoesNotExist:
        messages.add_message(request, messages.WARNING, "Course requested does not exist ")
        return redirect(reverse("login"))

    delta = int(1000 * (time.time() - tbeg))
    # print(f"MAIN7  {delta}")

    # print("A3c  %s " % ( time.time() - tbeg ) )
    allow_anonymous = course.allow_anonymous_student
    if not course.published and not user.is_staff:
        messages.add_message(request, messages.ERROR, "The course is or has just been unpublished")
        return render(request, "base_failed.html")
    lang = set_persistent_lang(course, request)
    # print("A4  %s " % ( time.time() - tbeg ) )

    # #print("IS HIJACKED", request.session.get('hijacked', False))
    if not request.user.is_staff :
        enrolled = int(course_pk) in enrollment(user)
        published_and_enrolled = course.published and enrolled
    else :
        enrolled = True
        published_and_enrolled = True
    msg = ""
    if not enrolled:
        msg = "Not enrolled in course"
        return render(request, "base_failed.html",{"msg": "Your are not enrolled."})
    if not course.published:
        return render(request, "base_failed.html",{"msg": "The course is not published."})
    # logging.debug("MSG = %s " % msg )
    if user.groups.filter(name="Student").exists() and not published_and_enrolled and not user.username == "student":
        try:
            mycourse = (Course.objects.get(pk=enrollment(user)[0])).course_name
            messages.add_message(request, messages.WARNING, msg)
            return redirect("/logout/" + mycourse + "/")
        except:
            messages.add_message(request, messages.WARNING, "Not enrolled!")
            return redirect("/logout/" + course.course_name + "/")

    # logging.debug("GET COURSE SERIALIZER")
    # logger.info("A5  %s " % ( time.time() - tbeg ) )

    delta = int(1000 * (time.time() - tbeg))

    user_ip_address = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if user_ip_address:
        ip = user_ip_address.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", None)
    safe_ips = get_safe_ips( user )
    if not settings.RUNTESTS  and not ip in safe_ips  and not request.session.get("lti_login", False):
        require_otp =  not hijacked  and request.session.get('REQUIRE-OTP', True )  #
        if settings.NO_OTP_FOR_SUPER and username == 'super' :
            require_otp = False
        if ( not request.session.get('OTP-VALID',False )   ) and settings.USE_OTP and require_otp :
            return redirect("/" + "otp_validate/")
    course_data = CourseSerializer(course).data
    help_url = getattr(settings, "HELP_URL", "")
    new_folder = getattr(settings, "NEW_FOLDER", "")
    trash_folder = getattr(settings, "TRASH_FOLDER", "")
    use_stars = getattr(settings, "USE_STARS", "")
    chunk_size = getattr(settings, "CHUNK_SIZE", 5 * 1024 * 1024 )
    source_url = 'https://github.com/opentaproject/openta-public'
    answer_delay = getattr(settings, "ANSWER_DELAY", "0")
    use_vite = getattr(settings, "USE_VITE", False)
    use_sidecar = getattr( settings, "USE_SIDECAR", False )
    sidecar_url = getattr(settings, 'SIDECAR_URL','http://localhost:8080')
    getattr(settings, "RUNNING_DEVSERVER", False)
    adminurl = getattr(settings, "ADMINURL", "administration")
    env_source = getattr(settings, "ENV_SOURCE", "views.py")
    adobe_id = getattr(settings, "ADOBE_ID", "")
    #print(f"CHATGPT IN SETTINGS ", settings.USE_CHATGPT )
    use_chatgpt = getattr(settings,"USE_CHATGPT",False)
    use_bugreport = getattr(settings,"USE_BUGREPORT",False) 
    use_mathpix = getattr(settings,"USE_MATHPIX",False)
    subdomain = settings.SUBDOMAIN
    student_username = f"student-{request.user.pk}"
    if not settings.RUNTESTS:
        try:
            s = User.objects.using(subdomain).get(username=student_username)
            student_pk = s.pk
        except ObjectDoesNotExist:
            student_pk = None
        except Exception as e:
            logger.error(f"ERROR in student_pk = {type(e).__name__}")
            student_pk = None
    else:
        student_pk = None
    # request.session['student_pk'] = student_pk
    # request.session['course_pk'] = course_pk

    # print("VIEWS: NEW_FOLDER = ", new_folder)
    # print("LANGUAGE_CODE = %s " % settings.LANGUAGE_CODE)
    # print("exerciseKey = %s " % exerciseKey )
    # print("ALLOW_ANONYMOUS = %s " % allow_anonymous)
    delta = int(1000 * (time.time() - tbeg))
    # print(f"MAIN9  {delta}")
    use_devtools = getattr(settings, "USE_DEVTOOLS", False)
    permissions = user.get_group_permissions()
    view_xml = user.has_perm("exercises.view_xml")
    if view_xml :
        user_permissions = "view_xml";
    else :
        user_permissions = ""
    #logger.error(f"USE_BUGREPORT IN VIEWS {use_bugreport}")
    #logger.error(f"USE_CHATGPT IN VIEWS {use_chatgpt}")
    extra = dict(
        course=course_data,
        timezone=settings.TIME_ZONE,
        help_url=help_url,
        new_folder=new_folder,
        trash_folder=trash_folder,
        use_stars=use_stars,
        language_code=settings.LANGUAGE_CODE,
        chunk_size=chunk_size,
        exerciseKey=exerciseKey,
        openta_version=settings.OPENTA_VERSION,
        username=user.username,
        allow_anonymous=allow_anonymous,
        subdomain=subdomain,
        use_devtools=use_devtools,
        adminurl=adminurl,
        use_vite=use_vite,
        student_pk=student_pk,
        adobe_id=adobe_id,
        env_source=env_source,
        course_pk=course_pk,
        answer_delay=answer_delay,
        user_permissions=user_permissions,
        use_sidecar=use_sidecar,
        sidecar_url=sidecar_url,
        return_url=return_url,
        use_mathpix=use_mathpix,
        use_bugreport=use_bugreport,
        use_chatgpt=use_chatgpt,
        source_url=source_url,
    )
    # logging.debug('PERSISTENT LANG =  %s' % lang )
    response = render(request, "base_main.html", context=extra)
    # response.set_cookie(key='django_language',value=lang)
    # print("A6  %s " % ( time.time() - tbeg ) )
    if not settings.RUNTESTS :
        x = request.user.last_login
        MAX_AGE = settings.OTP_BYPASS_MAX_AGE
        cookiename = ( f"{username}_last_login").replace('@','_')
        response.set_cookie(key=cookiename,value=x, max_age=MAX_AGE , httponly=True, secure=True , samesite=settings.SAMESITE )
    if settings.CSRF_COOKIE_NAME:
        response.set_cookie(key="csrf_cookie_name", value=settings.CSRF_COOKIE_NAME, samesite=settings.SAMESITE)
    if request.session.get("launch_presentation_return_url", None):
        response.set_cookie(
            key="launch_presentation_return_url",
            value=request.session.get("launch_presentation_return_url", None),
            path="/",
            samesite=settings.SAMESITE
        )

    delta = int(1000 * (time.time() - tbeg))
    # print(f"MAINA  {delta}")
    response.set_cookie(key="cookieTest", value="enabled", path="/", samesite=settings.SAMESITE)
    response.set_cookie(key="lang", value=lang, path="/", secure=True, samesite=settings.SAMESITE)
    if is_anonymous_student(user):
        response.set_cookie(key="anonymoususer", value=user.username, path="/", secure=True, samesite=settings.SAMESITE)
        response.delete_cookie(key="username")
    else:
        response.delete_cookie(key="anonymoususer")
        response.set_cookie(key="username", value=user.username, path="/", secure=True, samesite=settings.SAMESITE)
    # print("RETURN RESPONSE  %s " % str( response) )
    # print("A7  %s " % ( time.time() - tbeg ) )

    delta = int(1000 * (time.time() - tbeg))
    # print(f"MAINB  {delta}")
    request.session["course_pk"] = course_pk
    if exerciseKey == None :
        cache.set(key, response, settings.CACHE_LIFETIME)
    return response


@ratelimit(key="user", rate="5/1m")
class RegisterByPassword(FormView):
    template_name = "registration/register_with_password.html"
    form_class = RegisterWithPasswordForm
    ratelimit_key = "ip"
    ratelimit_rate = settings.RATELIMIT_RATE

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        ctx["domains"] = course.get_registration_domains()
        ctx["course"] = CourseSerializer(course).data
        return ctx

    def form_valid(self, form):
        if getattr(self.request, "limited", False) and (not settings.RUNNING_DEVSERVER):
            return render(
                self.request,
                "register rate_limit.html",
                context={"rate": "5 times per 30 seconds"},
            )
        course = Course.objects.get(pk=self.kwargs["course_pk"])
        kwargs = {"course_pk": self.kwargs["course_pk"]}
        if course.registration_by_password and course.registration_password == form.cleaned_data["password"]:
            return redirect(
                reverse("register-with-password", kwargs=kwargs) + "register/" + course.registration_password
            )
        return redirect(reverse("register-with-password", kwargs=kwargs))


@ratelimit(key="ip", rate=settings.RATELIMIT_RATE)
def validate_and_show_registration(request, course_pk, password):
    """Register with password.

    Register user with password view that handles the form submission
    of the register with password form.
    """
    if getattr(request, "limited", False) and (not settings.RUNNING_DEVSERVER):
        return render(request, "rate_limit.html", context={"rate": settings.RATELIMIT_RATE})
    course = Course.objects.get(pk=course_pk)
    if course.registration_by_password and course.registration_password == password:
        return RegisterUserNoPassword.as_view()(request, course_pk=course_pk)
    else:
        return redirect(reverse("register-with-password", kwargs={"course_pk": course_pk}))


def password_reset_done(request):
    """Add sent success message.

    Wrapper view that adds a success message to the login screen indicating
    that a password reset mail was sent.
    """
    messages.add_message(
        request,
        messages.INFO,
        "Password reset link sent to your email " "(check your spam folder as well).",
    )
    return redirect(reverse("login"))


@ratelimit(key="ip", rate="5/1h")
def password_reset(request):
    """Password reset view asking for an email."""
    subdomain,db = get_subdomain_and_db( request )
    from_email = settings.DONT_REPLY_EMAIL
    template_name = "registration/password_reset_subject.txt"
    subject = loader.render_to_string(template_name)
    if not settings.DEBUG and getattr(request, "limited", False):
        message = (
            "If you are not receiving an reset link by email, check your spam filter or junk mail. The email was sent from "
            + "[{from_email}] "
            + " with the subject "
            + "[{subject}]"
        )
        message_format = message.format(from_email=from_email, subject=subject)
        return render(
            request,
            "rate_limit.html",
            context=dict(rate="5 " + "times per hour.", extra_message=message_format),
        )
    logger.info("PasswordResetView from %s " % from_email)
    ret = auth_views.PasswordResetView.as_view(form_class=CustomPasswordResetForm)(
            request, from_email=from_email, extra_content={"subdomain": subdomain, "user" : request.user }
    )

    return ret


def password_reset_complete(request):
    """Add success and login message.

    Wrapper view that adds a success message to the login screen after password was reset.
    """
    msg=  "Password reset successful, please login."
    if settings.USE_OTP :
        msg=  "Password reset successful, please login. Note that your 2FA must be reset alson"
    messages.add_message(request, messages.INFO, msg )
    body = request.body
    return redirect(reverse("login"))


def serve_subdomain_public_media(request, subdomain, asset):
    return serve_public_media(request, asset)


def serve_public_media(request, asset):
    """Serve public media.

    Args:
        request (HttpRequest): request
        asset (str): Asset path

    Raises:
        Http404: If unauthorized

    Returns:
        HttpResponse: Asset response

    """
    subdomain, db = get_subdomain_and_db(request)
    # if not asset.startswith('public/'):
    #    raise Http404('Not authorized')
    kwargs = {}
    kwargs["devpath"] = f"{settings.VOLUME}/{subdomain}/media/public/{asset}"
    kwargs["accel_xpath"] = f"{subdomain}/media/public/{asset}"
    kwargs["source"] = "serve_public_media"
    try:
        return serve_file(kwargs["devpath"], kwargs["accel_xpath"], **kwargs)
    except:
        raise Http404("file not found")


@xframe_options_exempt
def trigger_error(request, msg="SENTRY ERROR TRIGGERED"):
    assert 1 == 0, msg
    raise Http404("msg")


class UserLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have successfully logged out.")
        return super().dispatch(request, *args, **kwargs)


@xframe_options_exempt  # NECESSARY TO KEEP FROM CRASHING IN CANVAS FRAME
def logout(request, course_name=None, lti_status="no_lti"):
    try:
        logger.error(f"SESSION = {request.session.get('launch_presentation_return_url')}")
        return_url =  request.session.get('launch_presentation_return_url',None)
        if return_url :
            lti_status = "lti"
            next_url = return_url.split('/external_content')[0]
        else :
            next_url = request.session.get('referer','/')
        subdomain, db = get_subdomain_and_db(request)
        ca = caches["aggregation"]
        user = request.user
        cachekey = f"logged-in-{subdomain}-{user.username}"
        ca.delete(cachekey)
        if user.is_staff:
            if os.path.exists(f'/subdomain-data/{subdomain}/reload') :
                subprocess.run(['touch','./backend/settings.py'])
                subprocess.run(['touch','./backend/settings.py'])
                subprocess.run(['python','manage.py','clear_cache','--all'])
                if not 'localhost' in settings.OPENTA_SERVER :
                    subprocess.run(['supervisorctl','reload'])
                os.remove(f'/subdomain-data/{subdomain}/reload')
                logger.error(f"RESET")
            courses = Course.objects.using(db).filter(opentasite=subdomain)
            for course in courses :
                logger.error(f" LOGOUT {course}")
                sync_opentasite(course)

        # print("REQUEST %s " % str( get_current_site(request) ) )
        #next_url = request.COOKIES.get("launch_presentation_return_url", "/")  #
        #next_url = "https://chalmers.instructure.com/courses/8481"
        #next_url = request.session.get('referer',request.COOKIES.get("launch_presentation_return_url", "/") )
        if not lti_status == 'lti' and is_anonymous_student(request.user):
            # print("LOGOUT ANONYMOUS STUDENT ")
            next_url = "lti/index/"
            response = HttpResponseRedirect(next_url)
            request.session.modified = True
            if settings.DELETE_ANONYMOUS_STUDENT_ON_LOGOUT:
                request.user.delete()
                for cookie in request.COOKIES:
                    # if not cookie == 'lang' :
                    response.delete_cookie(cookie)
            response.set_cookie(key="last_course_name", value=course_name, secure=True, samesite=settings.SAMESITE)  # HAVE THIS FOR NEXT LOGIN
            syslogout(request)  # Always do syslogout if request is from non-lti-window
            return response
        if lti_status == "no_lti":
            request.session["lti_login"] = False
            request.session.modified = True
            request.session["OTP-VALID"] = False
            #if course_name == None or course_name == "":
            #    next_url = "/login"
            #else:
            #    next_url = "/login/" + course_name + "/"
            syslogout(request)  # Always do syslogout if request is from non-lti-window
            response = HttpResponseRedirect(next_url)
            response.set_cookie(key="last_course_name", value=course_name, secure=True, samesite=settings.SAMESITE)  # HAVE THIS FOR NEXT LOGIN
            return response
        else:
            logger.error(f"LOGOUT WITH NEXT_URL = {next_url}")
            #next_url = request.COOKIES.get(
            #    "launch_presentation_return_url", "/"
            #)  # GET FROM COOKIE IN C̄ASE SESSION IS DEAD
            response = HttpResponseRedirect(next_url)
            request.session["lti_login"] = False
            response.set_cookie(key="last_course_name", value=course_name, secure=True, samesite=settings.SAMESITE)  # HAVE THIS FOR NEXT LOGIN
            request.session.modified = True
            syslogout(request)  # Always do syslogout if request is from non-lti-window
            response = HttpResponseRedirect(next_url)
            return response
    except Exception as e:
        response = HttpResponseRedirect("/")
        for cookie in request.COOKIES:
            response.delete_cookie(cookie)
        logger.error(f"Error logging out {type(e).__name__} {str(e) }")
        return response


@xframe_options_exempt
@api_view(["GET", "POST"]) #### TOCHECK
@never_cache
def ratelimit_error(request, exception=None):
    logger.error(f"RATELIMIT EXCEPTION = {exception} {request.user} {request.get_full_path() }  ")
    return Response({}, status=429)


@xframe_options_exempt
@api_view(["GET", "POST"]) #### TOCHECK
def csrf_failure(request, reason=""):
    x = datetime.datetime.now()
    ip = request.META["REMOTE_ADDR"]
    response = render(request, "csrf_failure.html", {"msg": reason})
    try:
        if not is_anonymous_student(request.user):
            logger.error(
                f"{x}  {ip} EXERCISE-CSRF-FAIL-205 {settings.SUBDOMAIN}  user={request.user} path={request.get_full_path()} reason={reason} "
            )
    except Exception as e:
        logger.error(
            f" SUSPICIOUS_CSRF_FAIL {type(e).__name__ } {x}  {ip} EXERCISE-CSRF-FAIL-205b {settings.SUBDOMAIN}  path={request.get_full_path()} reason={reason} "
        )
        response = render(request, "csrf_failure.html", {"msg": reason})
    return response


@csrf_exempt
def frontend_log(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        logger.error('FRONTEND_ERROR frontend_log: BAD JSON')
        return JsonResponse({'detail': 'Bad JSON'}, status=400)
    level = str(data.get('level','info')).lower()
    message = data.get('message','')
    context = data.get('context',{})
    return JsonResponse({'ok': True})
