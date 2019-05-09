from django.contrib import admin
from django.apps import AppConfig
from users.models import OpenTAUser
from django.contrib.auth.models import User, Group
from course.models import Course
from pylti.common import LTIException
import hashlib
import re
import time
import logging


# Register your models here.

lti_keys = [
    "roles",
    "user_id",
    "lis_person_contact_email_primary",
    "lti_tool_consumer_instance_guid",
    "lti_context_id",
    "lis_person_name_full",
    "lis_person_name_given",
    "lis_person_name_family",
]
lti_names = [
    "lti_roles",
    "lti_user_id",
    "lis_person_contact_email_primary",
    "lti_tool_consumer_instance_guid",
    "lti_context_id",
    "lis_person_name_full",
    "lis_person_name_given",
    "lis_person_name_family",
]


def groups_from_roles(roles):
    groups = []
    if "Student" in roles:
        groups = groups + ["Student"]
    if "Learner" in roles:
        groups = groups + ["Student"]
    if "Instructor" in roles or "ContentDeveloper" in roles:
        groups = groups + ["Admin", "Author", "View"]
    if "Observer" in roles:
        groups = groups + ["View"]
    groups = list(set(groups))
    return groups

class user_stub_from_request:
    def __init__(self, request,course):
        for key, name in zip(lti_keys, lti_names):
            setattr(self, name, request.POST.get(key))
        self.groups = groups_from_roles(request.POST.get("roles", "Student"))
        self.courses = course.pk
        self.immutable_user_id = immutable_user_id(self)

def immutable_user_id(user_stub):
    if not user_stub.lti_user_id:
        return None
    try:
        combostring = ""
        if user_stub.lti_user_id:
            combostring = combostring + user_stub.lti_user_id
        if user_stub.lti_context_id:
            combostring = combostring + user_stub.lti_context_id
        if user_stub.lti_tool_consumer_instance_guid:
            combostring = combostring + user_stub.lti_tool_consumer_instance_guid
        hashstring = hashlib.sha1(combostring.encode("UTF-8")).hexdigest()
        return hashstring
    except Exception as e:
        logging.debug("IMMUTABLE_USER_ID %s", str(e))
        return None


def default_username(opentauser):
    if not opentauser.lti_user_id:
        return None
    try:
        if opentauser.lis_person_contact_email_primary:
            return opentauser.lis_person_contact_email_primary
        elif opentauser.lis_person_name_full:
            return re.sub(r"\s+", "_", opentauser.lis_person_name_full.strip())
        elif opentauser.lis_person_name_given and opentauser.lis_person_name_family:
            last = re.sub(r"\s+", "_", opentauser.lis_person_name_family.strip())
            first = re.sub(r"\s+", "_", opentauser.lis_person_name_given.strip())
            return last + "-" + first

        else:
            return immutable_user_id(opentauser)

    except Exception as e:
        logging.debug("DEFAULT USERNAME FAILED %s", str(e))
        return None
