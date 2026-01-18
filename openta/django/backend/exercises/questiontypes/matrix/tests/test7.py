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

class Test5_Cross(TestCase, MatrixQuestionOps):


    def test_validate_cross(self) :
        global_xml = " <global> xhat = [1,0,0]; yhat = [0,1,0]; zhat = [0,0,1] </global>"
        global_xmltree = etree.fromstring( global_xml);
        question1 = "<question key='key2'>\
                <expression>[[1,0,0],[0,1,0],[0,0,1]] </expression>\
                <iscorrect>[[1,0,0],[0,1,0], zhat]  </iscorrect>\
                <iscorrect>[xhat,yhat, cross( xhat,yhat) ]  </iscorrect>\
                <iscorrect>[xhat,yhat, cross( [1,0,0] ,yhat) ]  </iscorrect>\
                <iscorrect>[xhat, cross(zhat , xhat ),  cross( xhat,cross( zhat,xhat) ) ]  </iscorrect>\
                <iscorrect>[ [1,0,0] , cross(zhat , xhat ),  cross( xhat,cross( zhat,xhat) ) ]  </iscorrect>\
                <iscorrect>[ [1,0,0] , cross(zhat , [1,0,0]  ),  cross( xhat,cross( zhat,xhat) ) ]  </iscorrect>\
                <istrue>AreOrthogonal( $$ ) </istrue>\
                </question>"



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


