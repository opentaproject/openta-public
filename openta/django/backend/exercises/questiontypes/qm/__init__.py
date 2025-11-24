# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type qm.
"""

# Below are imports that are specific to this question type
import logging

from exercises.question import register_question_class
try :
    from exercises.utils.checks import parens_are_balanced, brackets_are_balanced; 
except :
    pass
from exercises.questiontypes.basic import BasicQuestion, BasicQuestionOps
from .qm import QuantumQuestionOps;





#from .qm import qm, to_latex  # The sympy interface is placed in a separate file "qm.py" in this folder

logger = logging.getLogger(__name__)


# The function below is the core of the server interface and the only mandatory component.
class Quantum( BasicQuestion ) :

    name = "qm";
    hide_tags = ["expression","value"] 

    def __init__(self):
        super( BasicQuestion,self).__init__()

    @staticmethod
    def answer_class( *args,**kwargs):
        return   QuantumQuestionOps().answer_check(*args,*kwargs)

    @staticmethod
    def local_question_check( *args,**kwargs):
        return   QuantumQuestionOps().answer_check(*args,*kwargs)

    def validate_question(*args,**kwargs) :
        return QuantumQuestionOps().validate_question(*args, **kwargs)

    #def json_hook(*args,**kwargs):
    #    return BasicQuestionOps().json_hook(*args,**kwargs)
 




# This function call registers the question type with the system
register_question_class(Quantum)
