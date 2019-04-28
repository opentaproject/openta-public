from django.apps import AppConfig
from users.models import OpenTAUser
from django.contrib.auth.models import User, Group
from course.models import Course
from pylti.common import LTIException
from .admin import user_stub_from_request, default_username, immutable_user_id, lti_names, lti_keys
import re
import time
from django.contrib import messages
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


#! PLEASE LEAVE THE FOLLOWING COMMENTED SECTION  FOR POSSIBLE USE
#!
#!def username_from_immutable_user_id(username):
#!   if username == None:
#!       return None
#!   trueusername = None
#!   immutable_user_ids = ["immutable_user_id"]
#!   try:
#!       opentausers = OpenTAUser._meta.model.objects.all()
#!       for field in immutable_user_ids:
#!           filter = field + "__exact"
#!           query = opentausers.filter(**{filter: username})
#!           if query.count() > 0:
#!               opentauser = query[0]
#!               user = opentauser.user
#!               trueusername = user.username
#!   except:
#!       return None
#!   return trueusername
#!

#def dprint(*args,**kwargs) :
#    logger.info( (",").join([*args] ) )

def dprint(*args,**kwargs) :
    txt = "OPENTALTI.APPS: "
    for value in  list( args ) :
        txt = txt + ( str(value) )
    print(txt)
    logger.info( txt)



def create_new_user(request, username , course):
    assert course.pk >= 0 
    assert not ( username  == None  )
    assert not (  User.objects.filter(username=username).exists() )
    user = User.objects.create(username=username)
    # opentauser, _ = OpenTAUser.objects.get_or_create(user=user)
    opentauser = OpenTAUser.objects.create(user=user)
    user_stub = user_stub_from_request(request,course)
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
    user.username =  default_username(user_stub)
    groups = user_stub.groups
    for groupname in groups:
        groupname = groupname.strip()
        group = Group.objects.get(name=groupname)
        user.groups.add(group)
    opentauser.save()
    return user


class OpentaltiConfig(AppConfig):
    name = "opentalti"


def get_user_username(request, course):
    immutable_user_id = get_immutable_user_id(request, course)
    opentausers = OpenTAUser._meta.model.objects.all()
    try:
        opentauser = opentausers.filter(immutable_user_id=immutable_user_id)[0]
        return opentauser.user.username
    except:
        return None
    # PLEASE LEAVE THIS COMMENT username = username_from_immutable_user_id(immutable_user_id) 


def get_immutable_user_id(request, course):
    #scratchuser = user_stub_from_request(request,course)
    # testuser = LTIAuth.ltiauth( LTIAuth,  request)
    return immutable_user_id( user_stub_from_request(request,course) )


def get_or_create_user(request, course):
    dprint("AUTHENTICATE VIA OPENTALTI get_or_create_user")
    dprint("REQUEST.SESSION", request.session.get("lti_login", "NO LOGIN DEFINED"))
    try:
        assert request.session.get("lti_login", False)
    except AssertionError:
        return None
    try:
        username = get_immutable_user_id(request, course)
        user = User.objects.get(username=username)
    except User.DoesNotExist:
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
    course_pk = request.META.get("PATH_INFO").split("/").pop()
    try:
        course = Course.objects.get(pk=course_pk)
    except:
        course = Course.objects.order_by("-published", "-pk")[0]
    return course


class LTIAuth:
    def ltiauth(self, request):
        dprint("LTIAUTH LTIAUTH CALLED")
        course = course_from_request(request) # TODO REMOVE DEPENDENCE ON REQUEST PARSE
        try:
            user = get_or_create_user(request, course)
        except:
            messages.add_message(request, messages.ERROR, "ERROR IN LTIAuth" + str(request.POST))
            raise LTIException(" LTIAuth gives None " + str(request.POST))
        return user

    def authenticate(self, request, username=None, password=None):
        dprint("LTIAUTH AUTHENTICATE CALLED")
        #! THIS IS CALLED BY DJANGO AUTH FOR FAILED ATTEMPT IN LOGIN SCREEN
        #! AUTHENTICATION VIA OPENTALTI SHOULD NEVER GET HERE
        #! RETURNING NONE IS NECESSARY SO FAILED ORDINARY ALSO FAILS HERE
        return None

    def get_user(self, user_pk):
        dprint("LTIAUTH GET_USER CALLED" + str( user_pk) )
        try:
            return User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return None
