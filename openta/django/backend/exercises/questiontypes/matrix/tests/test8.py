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


    def test_validate_1(self) :
        global_xml = "<global> <vars>u,v</vars> F(u,v ) := [ u^2 - v^2 , 2 u v ] </global>"
        global_xmltree = etree.fromstring( global_xml);
        question1 = "<question type='matrix' key='a'>  \
            <expression>[[3,-1],[-3,1]] </expression> <istrue>F($$[1,1], $$[1,2] ) == [8,-6] </istrue> <istrue>F( $$[2,1] , $$[2,2] ) == [8,-6] </istrue>\
            <istrue>dimensions( $$ ) == [2,2] <if-not-so>Shape is wrong </if-not-so> </istrue>: <isfalse>$$[1] == $$[2] <if-not-so>Don't repeat! </if-not-so>\
            </isfalse> </question>"
        question2 = "<question type='matrix' key='a'> <expression>[[0,0]] </expression> <istrue>F($$[1,1], $$[1,2] ) == [0,0] </istrue> <istrue>dimensions($$) == [1,2]  \
            <if-not-so>Shape is wrong </if-not-so> </istrue> </question>"
        question3 =  "<question type='matrix' key='a'> <expression>[[ 0 , 0 ] , [1 , 0 ] ] </expression> <istrue>F( $$[2,1], $$[2,2] )  ==  $$[2]     </istrue>\
            <istrue>F( $$[1,1], $$[1,2] )  ==   $$[1]   </istrue> </question>"
        question4 = "<question  type='matrix' key='a'> <istrue>[ $$[1,1], $$[1,2]  ] ==  $$[1] </istrue> <istrue>[ $$[2,1], $$[2,2]  ] == $$[2]  </istrue>  \
            <expression>[[1,5],[3,8]] </expression> </question>"
        question5 =  " <question key='a'> <istrue>$$ ==  [  [ $$[1,1], $$[1,2] ] , [ $$[2,1], $$[2,2]  ]]  </istrue> <istrue>$$ ==  [   $$[1], $$[2] ]  </istrue>\
            <expression>[[3333,44],[20,9] ] </expression> </question>"
        i = 0;
        for question_xml in [question1, question2, question3 , question4, question5] : 
            print(f"INDEX = {i}")
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "a";
            question_json['@attr']['type'] ="matrix"
            R  = list( self.validate_question(question_json, question_xmltree, global_xmltree))
            print(f"INDEX = {i} R = {R}")
            self.assertTrue( R[0] == 'success' )
            i = i + 1 ;





    def test_validate_2(self) :
        global_xml = "<global> <oneforms>dx,dy,dz</oneforms> <vars>v1, v2, v3 ,g </vars> d(g) := dD( g , [dx,dy,dz],[x,y,z],[v1,v2,v3] ); </global>"
        global_xmltree = etree.fromstring( global_xml);
        question1 = " <question key='a'> <istrue>$$ == dD( 2 x + 3 y , [dx,dy,dz], [x,y,z] , [v1,v2,v3] ) </istrue> <istrue>$$ == d(2 x + 3 y ) </istrue> <expression>2 v1 + 3 v2 </expression> </question>"
        question2 = " <question key='a'> <istrue>$$ == dD( [ 2 x + 3 y, 4 x + 5 y ]  , [dx,dy,dz], [x,y,z] , [v1,v2,v3] ) </istrue> <istrue>$$ == d([ 2 x + 3 y, 4 x + 5 y ]  ) </istrue> <expression>[ 2 v1 + 3 v2 , 4 v1 + 5 v2 ].T </expression> </question>"
        question3 = " <question key='a'> <istrue>$$ == dD( 2 x + 3 y , [dx,dy,dz], [x,y,z] , [[1,0,0],[0,1,0],[0,0,1]] ) </istrue> <expression>[2,3,0] </expression> </question>"
        i = 0;
        for question_xml in [question1, question2, question3] : 
            print(f"INDEX = {i}")
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "a";
            question_json['@attr']['type'] ="matrix"
            R  = list( self.validate_question(question_json, question_xmltree, global_xmltree))
            print(f"INDEX = {i} R = {R}")
            self.assertTrue( R[0] == 'success' )
            i = i + 1 ;




    def test_validate_3(self) :
        global_xml = " <global> <oneforms>dx,dy,dz</oneforms> <vars>v1, v2, v3 ,g , w </vars> d(g) := dD( g , [dx,dy,dz],[x,y,z],[v1,v2,v3] ); fg(w) :=   [ w[1] + w[2], w[1] - w[2]  ]</global>"
        global_xmltree = etree.fromstring( global_xml);
        question1 = "  <question  key='a'> <iscorrect>fg([1,1] ) </iscorrect> <expression>[2,0] </expression> </question>"
        question2 = " <question key='a'> <istrue>$$ == dD( [ 2 x + 3 y, 4 x + 5 y ]  , [dx,dy,dz], [x,y,z] , [v1,v2,v3] ) </istrue> <istrue>$$ == d([ 2 x + 3 y, 4 x + 5 y ]  ) </istrue> <expression>[ 2 v1 + 3 v2 , 4 v1 + 5 v2 ].T </expression> </question>"
        question3 = " <question key='a'> <istrue>$$ == dD( 2 x + 3 y , [dx,dy,dz], [x,y,z] , [[1,0,0],[0,1,0],[0,0,1]] ) </istrue> <expression>[2,3,0] </expression> </question>"
        i = 0;
        for question_xml in [question1, question2, question3] : 
            print(f"INDEX = {i}")
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "a";
            question_json['@attr']['type'] ="matrix"
            R  = list( self.validate_question(question_json, question_xmltree, global_xmltree))
            print(f"INDEX = {i} R = {R}")
            self.assertTrue( R[0] == 'success' )
            i = i + 1 ;



