# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type pythonic.
"""

from django.conf import settings
import logging

import xmltodict
from exercises.question import (  # This function is used to register the question type
    QuestionError,
    get_number_of_attempts,
    get_other_answers,
    get_previous_answers,
    register_question_type,
)
from lxml import etree

from .pythonic import pythonic  # The sympy interface is placed in a separate file "pythonic.py" in this folder

logger = logging.getLogger(__name__)


# The function below is the core of the server interface and the only mandatory component.
def question_check_pythonic(question_json, question_xmltree, answer_data, global_xmltree):
    questiondict = dict((xmltodict.parse(etree.tostring(question_xmltree)))["question"])
    questiondict['@is_staff'] = question_json.get('is_staff',False )
    questiondict.update(dict(questiondict.get("runtime", {})))
    try:
        globaldict_ = dict(xmltodict.parse(etree.tostring(global_xmltree)))
    except:
        globaldict_ = {}
    # strip semicolons at the end of dicts 
    globaldict =  { key : val.rstrip().rstrip(';').rstrip()  for (key,val) in globaldict_.items() if val  }
    logger.error("PYTHONIC QUESTION_JSON ", question_json)
    all_answers = question_json.get("other_answers", {})
    studentanswerdict = {"studentanswer": answer_data, "all_answers": all_answers}
    #print(f"questiondict= {answer_data}")
    #print(f"globaldict= {globaldict}")
    result = pythonic(studentanswerdict, questiondict, globaldict)
    if "correct" in result:
        result["status"] = "correct" if result["correct"] else "incorrect"
    elif "error" in result:
        result["status"] = "error"
    return result

def default_validate_question(question_json, *arg,**kwargs):
    return ()



def pythonic_json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback,db=None):
    if full_question.get("@attr").get("exposeglobals", False):
        safe_question["exposeglobals"] = True
    else:
        safe_question["exposeglobals"] = False

    safe_question["username"] = user_id
    safe_question["n_attempts"] = get_number_of_attempts(question_id, user_id)
    safe_question["previous_answers"] = get_previous_answers(question_id, user_id, n_answers=settings.N_ANSWERS, feedback=feedback, db=db)
    safe_question["all_answers"] = get_other_answers(question_id, user_id, exercise_key)
    #print(f"PYTHONIC_JSON_HOOK {safe_question}")

    return safe_question


register_question_type("pythonic", question_check_pythonic, question_check_pythonic,  default_validate_question, pythonic_json_hook)
