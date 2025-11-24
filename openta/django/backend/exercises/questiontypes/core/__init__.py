# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type core.
"""

# Below are imports that are specific to this question type
import logging
from .core import CoreQuestionOps 
from django.conf import settings
from exercises.question import register_question_class
logger = logging.getLogger(__name__)


class CoreQuestion(CoreQuestionOps):

    name =  "core"
    hide_tags  = ["expression","value"]; 

    def __init__(self):
        super(CoreQuestion, self).__init__()

    @staticmethod
    def answer_class( *args,**kwargs):
        #print(f"CORE_ANSWER_CLASS")
        return   CoreQuestionOps().answer_class(*args,*kwargs)



    @staticmethod
    def local_question_check( *args,**kwargs):
        if settings.RUNNING_DEVSERVER :
            #print(f"BASIC LOCAL_ANSWER_CHECK")
            pass
        res = CoreQuestionOps().answer_check(*args,*kwargs)
        #print(f"RES = {res}")
        return res

    def validate_question(*args,**kwargs) :

        if settings.RUNNING_DEVSERVER :
            #print(f" BASIC VALIDATE_QUESTION")
            pass
        return CoreQuestionOps().validate_question(*args, **kwargs)

    def json_hook(*args,**kwargs):
        if settings.RUNNING_DEVSERVER :
            #print(f"BASIC JSON_HOOK")
            pass
        return CoreQuestionOps().json_hook(*args,**kwargs)

    def compare_expressions(  *args, **kwargs) :
        if settings.RUNNING_DEVSERVER :
            pass
            #print(f"BASIC_COMPARE_EXPRESSION")
        return CoreQuestionOps().check_expressions( *args, **kwargs)

def compare_expressions(  *args, **kwargs ):
        #
        #  This is only used to validate questions. Separate validation is done in type core
        # so that this becomes a stub
        #
        if settings.RUNNING_DEVSERVER :
            pass
            #print(f"BASIC COMPARE_EXPRESSIONS_BASIC IN INIT")
        return  CoreQuestion.compare_expressions( *args, **kwargs)


register_question_class(CoreQuestion)
