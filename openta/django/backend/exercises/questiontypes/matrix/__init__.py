# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type matrix.
"""

# Below are imports that are specific to this question type
import logging
from .matrix import BaseMatrixQuestionOps
from .matrixify import ExtraMethods
from exercises.question import register_question_class
logger = logging.getLogger(__name__)

class MatrixQuestionOps(BaseMatrixQuestionOps, ExtraMethods):
    pass

class MatrixQuestion(MatrixQuestionOps):

    name =  "matrix"
    hide_tags  = ["expression","value"]; 

    def __init__(self):
        super(MatrixQuestion, self).__init__()

    @staticmethod
    def local_question_check( *args,**kwargs):
        #print(f"LOCAL_QUESTION_CHECK_MATRIX")
        return   MatrixQuestionOps().answer_check(*args,*kwargs)

    @staticmethod
    def answer_class( *args,**kwargs):
        #print(f"LOCAL_QUESTION_CHECK_MATRIX")
        return   MatrixQuestionOps().answer_check(*args,*kwargs)

    def validate_question(*args,**kwargs) :
        #print(f"VALIDATE_QUESTION_MATRIX") 
        return MatrixQuestionOps().validate_question(*args, **kwargs)

    def json_hook(*args,**kwargs):
        #print(f"JSON_HOOK MATRIX")
        return MatrixQuestionOps().json_hook(*args,**kwargs) 
    
    def compare_expressions(  *args, **kwargs) :
        #print("COMPARE EXPRESSIONS MATRIX")
        return MatrixQuestionOps().check_expressions( *args, **kwargs)

def compare_expressions(  *args, **kwargs ):
    #print(f"COMPARE_EXPRESSIONS MATRIX")
    #
    #  This is only used to validate questions. Separate validation is done in type basic
    # so that this becomes a stub
    #
    return  MatrixQuestion.compare_expressions( *args, **kwargs)






register_question_class(MatrixQuestion)
