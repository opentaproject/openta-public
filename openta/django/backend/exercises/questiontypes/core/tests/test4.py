# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from unittest import TestCase
from exercises.questiontypes.core import CoreQuestionOps 
from exercises.questiontypes.core.core  import IS_CORRECT
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


class Test1_Core(TestCase, CoreQuestionOps):

    def test0_func(self ):
        exerciseassetpath = thispath()
        global_xml = "<global> <vars> x,y,z,q </vars> \
            fn = sin(x y ) + x y cos(x y) -  z y sin( x z );\
            h = x^2 + y^2 + z^2;\
            g =  exp(h );\
            f = sin(g);\
            F(q) := sin(q);\
            G(q) := exp( q );\
        </global>"
        global_xmltree = etree.fromstring( global_xml);
        full_question = {};
        full_question['@attr'] = {}
        full_question['@attr']['key'] = "randomkey1";
        full_question['@attr']['type'] ="core"
        full_question['is_staff'] = True;
        full_question["exposeglobals"] = False;
        full_question["feedback"] = True;
        full_question["expression"] = {}
        full_question["expression"]['$'] = '2 exp( x^2 + y^2 + z^2 ) x cos( exp( x^2 + y^2 + z^2) )'
        full_question["vars"] = {}
        full_question["vars"]['$'] = "f,G,F,h"
        safe_question = self.json_hook(   full_question, full_question, '1', '1' ,'exercise_key', feedback=True) 
        safe_question['is_staff'] = True ;
        question_xml = f" <question key=\"0\" type=\"default\"><vars>f,G,F,h</vars> <expression> 2 exp( x^2 + y^2 + z^2 ) x cos( exp( x^2 + y^2 + z^2) ) </expression> </question> "
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  safe_question , question_xmltree, "2 exp( x^2 + y^2 + z^2 ) x cos( exp( x^2 + y^2 + z^2) ) ", global_xmltree  )
        print(f"R0={r}")
        self.assertTrue( r.get('correct',False) );


        r =  self.answer_check(  safe_question , question_xmltree, " partial(f,x) ", global_xmltree  )
        print(f"R0={r}")
        self.assertTrue( r.get('correct',False) );


        r =  self.answer_check(  safe_question , question_xmltree, " F'(g) partial(g,x) ", global_xmltree  )
        print(f"R0={r}")
        self.assertTrue( r.get('correct',False) );


        r =  self.answer_check(  safe_question , question_xmltree, " F'(g) G'(h) partial(h,x) ", global_xmltree  )
        print(f"R0={r}")
        self.assertTrue( r.get('correct',False) );



        safe_question['is_staff'] = False ;
        question_xml = f" <question key=\"0\" type=\"default\"><vars>f,G,F,h</vars> <expression> 2 exp( x^2 + y^2 + z^2 ) x cos( exp( x^2 + y^2 + z^2) ) </expression> </question> "
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  safe_question , question_xmltree, "2 exp( x^2 + y^2 + z^2 ) x cos( exp( x^2 + y^2 + z^2) ) ", global_xmltree  )
        print(f"R0={r}")
        self.assertTrue( r.get('correct',False) );


        r =  self.answer_check(  safe_question , question_xmltree, " partial(f,x) ", global_xmltree  )
        print(f"R0={r}")
        self.assertTrue( r.get('correct',False) );


        r =  self.answer_check(  safe_question , question_xmltree, " F'(g) partial(g,x) ", global_xmltree  )
        print(f"R0={r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue(  'Not valid variables' in r.get('warning','') )


        r =  self.answer_check(  safe_question , question_xmltree, " F'(g) G'(h) partial(h,x) ", global_xmltree  )
        print(f"R0={r}")
        self.assertFalse( r.get('correct',False) );


