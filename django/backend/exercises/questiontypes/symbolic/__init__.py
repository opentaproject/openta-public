'''
This is the server side implementation of the question type symbolic.
'''

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
    # caretless = re.sub(r"\^",' ',correct_answer)
    # caretless = re.sub(r"[A-Za-z0-9]+\(",'(',caretless)
    # lis = re.findall(r'([A-Za-z]+\w*)', caretless )
    # print("DEV : INIT : JSON HOOK")
    variablelist = get_more_variables_from_obj(
        full_question.get('variables', {}), used_variable_list
    )
    # print("DEV : INIT : JSON HOOK variablelist after searching question", variablelist)
    if (full_question.get('@attr').get('exposeglobals', 'false')).lower() == 'true':
        # print("Expose = true")
        safe_question['exposeglobals'] = True
        # print("global variables full_question.get", full_question.get('global',{} ) )
        variablelist = get_more_variables_from_obj(full_question.get('global', {}), variablelist)
    else:
        # print("Expose = false")
        safe_question['exposeglobals'] = False
    variablelist = get_functions_from_obj(full_question.get('global', {}), variablelist)
    try:
        blacklist = full_question.get('variables').get('blacklist')
    except:
        blacklist = full_question.get('blacklist')
    if not blacklist is None:
        variablelist = remove_blacklist_variables_from_obj(blacklist, variablelist)
    # print("variablelist = ", variablelist)
    # print("DEV_INIT question_variables = ", full_question.get('variables',{} ) )
    # print("DEV_INIT global_variables = ", full_question.get('global', {} ) )
    # DISABLE feedback XML in quesiton
    # feedback = full_question.get('@attr').get('feedback',True)
    # safe_question['feedback'] = feedback
    # print("DEV/ININIT FEEDBACK",  full_question.get('@attr').get('feedback',None) )
    # print("DEV/ININIT FEEDBACK",  safe_question['feedback'] )
    # if feedback is False :
    #        #print("SETTING RESPONS TO None")
    #        #print("feedback is false? = ", feedback)
    #        safe_question['correct'] = None
    #        feedback = False
    # else :
    # print("feedback is true? = ", feedback)
    # print("Nlis = ", lis )
    # used_variable_list = []
    # [ used_variable_list.append(item) for item in lis if item not in used_variable_list ]  # SELECT UNIQUE ITEMS
    # print("usedvariablelist=", used_variable_list)
    # print("question_id, user_id", question_id, user_id)
    # print("nattemts = ", get_number_of_attempts(question_id, user_id) )
    # print("INIT.PY : full_question", full_question)
    # print("SAFE_QUESTION = ", safe_question)
    safe_question['username'] = user_id
    # safe_question['usedvariablelist'] = used_variable_list
    safe_question['used_variable_list'] = variablelist + ['AB']
    # print("VARIABLELIST = ", variablelist )
    safe_question['n_attempts'] = get_number_of_attempts(question_id, user_id)
    safe_question['previous_answers'] = get_previous_answers(question_id, user_id, 5)
    return safe_question


# This function call registers the question type with the system
register_question_type(
    'symbolic', question_check_symbolic, symbolic_json_hook, hide_tags=['expression', 'value'],
)
