# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type webworks.
"""

import importlib
import logging
import os.path
import sys

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
def question_check_webworks(question_json, question_xmltree, answer_data, global_xmltree):
    questiondict = dict((xmltodict.parse(etree.tostring(question_xmltree)))["question"])
    questiondict.update(dict(questiondict.get("runtime", {})))
    try:
        dict(xmltodict.parse(etree.tostring(global_xmltree)))
    except:
        pass
    all_answers = question_json.get("all_answers", {})
    studentanswerdict = {"studentanswer": answer_data, "all_answers": all_answers}
    # result = webworks(studentanswerdict, questiondict, globaldict)
    result = dict(correct=True, warning="Ungraded but marked correct; this may change on audit.")
    if "correct" in result:
        result["status"] = "correct" if result["correct"] else "incorrect"
    elif "error" in result:
        result["status"] = "error"
    # return {}
    return result


def webworks_json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback=False):
    if full_question.get("@attr").get("exposeglobals", False):
        safe_question["exposeglobals"] = True
    else:
        safe_question["exposeglobals"] = False
    safe_question["editor"] = full_question.get("@attr").get("editor", "default")
    exercise_key = full_question.get("exercise_key")

    safe_question["username"] = user_id
    safe_question["n_attempts"] = get_number_of_attempts(question_id, user_id)
    safe_question["previous_answers"] = get_previous_answers(question_id, user_id, 5)
    safe_question["all_answers"] = get_other_answers(question_id, user_id, exercise_key)

    return safe_question


def webworks_runner(studentanswerdict, questiondict, globaldict, result_queue):
    try:
        path = questiondict["runtime"]["@path"]
        filename = questiondict.get("@file", "questions")
        functionname = questiondict["@function"]
        sys.path.append(path)
        questions = importlib.import_module(filename)
        func = getattr(questions, functionname)
        response = func(studentanswerdict, questiondict, globaldict)
    except SyntaxError as e:
        response = {}
        response["correct"] = False
        response["warning"] = "B2: Syntax Error :" + functionname + ": " + str(e)

    except NameError as e:
        response = {}
        response["correct"] = False
        response["warning"] = "B1 Name Error:  " + functionname + " " + "  : " + str(e)
    except KeyError as e:
        response = {}
        response["correct"] = False
        response["warning"] = (
            "B3: Key Error: Probably missing previous answer or wrong key : " + functionname + ": " + str(e)
        )
    except OSError as e:
        response = {}
        response["correct"] = False
        estring = (str(e)).split(" ", 1)
        filename = os.path.basename(estring[0])
        try:
            secondpart = estring[1]
        except:
            secondpart = ""
        response["warning"] = "A3: " + (filename + " " + secondpart)[0:120]
    except Exception as e:
        response = {}
        response["correct"] = False
        response["warning"] = "A1: " + str(type(e).__name__) + " : " + functionname + ": " + (str(e))[0:120]
    result_queue.put(response)


# def pythonic(studentanswerdict, questiondict, globaldict):
#    """
#    Starts a process with external_question that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
#    """
#    invalid_strings = ['_']
#    expression1 = studentanswerdict['studentanswer']
#    for i in invalid_strings:
#        if i in expression1:
#            return {'error': _('Answer contains invalid character ') + i}
#    return safe_run(webworks_runner, args=(studentanswerdict, questiondict, globaldict))
def default_validate_question(question_json, *arg,**kwargs):
    return ()



register_question_type("webworks", question_check_webworks, question_check_webworks, default_validate_question, webworks_json_hook)
