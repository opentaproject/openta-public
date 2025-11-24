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

class Test1_Set(TestCase, MatrixQuestionOps):

    def setup(self):
        self.MatrixQuestionOps = MatrixQuestionOps().__init__()

    def test1_simple(self) :
        self.__init__()
        exerciseassetpath = thispath()
        global_xml = "<global> \
            </global>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"randomkey5\" type=\"matrix\">  <expression> set(1,2)  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " [1,2] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " [2,1] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "set(2,1)", global_xmltree  )
        self.assertTrue( r.get('correct',False) );

    def test2_simple(self) :
        self.__init__()
        exerciseassetpath = thispath()
        global_xml = "<global> \
            k = 1.234 ;  \
            mm = .7711;  \
            theta = pi/3.98234 \
            </global>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"randomkey6\" type=\"matrix\">  <expression> set( k/mm ( 1 - cos(theta) ) , k/mm ( 1 + cos(theta ) ) )  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " k/mm [ 1 - cos(theta), 1 + cos(theta) ] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " k/mm [ 1 + cos(theta), 1 - cos(theta) ]  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " set( k/mm ( 1 + cos(theta) ) , k/mm (  1 - cos(theta) ) ) ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " set( k/mm ( 1 - cos(theta) ) , k/mm (  1 + cos(theta) ) ) ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " [  ( k +  k cos(theta) ) / mm ,  ( k   -  k cos(theta)  ) / mm  ]   ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " [  ( k/mm +  k/mm cos(theta) )  ,  ( k/mm   -  k/mm cos(theta)  )   ]   ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );


    def test3_simple(self) :
        self.__init__()
        exerciseassetpath = thispath()
        global_xml = "<global> \
            k = 1.234 ;  \
            mm = .7711;  \
            theta = pi/3.98234 ;\
            </global>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"randomkey7\" type=\"matrix\">  <expression> set( [  k/mm ( 1 + cos(theta) ) , k/mm ( 1 - cos(theta) )  ] ) </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " k/mm [ 1 - cos(theta), 1 + cos(theta) ] ", global_xmltree  )
        r =  self.answer_check(  question_json, question_xmltree, " k/mm [ 1 - cos(theta), 1 + cos(theta) ] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " k/mm [ 1 + cos(theta), 1 - cos(theta) ]  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " set( k/mm ( 1 + cos(theta) ) , k/mm (  1 - cos(theta) ) ) ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " set( k/mm ( 1 - cos(theta) ) , k/mm (  1 + cos(theta) ) ) ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " [  ( k +  k cos(theta) ) / mm ,  ( k   -  k cos(theta)  ) / mm  ]   ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " [  ( k/mm +  k/mm cos(theta) )  ,  ( k/mm   -  k/mm cos(theta)  ),  ( k/mm   -  k/mm cos(theta)  )     ]   ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " [  ( k/mm +  k/mm cos(theta) )  ,  ( k/mm   -  k/mm cos(theta)  ),  ( k/mm   -  2 k/mm cos(theta)  )     ]   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );


    def test4_simple(self) :
        exerciseassetpath = thispath()
        global_xml = "<global> \
            k = 1.234 ;  \
            mm = .7711;  \
            theta = pi/3.98234 ;\
            </global>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"randomkey4\" type=\"matrix\">  <expression> set( [  k/mm ( 1 + cos(theta) ) , 2 k/mm ( 1 - cos(theta) )  ] ) </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " k/mm [ 1 - cos(theta), 1 + cos(theta) ] ", global_xmltree  )
        self.assertFalse( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " k/mm [ 1 + cos(theta), 1 - cos(theta) ]  ", global_xmltree  )
        self.assertFalse( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " set( [ k/mm ( 1 + cos(theta) ) , k/mm (  1 - cos(theta) ) ] ) ", global_xmltree  )
        self.assertFalse( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " set( k/mm ( 1 - cos(theta) ) , k/mm (  1 + cos(theta) ) ) ", global_xmltree  )
        self.assertFalse( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [  ( k +  k cos(theta) ) / mm ,  ( k   -  k cos(theta)  ) / mm  ]   ", global_xmltree  )
        self.assertFalse( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [  ( k/mm +  k/mm cos(theta) )  ,  ( k/mm   -  k/mm cos(theta)  )   ]   ", global_xmltree  )
        self.assertFalse( r.get('correct',None) );

