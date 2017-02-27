'''
This is the server side implementation of the question type compareNumeric.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError

# Below are imports that are specific to this question type
from lxml import etree
import json

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
    correct_items = question_xmltree.xpath('//choice[@correct="true"]')
    try:
        answer_json = json.loads(answer_data)
    except ValueError:
        print('Not valid json')

    results = {}
    n_correct = 0
    n_incorrect = 0
    for question, val in answer_json.items():
        for item in correct_items:
            if val:
                if item.get('key') == question:
                    results[question] = True
                    n_correct += 1
                else:
                    results[question] = False
                    n_incorrect += 1
    if n_incorrect == 0 and n_correct == len(correct_items):
        results['correct'] = True
    return results


# This function call registers the question type with the system
register_question_type('multipleChoice', question_check_multiple_choice)
