# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from .aibased import aibased_internal, responses_internal
from django.conf import settings
"""
This is the server side implementation of the question type aibased.
"""

import importlib
import logging
import os.path
import sys
from exercises.questiontypes.safe_run import safe_run


from exercises.question import (  # This function is used to register the question type
    QuestionError,
    get_number_of_attempts,
    get_other_answers,
    get_previous_answers,
    register_question_type,
)

logger = logging.getLogger(__name__)


import xmltodict
from lxml import etree

logger = logging.getLogger(__name__)


# The function below is the core of the server interface and the only mandatory component.
def question_check_aibased(question_json, question_xmltree, answer_data, global_xmltree):
    #print(f"QUESTION_CHECK_AI_BASED")
    questiondict = dict((xmltodict.parse(etree.tostring(question_xmltree)))["question"])
    questiondict.update(dict(questiondict.get("runtime", {})))
    all_answers = question_json.get("all_answers", {})
    studentanswerdict = {"studentanswer": answer_data, "all_answers": all_answers}
    globaldict = {}
    if 'rue' in questiondict.get('@silent','') :
        result = dict(status="correct")
    else :
        result = {} # dict(warning=f"{answer_data}")
        result = aibased(studentanswerdict, questiondict, globaldict)
    if "correct" in result:
        result["status"] = "correct" if result["correct"] else "incorrect"
    elif "error" in result:
        result["status"] = "error"
    #print(f"QUESTION_CHECK_AIBSEED RESULT ")
    # return {}
    return result


def aibased_json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback,db=None):
    #print(f"AIBASED_QUESTION_HOOK feedback={feedback} db={db}")
    if full_question.get("@attr").get("exposeglobals", False):
        safe_question["exposeglobals"] = True
    else:
        safe_question["exposeglobals"] = False
    safe_question["editor"] = full_question.get("@attr").get("editor", "default")
    safe_question["username"] = user_id
    safe_question["n_attempts"] = get_number_of_attempts(question_id, user_id)
    safe_question["previous_answers"] = get_previous_answers(question_id, user_id, n_answers=settings.N_ANSWERS, feedback=feedback,db=db)
    safe_question["all_answers"] = get_other_answers(question_id, user_id, exercise_key)
    return safe_question

def aibased_runner(studentanswerdict, questiondict, globaldict, result_queue):
    try:
        path = questiondict["runtime"]["@path"]
        filename = questiondict.get("@file", "questions")
        sys.path.append(path)
        try :
            questions = importlib.import_module(filename)
        except :
            pass
        response = responses_internal(studentanswerdict, questiondict, globaldict)
        #print(f"RSPONSE IN RUNNER = {response}")
    except Exception as e:
        response = {}
        response["correct"] = False
        response["warning"] = "A1: " + str(type(e).__name__) + " : "  ": " + (str(e))
    result_queue.put(response)


def aibased(studentanswerdict, questiondict, globaldict):
    print(f"AIBASED IN __INIT__")
    """
    Starts a process with external_question that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_']
    expression1 = studentanswerdict['studentanswer']
    #for i in invalid_strings:
    #    if i in expression1:
    #        return {'error': 'Answer contains invalid character ' + i}
    return responses_internal( studentanswerdict, questiondict, globaldict)
    #print(f"AIBASED_RESPONSE {response}")
    #return safe_run(aibased_runner, args=(studentanswerdict, questiondict, globaldict))

def default_validate_question(question_json, *arg,**kwargs):
    return ()


register_question_type("aibased", question_check_aibased, question_check_aibased, default_validate_question, aibased_json_hook)
