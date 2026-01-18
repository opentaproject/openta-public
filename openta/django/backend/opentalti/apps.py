# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from django.core.cache import caches

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from pylti.common import LTIException

from .admin import default_username, lti_names, user_stub_from_request, verify_request

logger = logging.getLogger(__name__)

# class OpentaltiConfig(AppConfig):
#    name = "opentalti"


@transaction.atomic
def create_new_guest_user(request, username, course, password):
    groupname = "View"
    from utils import get_subdomain_and_db
    from users.models import OpenTAUser
    from django.contrib.auth.models import Group, User

    subdomain, db = get_subdomain_and_db(request)
    logger.error(f"CREATE NEW  GUET USER username {username}  course {course} password={password}")
    user, _ = User.objects.using(db).get_or_create(username=username)
    logger.error(f" GO ON TO  CREATE NEW USER")
    opentauser, _ = OpenTAUser.objects.using(db).get_or_create(user=user)
    user_stub = user_stub_from_request(request, course)
    for name in lti_names:
        setattr(opentauser, name, getattr(user_stub, name))
    opentauser.lti_roles = [groupname]
    opentauser.courses.add(course)
    user.is_active = True
    group = Group.objects.using(db).get(name=groupname)
    user.groups.add(group)
    user.password = password
    opentauser.save(using=db)
    user.save(using=db)
    return user


# <<<<<<< HEAD
# @transaction.atomic
# def create_new_user(request, username, course):
# =======
def create_new_user(request, username, course, olduser=None):
    from utils import get_subdomain_and_db
    from users.models import OpenTAUser
    from django.contrib.auth.models import Group, User

    # >>>>>>> Fix shared secret label in forms.py
    from utils import get_subdomain_and_db
    subdomain, db = get_subdomain_and_db(request)
    # logging.debug("CREATE NEW USER username %s, course %s", username, course)
    if course.pk == 0:
        raise LTIException("COURSE PK = 0 ")
    if username == None:
        raise LTIException("USERNAME = None ")
    if User.objects.using(db).filter(username=username).exists():
        raise LTIException("Username exists and cannot be recreated")
    user = User.objects.using(db).create(username=username)
    request.POST.get("roles", "Learner")
    opentauser = OpenTAUser.objects.using(db).create(user=user)
    try :
        user_stub = user_stub_from_request(request, course)
    except Exception as e :
        logger.error(f"USERSTUB ERROR { type(e).__name__} {str(e)} ")
        raise LTIException("ERROR 177234: Probable error in assigend roles")
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
    if "Admin" in groups or "Author" in groups and settings.FORCE_ROLE_TO_STUDENT:
        groups = ["Student"]
    for groupname in groups:
        groupname = groupname.strip()
        group = Group.objects.using(db).get(name=groupname)
        user.groups.add(group)
    if "Admin" in groups or "Author" in groups:
        user.is_staff = True
    opentauser.save(using=db)
    user.save(using=db)
    return user


def update_user_profile(user, user_stub, db):
    # A LOT OF CODE DUPLICATION WITH create_new_user
    # BEFORE CONSOLIDATING, NOTE THAT ONLY THE PROFILE
    # SUBSET OF KEYS ARE UPDATED; SO BE CAREFUL
    # WITH EVENTUAL CODE CLEANUP. IN PARTICULAR
    # CERTAIN ID KEYS CANNOT BE UPDATED
    from users.models import OpenTAUser
    from django.contrib.auth.models import Group, User

    opentauser = OpenTAUser.objects.using(db).get(user=user)
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
    if "Admin" in groups or "Author" in groups and settings.FORCE_ROLE_TO_STUDENT:
        groups = ["Student"]
    for groupname in groups:
        groupname = groupname.strip()
        group = Group.objects.using(db).get(name=groupname)
        user.groups.add(group)
        if groupname in ["Admin", "Author"]:
            user.is_staff = True
    user.save(using=db)
    opentauser.save(using=db)
    return user


