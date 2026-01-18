# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type linearAlgebra.
"""

import logging

from exercises.question import register_question_class
from exercises.questiontypes.matrix import MatrixQuestionOps


# from exercises.questiontypes.linear_algebra import ( linear_algebra_expression as old_linear_algebra_expression,)
from exercises.utils import json_hook as linear_algebra_json_hook


logger = logging.getLogger(__name__)


class DevLinearAlgebra:
    name = "devLinearAlgebra"
    hide_tags = ["expression", "value"]

    def __init__(self):
        pass

    @staticmethod
    def local_question_check( *args,**kwargs):
        return   MatrixQuestionOps().answer_check(*args,*kwargs)

    @staticmethod
    def answer_class( *args,**kwargs):
        return   MatrixQuestionOps().answer_check(*args,*kwargs)

    def validate_question(*args,**kwargs) :
        return MatrixQuestionOps().validate_question(*args, **kwargs)

    def json_hook(*args,**kwargs):
        return MatrixQuestionOps().json_hook(*args,**kwargs) 

def compare_expressions(  *args, **kwargs ):
        #
        #  This is only used to validate questions. Separate validation is done in type basic
        # so that this becomes a stub
        #
        return  MatrixQuestion.compare_expressions( *args, **kwargs)





register_question_class(DevLinearAlgebra)
