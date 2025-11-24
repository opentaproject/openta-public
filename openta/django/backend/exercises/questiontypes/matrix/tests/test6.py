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

class validate_matrix_entries_simple(TestCase, MatrixQuestionOps):


    def test_validate_matrix_entries_simple(self) :
        exerciseassetpath = thispath()
        global_xml = "<global> \
            g = [ [1,2,3 ],[4,5,6]] \
            </global>"

        global_xmltree = etree.fromstring( global_xml);
        question1 = '<question type="matrix" key="key2"> <iscorrect>g[1,2] </iscorrect> <istrue>$$ == g[1,2] </istrue> <istrue>$$ == ( [1,2] )[2] </istrue> <istrue>( [ $$ , $$  ] )[1]  == ( [ g[1,1] , g[1,2]]  )[2] </istrue> <expression>2 </expression> </question>'

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




    def test_list_assignment(self) :
        exerciseassetpath = thispath()
        global_xml = " <global> p = [0,-2,1]; [x,y,z] = p; v = [1,2,-3]; [dx,dy,dz] = v  </global> "
        global_xmltree = etree.fromstring( global_xml);
        question1 =  '  <question type="matrix" key="key2"> <expression>4 </expression> <iscorrect>y^2 * dx </iscorrect> </question>'
        question2 =  ' <question type="matrix" key="key2">  <expression>- 4 </expression> <iscorrect>z dy - y dz  </iscorrect> </question>'
        question3 =  ' <question type="matrix" key="key2">   <expression>-2  </expression> <iscorrect>( z^2 - 1 ) dx - dy + x^2 dz  </iscorrect> </question>'
        for question_xml in [question1,question2,question3] :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "key2";
            question_json['@attr']['type'] ="matrix"
            R  = list( self.validate_question(question_json, question_xmltree, global_xmltree))
            print(f"R = {R}")
            #(success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( R[0] == 'success' )

    def test_1_5_3(self) :
        exerciseassetpath = thispath()
        global_xml = " <global> <vars>x,y,z,U1,U2,U3,v </vars> V = x U1 + y U2 + z U3; W = x y ( U1 - U3 ) + y z (U1 - U2 ); X = 1/x V + 1 /y W; dx(v) := D(v,U1 ); dy(v) := D(v, U2 ); dz(v) := D(v, U3); phi(v) := x^2 dx(v) - y^2 dz(v) </global>"
        global_xmltree = etree.fromstring( global_xml);
        question1 =  ' <question key="key2">  <expression>x^3 - y^2 z </expression> <iscorrect>phi(V) </iscorrect> </question>'
        question2 =  ' <question key="key2">  <expression>x*y^3 + x^2*(x*y + y*z) </expression> <iscorrect>phi(W) </iscorrect> </question>'
        question3 =  ' <question key="key2">  <expression>x^3 + x*y^2 - (y^2*z)/x + x^2*(1 + z) </expression> <iscorrect>phi(X) </iscorrect> </question> '
        for question_xml in [question1,question2,question3] :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "key2";
            question_json['@attr']['type'] ="matrix"
            R  = list( self.validate_question(question_json, question_xmltree, global_xmltree))
            print(f"R = {R}")
            #(success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( R[0] == 'success' )


    def test_perspective(self) :
        exerciseassetpath = thispath()
        global_xml = "<global> d = .234234; n = [1.0,3.0,4.0]; Zhat = [0.0,0.0,1.0]; p = [0.1923,0.9752,0.71333]; nhat = n / abs(n); xhat = cross( n, Zhat ) / | cross( n, Zhat ) |; yhat = cross( n, cross( n, Zhat ) ) / | cross( n, cross( n, Zhat) ) | </global>" 
        global_xmltree = etree.fromstring( global_xml);
        question1 =  '<question key="key2"> <expression>d / dot( p - n, nhat ) [ dot( p , xhat), dot( p , yhat ) ] </expression> </question> '
        for question_xml in [question1] :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "key2";
            R  = list( self.validate_question(question_json, question_xmltree, global_xmltree))
            print(f"R = {R}")
            #(success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( R[0] == 'success' )