@transaction.atomic
def get_or_create_user(request, course):
    from utils import get_subdomain_and_db
    from users.models import OpenTAUser

    subdomain, db = get_subdomain_and_db(request)
    # fp = open("/tmp/requests.txt",'a')
    # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # fp.write( now + ':' + str( request.body.decode('utf-8') ) )
    # fp.write("\n")
    # fp.close()
    # fp = open("/tmp/requests.txt",'a')
    # now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try :
        user_stub = user_stub_from_request(request, course)
    except Exception as e :
        raise LTIException(f" { type(e).__name__} ERROR 17557222 and {str(e)}"  )

    # fp.write( now + ': PPRINT ' + re.sub(r'\n','',plogger.debug.pformat( vars(user_stub))))
    # fp.write("\n")
    # fp.close()
    user = None
    user_exists = False
    try:
        if settings.TRUST_LTI_USER_ID and user_stub.lti_user_id:
            opentauser = OpenTAUser.objects.using(db).get(lti_user_id=user_stub.lti_user_id)
        else:
            opentauser = OpenTAUser.objects.using(db).get(immutable_user_id=user_stub.immutable_user_id)
        if not course in opentauser.courses.all():
            opentauser.courses.add(course)
            opentauser.save(using=db)
            time.sleep(1)  # sleep while saving before loggin in
        user = opentauser.user
        user_exists = True
    except ObjectDoesNotExist:
        user_exists = False
    try:
        if not user_exists:
            user = create_new_user(request, user_stub.immutable_user_id, course)
    except Exception:
        logger.error(f" ERROR CREATING OPENTAUSER FOR {request.user}  {vars( user_stub)} ")
        f1 = str(user_stub.lis_person_name_full)
        f2 = "{:<30}".format(str(user_stub.immutable_user_id))
        msg = f"Error 122: Error creating user {f1}  from the hash {f2}  .  The most likely reason is that you have two Canvas identities and have accessed OpenTA previously through another.  Alternatively your Canvas identity has changed but the username is unchanged. Either make sure you use the proper identity or else ask the course admin to change or delete the previous username. Another reason might be that you are trying to login as anonymous user but that the  AnonymousStudent group does not exist. "
        msg = f"Error 122: Error creating user >{f1}<. >{request.user.username}< >{request.user}<  User by that name already exists. If problems persist ask admin to look over the list of users  and include this entire message including the hash {f2}"
        if f1 == "Test student":
            msg = f"Error 122 ; You probably reset student in Student view in Canvas. Try again and a hash will be assiged as a name to the new test student."
        raise LTIException(msg)
    if user.is_staff:
        update_user_profile(user, user_stub, db=db)
    return user


def course_from_request(request):
    # TODO THIS SHOULD NOT BE NECESSARY
    # TODO COURSE SHOULD BE AVAILABLE WHERE NEEDED
    # course_pk = request.META.get("PATH_INFO").split("/").pop()
    # course_pk = request.COOKIES.get('course_pk',2)
    from utils import get_subdomain_and_db
    from course.models import Course

    subdomain, db = get_subdomain_and_db(request)
    logger.debug(f"REQUEST = {request.get_full_path()}")
    course_pk = (request.get_full_path()).split("/")[1]
    if course_pk:
        try:
            course = Course.objects.using(db).get(pk=course_pk)
        except ValueError as e:
            course = Course.objects.using(db).order_by("-published", "-pk")[0]
        except Exception as e:
            logger.error(
                "ERROR IN OPENTALTI type = %s string =  %s " % (type(e).__name__, str(e))
            )  # ObjectDoesNotExist:
            course = Course.objects.using(db).order_by("-published", "-pk")[0]
    else:
        course = Course.objects.using(db).order_by("-published", "-pk")[0]
    logging.debug(" COURSE FROM REQUEST USE COURSE " + str(course))
    return course


class LTIAuth:
    @transaction.atomic
    def ltiauth(self, request):
        from utils import get_subdomain_and_db
        from django.contrib.auth.models import Group, User

        logger.debug("LTI AUTH CALLED")
        subdomain, db = get_subdomain_and_db(request)
        logging.debug("LTIAUTH LTIAUTH CALLED")
        if not settings.RUNNING_DEVSERVER:
            verify_request(request)
        course = course_from_request(request)  # TODO REMOVE DEPENDENCE ON REQUEST PARSE
        try:
            with transaction.atomic():
                user = get_or_create_user(request, course)
        except Exception as e:
            raise LTIException("%s " % ("Authentication failed {0}".format(e)))
        subdomain,db = get_subdomain_and_db( request)
        username = user.username
        cache = caches['default'];
        cache.set(username,subdomain,86400)
        return user

    def authenticate(self, request, username=None, password=None):
        #! THIS IS CALLED BY DJANGO AUTH FOR FAILED ATTEMPT IN LOGIN SCREEN
        #! AUTHENTICATION VIA OPENTALTI SHOULD NEVER GET HERE
        #! RETURNING NONE IS NECESSARY SO FAILED ORDINARY ALSO FAILS HERE
        return None

    def get_user(self, user_pk):
        from django.contrib.auth.models import Group, User
        try:
            user = User.objects.get(pk=user_pk)
            return user
        except User.DoesNotExist:
            return None
