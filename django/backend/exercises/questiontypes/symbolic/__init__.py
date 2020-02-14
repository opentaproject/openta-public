'''
This is the server side implementation of the question type symbolic.
'''
from exercises.questiontypes.dev_linear_algebra.unithelpers import ns

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError
from exercises.question import get_number_of_attempts, get_previous_answers

# Below are imports that are specific to this question type
import hashlib
from collections import OrderedDict
import functools
import operator
from exercises.util import compose
from lxml import etree
import logging
import re
from .symbolic import symbolic_expression
from .symbolic import symbolic_expression_blocking
from exercises.questiontypes.dev_linear_algebra.variableparser import get_used_variable_list
from exercises.questiontypes.dev_linear_algebra import parsehints, parse_variables, question_check
from exercises.questiontypes.dev_linear_algebra import (
    get_more_variables_from_obj,
    get_functions_from_obj,
    remove_blacklist_variables_from_obj,
)

logger = logging.getLogger(__name__)


def question_check_symbolic(question_json, question_xmltree, answer_data, global_xmltree):
    return question_check(
        question_json, question_xmltree, answer_data, global_xmltree, symbolic_expression
    )


def symbolic_json_hook(safe_question, full_question, question_id, user_id, *args):
    correct_answer = full_question.get('expression').get('$', 'NO TEXT IN EXPRESSION').split(';')[0]
    used_variable_list = get_used_variable_list(correct_answer)
    variablelist = get_more_variables_from_obj(
        full_question.get('variables', {}), used_variable_list
    )
    if (full_question.get('@attr').get('exposeglobals', 'false')).lower() == 'true':
        safe_question['exposeglobals'] = True
        variablelist = get_more_variables_from_obj(full_question.get('global', {}), variablelist)
    else:
        safe_question['exposeglobals'] = False
    variablelist = get_functions_from_obj(full_question.get('global', {}), variablelist)
    try:
        blacklist = full_question.get('variables').get('blacklist')
    except:
        blacklist = full_question.get('blacklist')
    if not blacklist is None:
        variablelist = remove_blacklist_variables_from_obj(blacklist, variablelist)
    safe_question['username'] = user_id
    safe_question['used_variable_list'] = (
        variablelist if safe_question['exposeglobals'] else used_variable_list
    )
    safe_question['n_attempts'] = get_number_of_attempts(question_id, user_id)
    safe_question['previous_answers'] = get_previous_answers(question_id, user_id, 5)
    return safe_question


# This function call registers the question type with the system
register_question_type(
    'symbolic', question_check_symbolic, symbolic_json_hook, hide_tags=['expression', 'value'],
)
