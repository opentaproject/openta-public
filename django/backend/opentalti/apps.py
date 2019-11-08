from django.apps import AppConfig
from users.models import OpenTAUser
from django.contrib.auth.models import User, Group
from django.conf import settings
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


class OpentaltiConfig(AppConfig):
    name = "opentalti"


def create_new_user(request, username, course):
    logging.debug("CREATE NEW USER username" + str(username) + str(course))
    assert course.pk >= 0
    assert not (username == None)
    assert not (User.objects.filter(username=username).exists())
    user = User.objects.create(username=username)
    roles = request.POST.get("roles", "Learner")
    opentauser = OpenTAUser.objects.create(user=user)
    user_stub = user_stub_from_request(request, course)
    for name in lti_names:
        setattr(opentauser, name, getattr(user_stub, name))
    opentauser.lti_roles = user_stub.lti_roles
    opentauser.immutable_user_id = user_stub.immutable_user_id
    if opentauser.lis_person_contact_email_primary:
        user.email = opentauser.lis_person_contact_email_primary
    if opentauser.lis_person_name_given:
        user.first_name = opentauser.lis_person_name_given
    if opentauser.lis_person_name_family:
        user.last_name = opentauser.lis_person_name_family
    opentauser.courses.add(course)
    user.is_active = True
    user.username = default_username(user_stub)
    groups = user_stub.groups
    # CANVAS ROLES HAVE BEEN UNRELIABLE
    # SETTING THIS IN settings_opentalti FORCES ALL
    # CANVAS REGISTRATION TO BE STUDENT
    # AND OVERRIDES MUST BE DONE BY SUPERUSER
    if settings.FORCE_ROLE_TO_STUDENT:
        groups = ['Student']
    for groupname in groups:
        groupname = groupname.strip()
        group = Group.objects.get(name=groupname)
        user.groups.add(group)
    if "Admin" in groups or "Author" in groups:
        user.is_staff = True
    opentauser.save()
    user.save()
    return user


def update_user_profile(user, user_stub):
    # A LOT OF CODE DUPLICATION WITH create_new_user
    # BEFORE CONSOLIDATING, NOTE THAT ONLY THE PROFILE
    # SUBSET OF KEYS ARE UPDATED; SO BE CAREFUL
    # WITH EVENTUAL CODE CLEANUP. IN PARTICULAR
    # CERTAIN ID KEYS CANNOT BE UPDATED
    opentauser = OpenTAUser.objects.get(user=user)
    groups = user_stub.groups
    profile_keys = [
        "lti_roles",
        "lis_person_contact_email_primary",
        "lis_person_name_full",
        "lis_person_name_given",
        "lis_person_name_family",
    ]
    for name in profile_keys:
        setattr(opentauser, name, getattr(user_stub, name))
    if opentauser.lis_person_contact_email_primary:
        user.email = opentauser.lis_person_contact_email_primary
    if opentauser.lis_person_name_given:
        user.first_name = opentauser.lis_person_name_given
    if opentauser.lis_person_name_family:
        user.last_name = opentauser.lis_person_name_family
    if settings.FORCE_ROLE_TO_STUDENT:
        groups = ['Student']
    for groupname in groups:
        groupname = groupname.strip()
        group = Group.objects.get(name=groupname)
        user.groups.add(group)
        if groupname in ["Admin", "Author"]:
            user.is_staff = True
    user.save()
    opentauser.save()
    return user


def get_or_create_user(request, course):
    user_stub = user_stub_from_request(request, course)
    user = None
    try:
        opentauser = OpenTAUser.objects.get(immutable_user_id=user_stub.immutable_user_id)
        opentauser.courses.add(course)
        opentauser.save()
        user = opentauser.user
    except OpenTAUser.DoesNotExist:
        user = create_new_user(request, user_stub.immutable_user_id, course)

    if not user.is_staff:
        update_user_profile(user, user_stub)
    return user


def course_from_request(request):
    # TODO THIS SHOULD NOT BE NECESSARY
    # TODO COURSE SHOULD BE AVAILABLE WHERE NEEDED
    # course_pk = request.META.get("PATH_INFO").split("/").pop()
    # course_pk = request.COOKIES.get('course_pk',2)
    course_pk = (request.get_full_path()).split("/")[2]
    try:
        course = Course.objects.get(pk=course_pk)
    except:
        course = Course.objects.order_by("-published", "-pk")[0]
    logging.debug(" COURSE FROM REQUEST USE COURSE " + str(course))
    return course


class LTIAuth:
    def ltiauth(self, request):
        logging.debug("LTIAUTH LTIAUTH CALLED")
        verify_request(request)
        course = course_from_request(request)  # TODO REMOVE DEPENDENCE ON REQUEST PARSE
        try:
            user = get_or_create_user(request, course)
        except:
            raise LTIException("Authentication failed")
        return user

    def authenticate(self, request, username=None, password=None):
        #! THIS IS CALLED BY DJANGO AUTH FOR FAILED ATTEMPT IN LOGIN SCREEN
        #! AUTHENTICATION VIA OPENTALTI SHOULD NEVER GET HERE
        #! RETURNING NONE IS NECESSARY SO FAILED ORDINARY ALSO FAILS HERE
        return None

    def get_user(self, user_pk):
        try:
            user = User.objects.get(pk=user_pk)
            return user
        except User.DoesNotExist:
            return None
