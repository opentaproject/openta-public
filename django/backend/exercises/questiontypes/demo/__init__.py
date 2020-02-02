'''
This is the server side implementation of the question type demo.
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
from .demo import (
    demo,
    to_latex,
)  # The sympy interface is placed in a separate file "demo.py" in this folder

logger = logging.getLogger(__name__)


# The function below is the core of the server interface and the only mandatory component.
def question_check_demo(question_json, question_xmltree, answer_data, global_xmltree):
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
        <question type=demo>
            <variables>
                var1=value1; var2=value2; ...
            </variables>
            <expression>
                f(var1,var2,...)
            </expression>
        </question>
    '''

    correct_answer = question_xmltree.find('expression').text.split(';')[0]
    result = {}
    result = demo(answer_data, correct_answer)
    if 'correct' in result:
        result['status'] = 'correct' if result['correct'] else 'incorrect'
    elif 'error' in result:
        result['status'] = 'error'
    # Add the sympy representation in latex form for possible visual checks
    # latex = { 'latex': '' } #to_latex(answer_data) }
    # result.update(latex)
    return result


# This function call registers the question type with the system
register_question_type('demo', question_check_demo)
