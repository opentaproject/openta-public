'''
This is the server side implementation of the question type pythonic.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError
from exercises.question import get_number_of_attempts, get_previous_answers, get_other_answers


import functools
import xmltodict
import pprint as pp
import json
import operator
from exercises.util import compose
from lxml import etree
import logging
from .pythonic import (
    pythonic,
)  # The sympy interface is placed in a separate file "pythonic.py" in this folder

logger = logging.getLogger(__name__)


# The function below is the core of the server interface and the only mandatory component.
def question_check_pythonic(question_json, question_xmltree, answer_data, global_xmltree):
    questiondict = dict((xmltodict.parse(etree.tostring(question_xmltree)))['question'])
    questiondict.update(dict(questiondict.get('runtime', {})))
    try:
        globaldict = dict(xmltodict.parse(etree.tostring(global_xmltree)))
    except:
        globaldict = {}
    all_answers = question_json.get('all_answers', {})
    studentanswerdict = {'studentanswer': answer_data, 'all_answers': all_answers}
    result = pythonic(studentanswerdict, questiondict, globaldict)
    if 'correct' in result:
        result['status'] = 'correct' if result['correct'] else 'incorrect'
    elif 'error' in result:
        result['status'] = 'error'
    return result


def pythonic_json_hook(safe_question, full_question, question_id, user_id, exercise_key):
    if full_question.get('@attr').get('exposeglobals', False):
        safe_question['exposeglobals'] = True
    else:
        safe_question['exposeglobals'] = False

    safe_question['username'] = user_id
    safe_question['n_attempts'] = get_number_of_attempts(question_id, user_id)
    safe_question['previous_answers'] = get_previous_answers(question_id, user_id, 5)
    safe_question['all_answers'] = get_other_answers(question_id, user_id, exercise_key)

    return safe_question


register_question_type('pythonic', question_check_pythonic, pythonic_json_hook)
