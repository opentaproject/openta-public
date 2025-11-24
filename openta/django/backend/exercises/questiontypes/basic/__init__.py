# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type basic.
"""

# Below are imports that are specific to this question type
import logging
from .basic import BasicQuestionOps 
from django.conf import settings
from exercises.question import register_question_class
logger = logging.getLogger(__name__)


class BasicQuestion(BasicQuestionOps):

    name =  "basic"
    hide_tags  = ["expression","value"]; 

    def __init__(self):
        super(BasicQuestion, self).__init__()

    @staticmethod
    def local_question_check( *args,**kwargs):
        return   BasicQuestionOps().answer_check(*args,*kwargs)

    @staticmethod
    def answer_class( *args,**kwargs):
        if settings.RUNNING_DEVSERVER :
            #print(f"BASIC LOCAL_ANSWER_CHECK")
            pass
        return   BasicQuestionOps().answer_class(*args,*kwargs)


    def validate_question(*args,**kwargs) :

        if settings.RUNNING_DEVSERVER :
            #print(f" BASIC VALIDATE_QUESTION")
            pass
        return BasicQuestionOps().validate_question(*args, **kwargs)

    def json_hook(*args,**kwargs):
        if settings.RUNNING_DEVSERVER :
            #print(f"BASIC JSON_HOOK")
            pass
        return BasicQuestionOps().json_hook(*args,**kwargs)

    def compare_expressions(  *args, **kwargs) :
        if settings.RUNNING_DEVSERVER :
            pass
            #print(f"BASIC_COMPARE_EXPRESSION")
        return BasicQuestionOps().check_expressions( *args, **kwargs)

def compare_expressions(  *args, **kwargs ):
        #
        #  This is only used to validate questions. Separate validation is done in type basic
        # so that this becomes a stub
        #
        if settings.RUNNING_DEVSERVER :
            pass
            #print(f"BASIC COMPARE_EXPRESSIONS_BASIC IN INIT")
        return  BasicQuestion.compare_expressions( *args, **kwargs)


register_question_class(BasicQuestion)
