'''
This is the server side implementation of the question type compareNumeric.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError

# Below are imports that are specific to this question type
import functools
import operator
import exercises.symbolic as symbolic
from exercises.util import compose
from lxml import etree


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


# The function below is the core of the server interface and the only mandatory component.
def question_check_compare_numeric(question_json, question_xmltree, answer_data, global_xmltree):
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
        <question type=compareNumeric>
            <variables>
                var1=value1; var2=value2; ...
            </variables>
            <expression>
                f(var1,var2,...)
            </expression>
        </question>
    '''
    # variables = parse_variables(question_json['variables']['$'])
    # if 'global' in question_json and 'variables' in question_json['global']:
    variables = []
    variables_element = question_xmltree.find('variables')
    if variables_element is not None:
        variables = parse_variables(variables_element.text)
    if global_xmltree is not None and global_xmltree.text is not None:
        global_variables = parse_variables(global_xmltree.text)
        variables += global_variables
    correct_answer = question_xmltree.find('expression').text
    result = {}
    # try:
    result = symbolic.compare_numeric(variables, answer_data, correct_answer)
    # except SympifyError as e:
    #    print(e)
    # print(answer_data)
    # print(correct_answer)
    if 'correct' in result:
        result['status'] = 'correct' if result['correct'] else 'incorrect'
    elif 'error' in result:
        result['status'] = 'error'
    latex = {'latex': symbolic.to_latex(answer_data)}
    result.update(latex)
    return result


# This function call registers the question type with the system
register_question_type('compareNumeric', question_check_compare_numeric)
