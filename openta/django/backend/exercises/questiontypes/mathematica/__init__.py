# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type mathematica.
"""

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

from .mathematica import mathematica  # The sympy interface is placed in a separate file "mathematica.py" in this folder

logger = logging.getLogger(__name__)
from exercises.utils import json_hook as mathematica_json_hook



# The function below is the core of the server interface and the only mandatory component.
def question_check_mathematica(question_json, question_xmltree, answer_data, global_xmltree):
    questiondict = dict((xmltodict.parse(etree.tostring(question_xmltree)))["question"])
    questiondict.update(dict(questiondict.get("runtime", {})))
    try:
        globaldict = dict(xmltodict.parse(etree.tostring(global_xmltree)))
    except:
        globaldict = {}
    all_answers = question_json.get("all_answers", {})
    studentanswerdict = {"studentanswer": answer_data, "all_answers": all_answers}
    result = mathematica(studentanswerdict, questiondict, globaldict)
    if "correct" in result:
        result["status"] = "correct" if result["correct"] else "incorrect"
    elif "error" in result:
        result["status"] = "error"
    return result


def validate_question(question_json, *arg,**kwargs):
    return ()





register_question_type("mathematica", question_check_mathematica, question_check_mathematica, validate_question, mathematica_json_hook)
register_question_type("wlanguage", question_check_mathematica, question_check_mathematica,  validate_question, mathematica_json_hook)
