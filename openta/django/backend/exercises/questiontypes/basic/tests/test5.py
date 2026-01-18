# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander


from unittest import TestCase
from exercises.questiontypes.basic import BasicQuestionOps 
from exercises.questiontypes.basic.basic  import IS_CORRECT
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


class Test1_Basic(TestCase, BasicQuestionOps):

    def test_validate_isfalse_1( self ):
        q = BasicQuestionOps()
        exerciseassetpath = thispath()
        global_xml = "  <global> <oneforms>dx,dy,dz</oneforms> </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key='randomkey1'>  <expression> - dx dy  </expression>  <isincorrect> dx dy </isincorrect> <iscorrect> Wedge( dy dx ) </iscorrect> </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "randomkey1";
        question_json['@attr']['type'] ="basic"
        r  = self.validate_question(question_json, question_xmltree, global_xmltree)
        print(f"TEST R = {r}")
        (success,msg) = r
        self.assertTrue( success == 'success' )
        r =  self.answer_check(  question_json, question_xmltree, "-dx dy ", global_xmltree  )
        print(f"RETURN FALSE {r}")
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "dy dx", global_xmltree  )
        print(f"R = {r}")
        self.assertFalse( r.get('correct',True) );
