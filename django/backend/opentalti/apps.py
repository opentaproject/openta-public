from django.apps import AppConfig
from users.models import OpenTAUser
from django.contrib.auth.models import User, Group
from course.models import Course
from exercises.modelhelpers import enrollment
from pylti.common import LTIException
from .admin import (
    user_stub_from_request,
    default_username,
    immutable_user_id,
    lti_names,
    lti_keys,
    verify_request,
)
import re
import time
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def create_new_user(request, username, course):
    assert course.pk >= 0
    assert not (username == None)
    assert not (User.objects.filter(username=username).exists())
    user = User.objects.create(username=username)
    roles = request.POST.get("roles", "Student")
    opentauser = OpenTAUser.objects.create(user=user)
    user_stub = user_stub_from_request(request, course)
    for name in lti_names:
        setattr(opentauser, name, getattr(user_stub, name))
    opentauser.lti_roles = user_stub.lti_roles
    opentauser.immutable_user_id = user_stub.immutable_user_id
    course_pk = user_stub.courses
    if opentauser.lis_person_contact_email_primary:
        user.email = opentauser.lis_person_contact_email_primary
    if opentauser.lis_person_name_given:
        user.first_name = opentauser.lis_person_name_given
    if opentauser.lis_person_name_family:
        user.last_name = opentauser.lis_person_name_family
    try:
        course = Course.objects.get(pk=course_pk)
    except:
        course = Course.objects.order_by("-published", "-pk")[0]
    opentauser.courses.add(course)
    user.is_active = True
    user.username = default_username(user_stub)
    groups = user_stub.groups
    for groupname in groups:
        groupname = groupname.strip()
        group = Group.objects.get(name=groupname)
        user.groups.add(group)
    if 'ContentDeveloper' in roles or 'Admin' in roles or 'Instructor' in roles:
        user.is_staff = True
    opentauser.save()
    user.save()
    return user


class OpentaltiConfig(AppConfig):
    name = "opentalti"


def get_user_username(request, course):
    immutable_user_id = get_immutable_user_id(request, course)
    if immutable_user_id is None:
        return None
    opentausers = OpenTAUser._meta.model.objects.all()
    logging.debug("GET USER_USERNAME")
    try:
        opentauser = opentausers.filter(immutable_user_id=immutable_user_id)[0]
        if course.pk not in enrollment(opentauser):
            opentauser.courses.add(course)
            opentauser.save()
        return opentauser.user.username
    except:
        return None
    # PLEASE LEAVE THIS COMMENT username = username_from_immutable_user_id(immutable_user_id)


def get_immutable_user_id(request, course):
    # scratchuser = user_stub_from_request(request,course)
    # testuser = LTIAuth.ltiauth( LTIAuth,  request)
    return immutable_user_id(user_stub_from_request(request, course))


def get_or_create_user(request, course):
    try:
        logging.debug("TRY GETTING IMMUTABLE")
        username = get_immutable_user_id(request, course)
        user = User.objects.get(username=username)
        opentauser = OpenTAUser.objects.get(user=user)
        opentauser.courses.add(course)
        opentauser.save()
    except User.DoesNotExist:
        logging.debug("USER NO EXIST")
        try:
            username = get_user_username(request, course)
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            username = get_immutable_user_id(request, course)
            user = create_new_user(request, username, course)

    return user


def course_from_request(request):
    # TODO THIS SHOULD NOT BE NECESSARY
    # TODO COURSE SHOULD BE AVAILABLE WHERE NEEDED
    # course_pk = request.META.get("PATH_INFO").split("/").pop()
    # course_pk = request.COOKIES.get('course_pk',2)
    course_pk = (request.get_full_path()).split('/')[2]
    logging.debug("COURSE FROM REQUEST RETURN COURSE_PK  " + str(course_pk))
    try:
        course = Course.objects.get(pk=course_pk)
    except:
        course = Course.objects.order_by("-published", "-pk")[0]
    return course


class LTIAuth:
    def ltiauth(self, request):
        logging.debug("LTIAUTH LTIAUTH CALLED")
        verify_request(request)
        course = course_from_request(request)  # TODO REMOVE DEPENDENCE ON REQUEST PARSE
        try:
            user = get_or_create_user(request, course)
            logging.debug("GET OR CREATE SUCCEEDED")
        except:
            raise LTIException("Authentication failed")
        return user

    def authenticate(self, request, username=None, password=None):
        logging.debug("LTIAUTH AUTHENTICATE CALLED")
        #! THIS IS CALLED BY DJANGO AUTH FOR FAILED ATTEMPT IN LOGIN SCREEN
        #! AUTHENTICATION VIA OPENTALTI SHOULD NEVER GET HERE
        #! RETURNING NONE IS NECESSARY SO FAILED ORDINARY ALSO FAILS HERE
        return None

    def get_user(self, user_pk):
        logging.debug("LTIAUTH GET_USER CALLED %s", str(user_pk))
        try:
            user = User.objects.get(pk=user_pk)
            logging.debug("USER FOUND")
            return user
        except User.DoesNotExist:
            return None
