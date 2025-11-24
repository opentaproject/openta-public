# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander


from django.test import TestCase
import pytest
from exercises.questiontypes.matrix import MatrixQuestionOps 
from exercises.questiontypes.matrix.matrix  import IS_CORRECT
from sympy import Matrix
from exercises.parsing import exercise_xml_to_json 
from lxml import etree
import os

def thispath():
    cwd = os.getcwd()
    thisdir =  os.path.dirname( os.getenv('PYTEST_CURRENT_TEST').split('::')[0] )
    head = cwd.split('exercises')[0];
    tail = thisdir.split('exercises')[1];
    path = f"{head}/exercises/{tail}"
    return path

class Test5_Matrix(TestCase, MatrixQuestionOps):


    def test_validate_matrix_entries(self) :
        exerciseassetpath = thispath()
        global_xml = " <global> G = [ [1,2,3 ],[4,5,6]] </global>"
        global_xmltree = etree.fromstring( global_xml);
        question1 =  "<question key=\"key2\"> <expression> 2 </expression> <iscorrect>G[1,2] </iscorrect> <istrue>$$ == G[1,2] </istrue> <istrue> $$ == ( [1,2] )[2] </istrue> <istrue> ( [ $$ , 3  ] )[1]  == ( [ G[1,1] , G[1,2]]  )[2] </istrue>  </question>"
        for question_xml in [question1] :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "key2";
            question_json['@attr']['type'] ="matrix"
            R  = list( self.validate_question(question_json, question_xmltree, global_xmltree))
            print(f"R = {R}")
            #(success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( R[0] == 'success' )


