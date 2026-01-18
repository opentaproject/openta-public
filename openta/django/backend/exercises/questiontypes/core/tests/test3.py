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
        global_xml = "  <global>  <vars>x,y,z,r,s</vars> <blacklist><token> f </token> </blacklist>  f(r,s) := r^2 s; g(y,z) := y sin(z) ; </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f" <question key=\"0\" type=\"default\"> <expression>( f(x,y) )^2 g(y,z) </expression> </question> "
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, "( f(x,y) )^2 g(y,z) ", global_xmltree  )
        print(f"R0={r}")
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "( x^2 y  )^2  y sin(z)  ", global_xmltree  )
        print(f"R1={r}")
        self.assertTrue( r.get('correct',False) );
        question_xml = f" <question key=\"0\" type=\"default\"> <vars>x,y,z</vars> <expression>   x^2 y sin(z) + 2 x y^2 sin(z)     </expression> </question> "
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, "partial( f(x,y), x ) * g(y,z) + partial(g(y,z),y ) f(x,y)   ", global_xmltree  )
        print(f"R2 = {r}")
        self.assertTrue( r.get('correct',False) );


    def test1_func(self ):
        exerciseassetpath = thispath()
        global_xml = "  <global> <vars>r,s</vars> \
            x = var(\"x\"); \
            y = var(\"y\"); \
            z = var(\"z\"); \
            f(r,s) := r^2 s; \
            g(y,z) := y sin(z) ; \
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f" <question key=\"0\" type=\"default\"> <expression>( f(x,y) )^2 g(y,z) </expression> </question> "
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, "( f(x,y) )^2 g(y,z) ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "( x^2 y  )^2  y sin(z)  ", global_xmltree  )
        print(f"R3={r}")
        self.assertTrue( r.get('correct',False) );
        question_xml = f" <question key=\"0\" type=\"default\"> <expression>   x^2 y sin(z) + 2 x y^2 sin(z)     </expression> </question> "
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, "partial( f(x,y), x ) * g(y,z) + partial(g(y,z),y ) f(x,y)   ", global_xmltree  )
        print(f"R4 = {r}")
        self.assertTrue( r.get('correct',False) );
