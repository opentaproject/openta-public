'''
This is the server side implementation of the question type Numeric.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError
from exercises.models import Exercise, Question, Answer

# Below are imports that are specific to this question type
import functools
import operator
import re
from exercises.util import compose
import json
from lxml import etree
import logging
from .numeric import (
    numeric,
    to_latex,
    getprecision,
)  # The sympy interface is placed in a separate file "numeric.py" in this folder

logger = logging.getLogger(__name__)
from .variableparser import getallvariables


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


# def parse_xml_variables(node):
#    '''
#    Parses variables defined through the XML syntax <var>...</var>
#    '''
#    variables = node.xpath('./var')
#    res = []
#    if variables is None:
#        return res
#    for var in variables:
#        token = var.find('token')
#        value = var.find('val')
#        if token is not None:
#            res.append({'name': token.text, 'value': value if value is not None else '1'})
#    return res

# def parse_blacklist(node):
#    tokens = node.xpath('./blacklist/token')
#    ret = []
#    for token in tokens:
#        if hasattr(token,'text'):
#            ret.append(token.text.strip(' \t\n\r'))
#    return ret

# The function below is the core of the server interface and the only mandatory component.
def question_check_numeric(question_json, question_xmltree, answer_data, global_xmltree):
    '''Checks a symbolic answer by numeric evaluation.

    Args:
        question_json (dictionary): The JSON representation of the <question> XML content
        question_xmltree (etree.Element): The XML ETree representation of the <question> XML content
        answer_data (dynamic): The answer provided by the frontend
    Returns:
        (dictionary)
        {
            correct: true/false
            error: (optional)
            status: correct/incorrect/error
            latex: latex representation of answer_data by sympy
        }
    Notes:
    Expects the XML format:
        <question type=Numeric>
            <variables>
                var1=value1; var2=value2; ...
            </variables>
            <expression>
                f(var1,var2,...)
            </expression>
        </question>
    '''
    precision = question_json.get('@attr').get('precision', '0')
    questiontext = question_xmltree.find('expression', None)
    # print("questiontext = ", questiontext.text)
    # print("precision = ", precision)
    # print("answerdata = ", answer_data)
    caretless = re.sub(r"\^", ' ', questiontext.text)
    # print("caretless = ", caretless )
    lis = re.findall(r'([A-z]+\w*)', caretless)
    # print("lis = ", lis )
    used_variable_list = []
    [
        used_variable_list.append(item) for item in lis if item not in used_variable_list
    ]  # SELECT UNIQUE ITEMS
    # print("used_variable_list = ", used_variable_list )
    ret = getallvariables(global_xmltree, question_xmltree)
    variables = ret['variables']
    blacklist = ret['blacklist']
    correct_answer = ret['correct_answer']
    # variables = []
    # variables += parse_xml_variables(question_xmltree)
    # if global_xmltree is not None:
    #   variables += parse_xml_variables(global_xmltree)
    # variables_element = question_xmltree.find('variables')
    # if variables_element is not None:
    #    variables += parse_variables(variables_element.text)
    # if global_xmltree is not None and global_xmltree.text is not None:
    #    global_variables = parse_variables(global_xmltree.text)
    #    variables += global_variables
    #
    # unique_vars = { var['name']: var for var in variables }
    # variables = list(unique_vars.values())
    # correct_answer = question_xmltree.find('expression').text.split(';')[0]
    # if global_xmltree is not None:
    #   blacklist.update(parse_blacklist(global_xmltree))
    # blacklist.update(parse_blacklist(question_xmltree))
    # print("variables = ", variables)
    # print("used_variable_list = ", used_variable_list)
    used_variables = [v for v in variables if v['name'] in used_variable_list]
    # print("used_variables = ", used_variables )
    result = {}
    result = numeric(variables, answer_data, correct_answer, precision)
    if 'correct' in result:
        result['status'] = 'correct' if result['correct'] else 'incorrect'
    elif 'error' in result:
        result['status'] = 'error'
    # Add the sympy representation in latex form for possible visual checks
    # latex = { 'latex': '' } #to_latex(answer_data) }
    # result.update(latex)
    return result


def numeric_json_hook(safe_question, full_question, question_id, user_id):
    # print("NUMERIC_INIT.PY: question", json.dumps( full_question,  sort_keys=True, indent=4))
    question_key = full_question.get('@attr').get('key', 0)
    # print("NUMERIC_INIT.PY question_key =  ", question_key )
    # print("NUMERIC_INIT.PY exercise_key =  ", exercise_key )
    # print("NUMERIC_INIT.PY:  Answer Objects : number incorrect=",    len( Answer.objects.filter(user=user,question_key=question_key,exercise_key=exercise_key,correct=False)))
    try:
        # print("NUMERIC_INIT.PY: question.children", question.get('$children$',"NO children") )
        # print("NUMERIC_INIT.PY: question.expression", question.get('expression').get('$',"NO EXPRESSION") )
        correct_answer = (
            full_question.get('expression').get('$', 'NO TEXT IN EXPRESSION').split(';')[0]
        )
        caretless = re.sub(r"\^", ' ', correct_answer)
        # print("Ncaretless = ", caretless )
        lis = re.findall(r'([A-Z,a-z]+\w*)', caretless)
        # print("Nlis = ", lis )
        if full_question.get('@attr').get('exposeglobals', False):
            print("EXPOSE GLOBALS WAS SET")
            safe_question['exposeglobals'] = True
        else:
            safe_question['exposeglobals'] = False
        print("EXPOSE GLOBALS WAS NOT  SET")
        used_variable_list = []
        [
            used_variable_list.append(item) for item in lis if item not in used_variable_list
        ]  # SELECT UNIQUE ITEMS
        # print("Nused_variable_list = ", used_variable_list )
        # print("NNUMERIC_INIT.PY CORRECTANSWER = ",  correct_answer )
        safe_question['username'] = user_id
        safe_question['usedvariablelist'] = used_variable_list
        precision = full_question.get('@attr').get('precision', 0)
        precision = float(precision)
        if precision == 0:
            precision = getprecision(correct_answer)
            # if prec[0] == 0:
            #    precision =  0
            # else:
            #    precision = 'numeriskt &plusmn; '+ str( 100 * prec[0] )+'%'
        # print("NUMERIC_JSON_HOOK: prec = ", precision )
        if precision == 0:
            precisiontext = "EXAKT"
        else:
            precisiontext = '\u00B1 ' + str(100 * precision) + '%'
        safe_question['precision'] = precisiontext
    except:
        print("ERROR IN JSON HOOK")
    # print("RETURN FROM HOOK, question = ",  json.dumps( question ,  sort_keys=True, indent=4))
    return safe_question


register_question_type(
    'Numeric', question_check_numeric, numeric_json_hook, hide_tags=['expression']
)


# This function call registers the question type with the system
