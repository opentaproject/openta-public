# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type matrix.
"""

import logging
from exercises.questiontypes.matrix import MatrixQuestionOps, MatrixQuestion
from exercises.questiontypes.basic import BasicQuestion
from exercises.questiontypes.qm import Quantum
from exercises.utils import json_hook  as default_json_hook
from exercises.question import register_question_class
from django.conf import settings

from exercises.question import (  # This function is used to register the question type
    get_number_of_attempts,
    get_safe_previous_answers,
)
from exercises.utils.variableparser import (
    get_more_functions_from_obj,
    get_more_variables_from_obj,
    get_used_variable_list,
    remove_blacklist_variables_from_obj,
)



logger = logging.getLogger(__name__)

qclass = {};
qclass['basic'] = BasicQuestion
qclass['matrix'] =  MatrixQuestion
qclass['qm'] = Quantum
qclass['default'] = MatrixQuestion
qclass['Numeric'] = BasicQuestion
qclass['symbolic'] = MatrixQuestion
qclass['linearAlgebra'] = MatrixQuestion


class DefaultQuestion():

    name =  "default"
    hide_tags  = ["expression","value"]; 

    def __init__(self):
        if settings.RUNNING_DEVSERVER :
            pass
            #logger.info(f"DEFAULT INIT")
        BasicQuestion(BasicQuestion, self).__init__()

    @staticmethod
    def local_question_check( question_json, question_xmltree,txt,global_xmltree ):
        qtype = question_json.get('qtype','default');
        if settings.RUNNING_DEVSERVER :
            exercise_key = question_json.get('exercise_key');
            question_key = question_json.get('question_key');
            db = question_json.get('db');
            logger.info(f" DEFAULT_EXERCISE_KEY = {exercise_key} QUESTION_KEY={question_key} DB={db}");
            logger.info(f"DEFAULT LOCAL_QUESTION_CHECK {qtype} ")
        return   qclass[qtype].local_question_check(question_json, question_xmltree,txt,global_xmltree)

    @staticmethod
    def answer_class( question_json, question_xmltree,txt,global_xmltree ):
        qtype = question_json.get('qtype','default');
        if settings.RUNNING_DEVSERVER :
            exercise_key = question_json.get('exercise_key');
            question_key = question_json.get('question_key');
            db = question_json.get('db');
            #print(f" DEFAULT_EXERCISE_KEY = {exercise_key} QUESTION_KEY={question_key} DB={db}");
            #print(f"DEFAULT LOCAL_QUESTION_CHECK {qtype} ")
        return   qclass[qtype].local_question_check(question_json, question_xmltree,txt,global_xmltree)

    
    @staticmethod
    def compare_expressions( question_json, question_xmltree,txt,global_xmltree ):
        qtype = question_json.get('qtype','default');
        if settings.RUNNING_DEVSERVER :
            exercise_key = question_json.get('exercise_key');
            question_key = question_json.get('question_key');
            db = question_json.get('db');
            logger.info(f" DEFAULT_EXERCISE_KEY = {exercise_key} QUESTION_KEY={question_key} DB={db}");
            logger.info(f"DEFAULT COMPARE_EXPRESSIONS  {qtype}   ")
        return   qclass[qtype].compare_expressions(question_json, question_xmltree,txt,global_xmltree )


    def validate_question(question_json, question_xmltree,global_xmltree ):
        qtype = question_json.get('qtype','default');
        if settings.RUNNING_DEVSERVER :
            exercise_key = question_json.get('exercise_key');
            question_key = question_json.get('question_key');
            db = question_json.get('db');
            logger.info(f" DEFAULT_EXERCISE_KEY = {exercise_key} QUESTION_KEY={question_key} DB={db}");
            logger.info(f"DEFAULT VALIDATE_QUESTION {qtype} ")
        return qclass[qtype].validate_question(question_json, question_xmltree,global_xmltree )

    def json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback, db=None ):
        qtype = full_question.get('qtype','default');
        exercise_key = full_question.get('exercise_key');
        question_key = full_question.get('question_key');
        db = full_question.get('db');
        logger.info(f" DEFAULT_EXERCISE_KEY = {exercise_key} QUESTION_KEY={question_key} DB={db}");
        logger.info(f"DEFAULT_JSON_HOOK {qtype} ")
        res = qclass[qtype].json_hook( safe_question, full_question, question_id, user_id, exercise_key, feedback)
        return res



def compare_expressions(  *args, **kwargs ):
        if settings.RUNNING_DEVSERVER :
            pass
            #exercise_key = question_json.get('exercise_key');
            #question_key = question_json.get('question_key');
            #db = question_json.get('db');
            #logger.info(f" DEFAULT_EXERCISE_KEY = {exercise_key} QUESTION_KEY={question_key} DB={db}");
            #logger.info(f"DEFAULT COMPARE_EXPRESSIONS")
            #logger.info(f"args = {args}")
            #logger.info(f"kwargs = {kwargs}")
        qtype = safe_question.get('qtype');
        return  qclass[qtype].compare_expressions( *args, **kwargs)




register_question_class(DefaultQuestion)
