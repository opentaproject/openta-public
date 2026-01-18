# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from unittest import TestCase
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

class Test1_Matrix(TestCase, MatrixQuestionOps):

    def test1_1_2(self) :
        exerciseassetpath = thispath()
        global_xml = "<global><vars>x,y,z</vars><blacklist>ans</blacklist> U1 = [1,0,0]; U2 = [0,1,0]; U3 = [0,0,1]; V = x U1 + y U2; W = 2 x^2 U2 - U3; ans(x,y,z) := W - x V; </global>";
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);

        question_xml = "<question key=\"randomkey1\" type=\"matrix\">  <expression>  ans(x,y,z)  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " - x^2 U1 + ( 2 x^2 - x  y ) U2 - U3  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );


        question_xml = "<question key=\"randomkey1\" type=\"matrix\">  <expression>  ans(x,y,z)  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " - x^2 U1 + ( 2 x^2 - x  y ) U2 - U3 * 5   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );


        question_xml = "<question key=\"randomkey1\" type=\"matrix\">  <expression>  ans(-1,0,2)  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " - U1 + 2 U2 - U3   ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );


        question_xml = "<question key=\"randomkey1\" type=\"matrix\">  <expression>  ans(-1,0,2)  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " - U1 + 2 U2 - U3  * 4  ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );

