# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import hashlib
import logging
import re

from pylti.common import LTIException

logger = logging.getLogger(__name__)


# Register your models here.

lti_keys = [
    ["roles"],
    ["custom_user_id", "user_id"],
    ["custom_lis_person_contact_email_primary", "lis_person_contact_email_primary"],
    ["lti_tool_consumer_instance_guid", "tool_consumer_instance_guid"],
    ["lti_context_id", "context_id"],
    ["custom_lis_person_name_full", "lis_person_name_full"],
    ["custom_lis_person_name_given", "lis_person_name_given"],
    ["custom_lis_person_name_family", "lis_person_name_family"],
    ["custom_canvas_login_id" ]
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
    "lti_login_id",
]


def groups_from_roles(roles):
    groups = []
    if "Student" in roles:
        groups = groups + ["Student"]
    if "Learner" in roles:
        groups = groups + ["Student"]
    if "Instructor" in roles or "ContentDeveloper" in roles or "TeachingAssistant" in roles:
        groups = groups + ["Admin", "Author", "View"]
    if "Observer" in roles:
        groups = groups + ["View"]
    if "Guest" in roles:
        groups = groups + ["AnonymousStudent"]
    groups = list(set(groups))
    if not groups :
        raise LTIException("Error in LTI authentication: No valid role indicated")
    return groups


def verify_request(request):
    """Catch some known LTI/Canvas issues."""
    if request.POST.get("user_id") is None and request.POST.get("custom_user_id") is None:
        raise LTIException("Error in LTI authentication: user_id and custom_user_id = None, please try again.")

    # if request.POST.get("custom_user_id") is None:
    #    raise LTIException("Error in LTI authentication: custom_user_id = None, please try again.")

    # if "$" in request.POST.get("custom_user_id"):
    #    raise LTIException("Error in LTI authentication: custom_userid_contains dollar sign, please try again.")


class user_stub_from_request:
    def __init__(self, request, course):
        for keys, name in zip(lti_keys, lti_names):
            keyval = None
            for key in keys:
                if request.POST.get(key):
                    keyval = request.POST.get(key).strip()
                    break;
            setattr(self, name, keyval)
        self.groups = groups_from_roles(request.POST.get("roles", "Student"))
        self.courses = [course]
        self.immutable_user_id = immutable_user_id(self)


def immutable_user_id(user_stub):
    if not user_stub.lti_user_id:
        return None
    try:
        combostring = ""
        if user_stub.lti_user_id:
            combostring = combostring + user_stub.lti_user_id
        # if user_stub.lti_context_id: # THIS IS DANGEROUS; IT IS AN UNSTABLE KEY
        #    combostring = combostring + user_stub.lti_context_id
        if user_stub.lti_tool_consumer_instance_guid:
            combostring = combostring + user_stub.lti_tool_consumer_instance_guid
        hashstring = hashlib.sha1(combostring.encode("UTF-8")).hexdigest()
        return hashstring
    except Exception as e:
        logging.debug("IMMUTABLE_USER_ID %s", str(e))
        return None


def default_username(opentauser):
    #logger.error(f"DEFAULT_USERNAME OPENTAUSER = {vars(opentauser)}")
    #try :
    #    if opentauser.lti_login_id :
    #        return opentauser.lti_login_id
    #except :
    #    pass
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
            # return "%s-%s" % ( immutable_user_id(opentauser)[0:4], immutable_user_id(opentauser)[5:9] )
            return immutable_user_id(opentauser)

    except Exception as e:
        logging.debug("DEFAULT USERNAME FAILED %s", str(e))
        return None
