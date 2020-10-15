'''
This is the server side implementation of the question type linearAlgebra.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError
from exercises.question import get_number_of_attempts, get_previous_answers

# Below are imports that are specific to this question type
import json
import hashlib
from collections import OrderedDict
import functools
import operator
from exercises.util import compose
from lxml import etree
import logging
import re
from .linear_algebra import linear_algebra_expression, question_check
from .variableparser import getallvariables, get_used_variable_list, get_more_variables_from_obj , get_more_functions_from_obj, remove_blacklist_variables_from_obj, get_functions_from_obj


logger = logging.getLogger(__name__)



def question_check_linear_algebra(question_json, question_xmltree, answer_data, global_xmltree):
    return question_check(
        question_json, question_xmltree, answer_data, global_xmltree, linear_algebra_expression
    )


def linear_algebra_json_hook(safe_question, full_question, question_id, user_id, *args):
    #print("FULL = ", full_question)
    correct_answer = full_question.get('expression').get('$', 'NO TEXT IN EXPRESSION').split(';')[0]
    used_variable_list = get_used_variable_list(correct_answer) 
    variablelist = get_more_variables_from_obj( full_question.get('variables', {}), used_variable_list)
    #print("VARIABLELIST = ", variablelist)
    #print("FULL= ", full_question )
    functionlist = get_more_functions_from_obj( full_question.get('global', {}), [])
    #print("FUNCTIONLIST = ", functionlist )
    if (full_question.get('@attr').get('exposeglobals', 'false')).lower() == 'true':
        safe_question['exposeglobals'] = True
        #print("MORE VARIABLES = ",  get_more_variables_from_obj(full_question.get('global', {}), [] ) )
        variablelist = get_more_variables_from_obj(full_question.get('global', {}), variablelist)
    else:
        safe_question['exposeglobals'] = False
    try:
        blacklist = full_question.get('variables').get('blacklist')
    except:
        blacklist = full_question.get('blacklist')
    # DISABLE feedback XML in quesiton
    feedback = full_question.get('@attr').get('feedback',True)
    safe_question['feedback'] = feedback
    if feedback is False:
           safe_question['correct'] = None
           feedback = False
    #print("__INIT__ CALLED")
    #print("VARIABLELIST = ", variablelist )
    if not blacklist is None:
        variablelist = remove_blacklist_variables_from_obj(blacklist, variablelist)
    ## THIS IS WHERE INITIAL USED VARIABLES MUST BE LISTED"
    ## AFTER INITIAL LOAD, the question respsonse loads the variables
    ## 
    #print("FUNCTIONLIST = ", functionlist)
    safe_question['username'] = user_id
    safe_question['used_variable_list'] = [re.sub(r"variable",'', item ) for item in variablelist  ] 
    safe_question['n_attempts'] = get_number_of_attempts(question_id, user_id)
    safe_question['previous_answers'] = get_previous_answers(question_id, user_id, 5)
    return safe_question


# This function call registers the question type with the system
register_question_type(
    'devLinearAlgebra',
    question_check_linear_algebra,
    linear_algebra_json_hook,
    hide_tags=['expression', 'value'],
)
