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
from .variableparser import getallvariables, get_used_variable_list

# from .parsehints import parsehints

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


def question_check(question_json, question_xmltree, answer_data, global_xmltree, symex):
    print("DEV LINEAR ALGEBRA QUESTION_CHECK, ANSWER-DATA", answer_data)
    # hints = parsehints(question_xmltree, global_xmltree, answer_data)
    result = {}
    # if hints is not None:
    #    if hints.get('correct', None) is not None:
    #        return hints
    check_units = True
    ret = getallvariables(global_xmltree, question_xmltree, assign_all_numerical=False)
    # print("RET = ", ret)
    used_variables = list(ret['used_variables'])
    variables = ret['variables']
    funcsubs = ret['functions']
    # print("QUESTION CHECK FUNCSUBS = ", funcsubs)
    authorvariables = ret['authorvariables']
    blacklist = ret['blacklist']
    correct_answer = ret['correct_answer']
    equality = question_xmltree.find('equality')
    negate = False
    if equality is not None:
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
    precision = question_json.get('@attr').get('precision', '1e-6')
    precision = float(precision)
    result = symex(
        precision,
        authorvariables,
        answer_data,
        correct_answer,
        check_units=check_units,
        blacklist=list(blacklist),
        used_variables=used_variables,
        funcsubs=funcsubs,
    )
    logger.debug("RESULT = " + str(result))
    logger.debug("NEGATE = " + str(negate))
    logger.debug("RESULT KEYS = " + str(list(result.keys())))
    if negate:
        logger.debug("WILL NEGATE " + str(result))
        if 'correct' in list(result.keys()):
            if result['correct']:
                result['status'] = 'incorrect'
            else:
                result['status'] = 'correct'
            # result['status'] = 'incorrect' if result['correct'] else 'correct'
        elif 'error' in list(result.keys()):
            result['status'] = 'error'
    else:
        logger.debug("DONT NEGATE " + str(result))
        if 'correct' in list(result.keys()):
            if result['correct']:
                result['status'] = 'correct'
            else:
                result['status'] = 'incorrect'
        # result['status'] = 'incorrect' if result['correct'] else 'correct'
        # if 'correct' in result.keys() :
        #    result['status'] = 'correct' if result['correct'] else 'incorrect'
        elif 'error' in list(result.keys()):
            result['status'] = 'error'
    # if hints is not None:
    #    result.update(hints)
    #print("final result = ", result)
    logger.debug("RETTURN RESULT = " + str(result))
    return result


def question_check_linear_algebra(question_json, question_xmltree, answer_data, global_xmltree):
    return question_check(
        question_json, question_xmltree, answer_data, global_xmltree, linear_algebra_expression
    )


def get_functions_from_obj(variablesobj, foundvariables=[]):
    vars_ = variablesobj.get('func', {})
    if not isinstance(vars_, list):
        vars_ = [vars_]
    for var in vars_:
        try:
            token = (var.get('token').get('$')).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
        except:
            pass
    return foundvariables


def get_more_variables_from_obj(variablesobj, foundvariables=[]):
    variablestring = variablesobj.get('$', '')
    variablelist = variablestring.split(';')
    for variable in variablelist:
        variable = variable.strip()
        if '=' in variable:
            token = (variable.split('=')[0]).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
    vars_ = variablesobj.get('var', {})
    if not isinstance(vars_, list):
        vars_ = [vars_]
    for var in vars_:
        try:
            token = (var.get('token').get('$')).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
        except:
            pass
    return foundvariables


def remove_blacklist_variables_from_obj(variablesobj, foundvariables=[]):
    variablestring = variablesobj.get('$', '')
    variablelist = variablestring.split(';')
    tokens = variablesobj.get('token', {})
    if not isinstance(tokens, list):
        tokens = [tokens]
    for tokendict in tokens:
        if not tokendict.get('$') is None:
            # print("FOUND TOKEN TO REMOVE ", tokendict.get('$') )
            token = (tokendict.get('$')).strip()
            if token in foundvariables:
                foundvariables.remove(token)
    return foundvariables


def linear_algebra_json_hook(safe_question, full_question, question_id, user_id, *args):
    correct_answer = full_question.get('expression').get('$', 'NO TEXT IN EXPRESSION').split(';')[0]
    used_variable_list = get_used_variable_list(correct_answer)
    variablelist = get_more_variables_from_obj(
        full_question.get('variables', {}), used_variable_list
    )
    if (full_question.get('@attr').get('exposeglobals', 'false')).lower() == 'true':
        # print("Expose = true")
        safe_question['exposeglobals'] = True
        variablelist = get_more_variables_from_obj(full_question.get('global', {}), variablelist)
    else:
        safe_question['exposeglobals'] = False
    try:
        blacklist = full_question.get('variables').get('blacklist')
    except:
        blacklist = full_question.get('blacklist')
    if not blacklist is None:
        variablelist = remove_blacklist_variables_from_obj(blacklist, variablelist)
    safe_question['username'] = user_id
    safe_question['used_variable_list'] = variablelist
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
