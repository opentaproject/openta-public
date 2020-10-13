'''
This is the server side implementation of the question type symbolic.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError
from .symbolic import question_check
from exercises.questiontypes.dev_linear_algebra import linear_algebra_json_hook

# Below are imports that are specific to this question type


import logging
import re



from .symbolic import symbolic_expression
#from .symbolic import symbolic_expression_blocking
from exercises.questiontypes.symbolic.variableparser import get_used_variable_list, getallvariables

# from exercises.questiontypes.symbolic.parsehints import parsehints
from exercises.question import get_number_of_attempts, get_previous_answers
from exercises.questiontypes.symbolic.variableparser import (
    get_more_variables_from_obj,
    get_functions_from_obj,
    remove_blacklist_variables_from_obj,
 )

logger = logging.getLogger(__name__)




def question_check_symbolic(question_json, question_xmltree, answer_data, global_xmltree):
    return question_check(
        question_json, question_xmltree, answer_data, global_xmltree, symbolic_expression
    )


def symbolic_json_hook( *args ):
    return linear_algebra_json_hook( *args )



# This function call registers the question type with the system
register_question_type(
    'symbolic', question_check_symbolic, symbolic_json_hook, hide_tags=['expression', 'value'],
)

