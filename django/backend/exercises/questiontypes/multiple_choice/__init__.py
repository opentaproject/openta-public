'''
This is the server side implementation of the question type compareNumeric.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError

# Below are imports that are specific to this question type
from lxml import etree

# The function below is the core of the server interface and the only mandatory component.
def question_check_multiple_choice(question_json, question_xmltree, answer_data, global_xmltree):
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
    choices = []
    choices_element = question_xmltree.xpath('//choice')
    correct_answer = question_xmltree.find('correct').text

    result = {}
    if int(correct_answer) - 1 == int(answer_data):
        result['correct'] = True
    else:
        result['correct'] = False
    return result


# This function call registers the question type with the system
register_question_type('multipleChoice', question_check_multiple_choice)
