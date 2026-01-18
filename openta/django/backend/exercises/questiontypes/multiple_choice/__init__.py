# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type multipleChoice.
"""

import json
import logging

# Below are imports that are specific to this question type
from django.utils.translation import gettext as _

# This function is used to register the question type
from exercises.question import get_number_of_attempts, register_question_type

logger = logging.getLogger(__name__)

# The function below is the core of the server interface and the only mandatory component.
def question_check_multiple_choice(question_json, question_xmltree, answer_data, global_xmltree):
    """Checks a multiple choice question

    Args:
        question_json (dictionary): The JSON representation of the <question> XML content
        question_xmltree (etree.Element): The XML ETree representation of the <question> XML content
        answer_data (JSON string): JSON encoded dictionary of answers
            {
                '[choice key]': true/false
                ...
            }
    Returns:
        (dictionary)
        {
            correct: true/false
            correctAnswers: A dictionary with entries corresponding to the answers in answer_data
                {
                '[choice key]': boolean
                ...
                }
            error: (optional)
        }
    Notes:
    Expects the XML format:
        <question type=multipleChoice>
            <choice key="..">
                ...
            </choice>
            <choice key=".." correct="true">
            </choice>
            <text>
                Question text
            </text>
        </question>
    """
    correct_items = question_xmltree.xpath('.//choice[@correct="true"]')
    show_errors = question_xmltree.attrib.get("showerrors", "false").lower() == "true"
    try:
        answer_json = json.loads(answer_data)
    except ValueError:
        return {"error": "Not valid answer data."}
    results = {"choices": {}}
    n_correct = 0
    n_incorrect = 0
    for question, val in answer_json.items():
        if val:
            correct = next((True for item in correct_items if item.get("key") == question), None)
            if correct is not None:
                if show_errors:
                    results["choices"][question] = True
                n_correct += 1
            else:
                if show_errors:
                    results["choices"][question] = False
                n_incorrect += 1

    results["correct"] = False
    if n_incorrect == 0 and n_correct == len(correct_items):
        results["correct"] = True
    if n_correct > 0 and n_correct < len(correct_items) and show_errors:
        results["info"] = _("There are more correct alternatives.")
        results["status"] = _("There are more correct alternatives.")
    return results


def mutiple_choice_json_hook(safe_question, full_question, question_id, user_id, *args,**kwargs):
    safe_question["n_attempts"] = get_number_of_attempts(question_id, user_id)
    return safe_question

def default_validate_question(question_json, *arg,**kwargs):
    return ()


# This function call registers the question type with the system
register_question_type(
    "multipleChoice",
    question_check_multiple_choice,
    question_check_multiple_choice,
    default_validate_question,
    mutiple_choice_json_hook,
    hide_attrs=["correct"],
)
