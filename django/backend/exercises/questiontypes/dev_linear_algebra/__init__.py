'''
This is the server side implementation of the question type linearAlgebra.
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
from .linear_algebra import linear_algebra_expression
from .linear_algebra import linear_algebra_expression_blocking
from .variableparser import getallvariables
from .parsehints import parsehints

logger = logging.getLogger(__name__)


def parse_variables(variables):  # {{{
    '''
    Parses the variable field.
    Takes a string with variables in the format "var1=x; var2=y; var3=z" and converts into a list of the form
    [ { 'name': 'var1', 'value': 'x'}, ... ]
    '''
    rawvars = " ".join(variables.split()).split(';')
    try:
        pipeline = compose(
            functools.partial(filter, operator.truth),
            functools.partial(map, lambda x: x.split('=')),
            functools.partial(
                map, lambda x: {'name': x[0].strip(' \n\t'), 'value': x[1].strip(' \n\t')}
            ),
        )
        variables = list(pipeline(rawvars))
        return variables  # }}}
    except IndexError:
        raise QuestionError("Cannot parse variables")


def question_check_linear_algebra(question_json, question_xmltree, answer_data, global_xmltree):
    # print("QUESTION_CHECK_LINEAR_ALGEBRA");
    # print("question xmltree",  etree.tostring(question_xmltree , pretty_print=True) )
    # print("global xmltree",  etree.tostring(global_xmltree, pretty_print=True) )
    hints = parsehints(question_xmltree, global_xmltree, answer_data)
    # print("hints = ", hints)
    result = {}
    if hints is not None:
        if hints.get('correct', None) is not None:
            return hints
    check_units = True
    ret = getallvariables(global_xmltree, question_xmltree)
    variables = ret['variables']
    blacklist = ret['blacklist']
    correct_answer = ret['correct_answer']
    equality = question_xmltree.find('equality')
    negate = False
    if equality is not None:
        # print("EQUALITTY = ", equality.text)
        correct_answer = equality.text
    istrue = question_xmltree.find('istrue')
    if istrue is not None:
        correct_answer = istrue.text
        if '==' not in istrue.text:
            correct_answer = istrue.text + "== 1 "
        check_units = False

    isfalse = question_xmltree.find('isfalse')
    if isfalse is not None:
        negate = True
        correct_answer = isfalse.text
        if '==' not in isfalse.text:
            correct_answer = isfalse.text + "== 1 "
        check_units = False

    if '==' in answer_data:
        check_units = False
    precision = question_json.get('@attr').get('precision', '1e-6')
    precision = float(precision)
    result = linear_algebra_expression(
        precision,
        variables,
        answer_data,
        correct_answer,
        check_units=check_units,
        blacklist=list(blacklist),
    )
    # print("NEGATE = ", negate )
    if negate:
        # print("WILL NEGATE ", result )
        if 'correct' in result:
            result['status'] = 'incorrect' if result['correct'] else 'correct'
        elif 'error' in result:
            result['status'] = 'error'
    else:
        if 'correct' in result:
            result['status'] = 'correct' if result['correct'] else 'incorrect'
        elif 'error' in result:
            result['status'] = 'error'
    if hints is not None:
        result.update(hints)
    # print("final result = ", result)
    return result


def linear_algebra_json_hook(safe_question, full_question, question_id, user_id, *args):
    correct_answer = full_question.get('expression').get('$', 'NO TEXT IN EXPRESSION').split(';')[0]
    caretless = re.sub(r"\^", ' ', correct_answer)
    caretless = re.sub(r"[A-Za-z0-9]+\(", '(', caretless)
    lis = re.findall(r'([A-Za-z]+\w*)', caretless)
    if full_question.get('@attr').get('exposeglobals', False):
        safe_question['exposeglobals'] = True
    else:
        safe_question['exposeglobals'] = False

    # DISABLE feedback XML in quesiton
    # feedback = full_question.get('@attr').get('feedback',True)
    # safe_question['feedback'] = feedback
    # print("DEV/ININIT FEEDBACK",  full_question.get('@attr').get('feedback',None) )
    # print("DEV/ININIT FEEDBACK",  safe_question['feedback'] )
    # if feedback is False:
    #        #print("SETTING RESPONS TO None")
    #        #print("feedback is false? = ", feedback)
    #        safe_question['correct'] = None
    #        feedback = False
    # else:
    # print("feedback is true? = ", feedback)
    # print("Nlis = ", lis )
    used_variable_list = []
    [
        used_variable_list.append(item) for item in lis if item not in used_variable_list
    ]  # SELECT UNIQUE ITEMS
    # print("usedvariablelist=", used_variable_list)
    # print("question_id, user_id", question_id, user_id)
    # print("nattemts = ", get_number_of_attempts(question_id, user_id) )
    safe_question['username'] = user_id
    safe_question['usedvariablelist'] = used_variable_list
    safe_question['n_attempts'] = get_number_of_attempts(question_id, user_id)
    safe_question['previous_answers'] = get_previous_answers(question_id, user_id, 5)
    return safe_question


# This function call registers the question type with the system
register_question_type(
    'devLinearAlgebra',
    question_check_linear_algebra,
    linear_algebra_json_hook,
    hide_tags=['expression'],
)
