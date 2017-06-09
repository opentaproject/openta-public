'''
This is the server side implementation of the question type Numeric.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError

# Below are imports that are specific to this question type
import functools
import operator
from exercises.util import compose
from lxml import etree
import logging
from .numeric import (
    numeric,
    to_latex,
)  # The sympy interface is placed in a separate file "numeric.py" in this folder

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


def parse_xml_variables(node):
    '''
    Parses variables defined through the XML syntax <var>...</var>
    '''
    variables = node.xpath('./var')
    res = []
    if variables is None:
        return res
    for var in variables:
        token = var.find('token')
        value = var.find('val')
        if token is not None:
            res.append({'name': token.text, 'value': value if value is not None else '1'})
    return res


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
    print("precision = ", precision)
    variables = []
    variables += parse_xml_variables(question_xmltree)
    # NOTE THAT GLOBAL XMLTREE IS NOT PARSED IN THIS TYPE
    # if global_xmltree is not None:
    #    variables += parse_xml_variables(global_xmltree)
    variables_element = question_xmltree.find('variables')
    if variables_element is not None:
        variables += parse_variables(variables_element.text)
    # if global_xmltree is not None and global_xmltree.text is not None:
    #    global_variables = parse_variables(global_xmltree.text)
    #    variables += global_variables

    unique_vars = {var['name']: var for var in variables}
    variables = list(unique_vars.values())
    correct_answer = question_xmltree.find('expression').text.split(';')[0]

    # if global_xmltree is not None:
    #   blacklist.update(parse_blacklist(global_xmltree))
    # blacklist.update(parse_blacklist(question_xmltree))
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


# This function call registers the question type with the system
register_question_type('Numeric', question_check_numeric)
