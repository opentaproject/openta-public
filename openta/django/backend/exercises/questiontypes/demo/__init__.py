# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type demo.
"""

# Below are imports that are specific to this question type
import logging

from exercises.question import register_question_class
from exercises.questiontypes.dev_linear_algebra.linear_algebra import linear_algebra_expression
from exercises.utils import json_hook as demo_json_hook




from .demo import demo, to_latex  # The sympy interface is placed in a separate file "demo.py" in this folder

logger = logging.getLogger(__name__)


# The function below is the core of the server interface and the only mandatory component.
class Demo:

    name = "demo";
    hide_tags = ["expression","value"] 

    def __init__(self):
        pass

    @staticmethod
    def local_question_check(question_json, question_xmltree, answer_data, global_xmltree):
        return {}

    @staticmethod
    def answer_class(question_json, question_xmltree, answer_data, global_xmltree):
        return {}

    @staticmethod
    def question_class(question_json, question_xmltree, answer_data, global_xmltree):
        return {}

        #correct_answer = question_xmltree.find("expression").text.split(";")[0]
        #result = {}
        #result = demo(answer_data, correct_answer)
        #if "correct" in result:
        #    result["status"] = "correct" if result["correct"] else "incorrect"
        #elif "error" in result:
        #    result["status"] = "error"
        ## Add the sympy representation in latex form for possible visual checks
        ## latex = { 'latex': '' } #to_latex(answer_data) }
        ## result.update(latex)
        #return result
    
    @staticmethod
    def json_hook(*args):
        return demo_json_hook(*args)
        




# This function call registers the question type with the system
register_question_class(Demo)
