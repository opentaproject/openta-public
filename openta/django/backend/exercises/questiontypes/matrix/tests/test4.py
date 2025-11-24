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

class Test4_Matrix(TestCase, MatrixQuestionOps):




    def test_validate_scalar1( self ):

        exerciseassetpath = thispath()
        global_xml = " <global> z = sample(  33 / 31.0 , - 34 / 32.0)   </global>";
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question type=\"matrix\" key=\"randomkey1\">\
            <expression>exp( - abs(z) )</expression>\
            <iscorrect> exp( - sqrt( z * z ) )</iscorrect>\
            <isincorrect> exp( - z ) </isincorrect>\
            <iscorrect> exp( - abs(z) ) </iscorrect>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "randomkey1";
        question_json['@attr']['type'] ="matrix"
        (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
        self.assertTrue( success == 'success' )


    def test_validate_matrix_mess( self ):

        exerciseassetpath = thispath()

        global_xml = " <global>\
            e1 =  [1,1,0 ]; \
            e2 = [1,-1,1]; \
            e3 = [1,-1,-2]; \
            f1 = [1,0,1]; \
            f2 = [-1,2,1]; \
            f3 = [-1,-1,1]; \
            m1 = ( e1 / | e1 | );\
            m2 = ( e2 / | e2 | );\
            m3 = ( e3 / | e3 | );\
            v1 = m1;\
            v2 = m2;\
            v3 = m3;\
            n1 = f1 / | f1 |;\
            n2 = f2 / | f2 |;\
            n3 = f3 / | f3 |;\
            w1 = n1;\
            w2 = n2;\
            w3 = n3;\
            Me = [  m1 , m2 , m3  ];\
            Mf = [  n1 , n2 , n3  ];\
            x1 = [1,0,0];\
            x2 = [0,1,0];\
            x3 = [0,0,1 ];\
            </global> "
        

        
        question_xml_1 = f"<question key=\"mf\" type=\"matrix\">\
            <istrue> Rank( $$ ) == 3 \
              <if-not-so> Rank must be 3 </if-not-so>\
            </istrue>\
            <istrue> Transpose( $$ ) * $$ == [[1,0,0],[0,1,0],[0,0,1]] \
              <if-not-so> Matrix is not orthgonal </if-not-so>\
            </istrue>\
            <istrue> x1 == $$ * ( v1 ) ; \
              <if-not-so> The matrix does not map e1 into v1 </if-not-so>\
            </istrue>\
            <istrue> x2 == $$ * ( v2 ) ; \
              <if-not-so> The matrix does not map e2 into v2 </if-not-so>\
            </istrue>\
            <istrue> x3 == $$ * ( v3 )  \
              <if-not-so> The matrix does not map e3 into v3 </if-not-so>\
            </istrue>\
            <expression> [m1,m2,m3]  </expression>\
          </question>"

        question_xml_2 = "<question key=\"mf\" type=\"default\">\
            <istrue> Rank( $$ ) == 3 \
              <if-not-so> Rank must be 3 </if-not-so>\
            </istrue>\
            <istrue> Transpose( $$ ) * $$ == [[1,0,0],[0,1,0],[0,0,1]] \
              <if-not-so> Matrix is not orthgonal </if-not-so>\
            </istrue>\
            <istrue> x1 == $$ * ( w1 )   <if-not-so> The matrix does not map f1 into w1 </if-not-so>\
            </istrue>\
            <istrue> x2 == $$ * ( w2 ) \
              <if-not-so> The matrix does not map f2 into w2 </if-not-so>\
            </istrue>\
            <istrue> x3 == $$ * ( w3 ) \
              <if-not-so> The matrix does not map f3 into w3 </if-not-so>\
            </istrue>\
            <expression> [n1,n2,n3]  </expression>\
          </question>"
          
        question_xml_3 = "<question key=\"randomkey2\" type=\"matrix\">\
            <blacklist>\
              <token> Me </token>\
            </blacklist>\
            <variables> Qe = [m1,m2,m3] ; Qf = [n1,n2,n3]  </variables>\
            <istrue> $$ == Transpose( Me ) * Mf </istrue>\
            <expression> Transpose( Me ) * Mf ; </expression>\
            <istrue> Transpose( $$ ) * $$ == [[1,0,0],[0,1,0],[0,0,1]] \
              <if-not-so> Matrix is not orthgonal </if-not-so>\
            </istrue>\
            <istrue> v1 == $$ * w1 \
              <if-not-so> e1 is not mapped to f1 </if-not-so>\
            </istrue>\
            <istrue> v2 == $$ * w2 \
              <if-not-so> e2 is not mapped to f2 </if-not-so>\
            </istrue>\
            <istrue> v3 == $$ * w3 \
              <if-not-so> e3 is not mapped to f3 </if-not-so>\
            </istrue>\
            <isincorrect> [m1,m2,m3 ] </isincorrect>\
          </question>"

        global_xmltree = etree.fromstring( global_xml);
        question_xmls = [question_xml_1, question_xml_2, question_xml_3];
        i = 0
        for question_xml in question_xmls :
            print(f"I = {i}")
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "randomkey1";
            question_json['@attr']['type'] ="matrix"
            (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( success == 'success' )
            i = i + 1




    def test_validate_matrix_rotation( self ):

        exerciseassetpath = thispath()

        global_xml = " <global>\
            theta = var(\'theta\');\
            r = RotationMatrix; \
            xhat = [1,0,0];\
            zhat = [0,0,1];\
            yhat = [0,1,0]; \
            m = RotationMatrix(xhat,  - pi/2 )  * RotationMatrix(zhat, - pi/2 ) *  RotationMatrix(xhat, pi/2) * RotationMatrix(zhat, pi/2);\
            v,th = RotationArguments(m)\
            </global> "
                    
        question1 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [ [ 0,0,1],[1,0,0],[0,1,0] ] </expression>\
                <istrue> $$ == RotationMatrix([1,1,1]/sqrt(3), 2 * pi / 3 ) </istrue>\
              </question>"
            
        question2 =  "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [[ 0,-1,0],[1,0,0],[0,0,1]] </expression>\
                <istrue> $$ == RotationMatrix( [0,0,1] ,  pi/2 ) </istrue>\
              </question>"
            
        question3 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [[ 1,0,0],[0,0,-1],[0,1,0]] </expression>\
                <istrue> $$ == RotationMatrix( [1,0,0] ,  pi/2 ) </istrue>\
              </question>"
            
        question4 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [[0, 0, -1], [1, 0, 0], [0, -1, 0]] </expression>\
                <istrue> $$   == RotationMatrix([ -1,-1, 1] / sqrt(3) , 2 pi / 3 ) </istrue>\
                <istrue> $$ ==  m </istrue>\
              </question>"
            
            
        question5 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression>  th </expression> \
                <istrue>  2 pi / 3 ==  $$   </istrue> \
              </question>"
            
        question6 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> 1/sqrt(3) *  [ -1,-1,1]  </expression>\
                <istrue>  $$ == v  </istrue>\
                <isfalse>  $$ == [-1,-1,1]  <if-not-so> Normalize v! </if-not-so>\
                </isfalse>\
              </question>"

        global_xmltree = etree.fromstring( global_xml);
        question_xmls = [question1,question2,question3,question4,question5,question6]
        for question_xml in question_xmls :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "randomkey1";
            question_json['@attr']['type'] ="matrix"
            (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( success == 'success' )


    def test5(self) :
        exerciseassetpath = thispath()
        global_xml = "<global> \
            x =  1/2  ;\
            y = 1   ;\
            z = 3/2   ;\
            a = [2,3,4 ];\
            b = [4,5,6];\
            c = [7,8,9];\
            M = [ [2,3,4],[4,5,6],[7,8,9] ] \
            </global>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"randomkey1\" type=\"matrix\">  <expression> M  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " M ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [ a,b,c ] ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [ 4 [x,y,z] / 2 + 1 ,b,c]  ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [ 4 [x,y,z] / 2 + [1,1,1 ] ,b,c]  ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );



    def test5failure(self) :
        exerciseassetpath = thispath()
        global_xml = "<global> \
            x =  1/2  ;\
            y = 1   ;\
            z = 3/2   ;\
            a = [2,3,4 ];\
            b = [4,5,6];\
            c = [7,8,9];\
            M = [ [2,3,4],[4,5,6],[7,8,9] ] \
            </global>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"randomkey1\" type=\"matrix\">  <expression> M  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " [ 2 * [1,3/2,2] , b,c ]  ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [  [4,6,8] / 2  , b,c ]  ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [[ 1,3,4],[4,4,6],[7,8,8] ] + 1  ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [ 4 [x,y,z] / 2 + 1 ,b,c]  ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [ 4 [x,y,z] / 2 + [1,1,1 ] ,b,c]  ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [ [[1,0,0],[0,1,0],[0,0,1]] *[2,3,4], b,c ]   ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
        self.assertTrue( r.get('correct',None) );
        r =  self.answer_check(  question_json, question_xmltree, " [ 1 + [[1,0,0],[0,1,0],[0,0,1]] *[1,2,3], b,c ]   ", global_xmltree  )
        self.assertTrue( r.get('correct',None) );
 

 
    #@pytest.mark.xfail
    def test_validate_matrix_rotation_and_funcsub( self ):

        exerciseassetpath = thispath()

        global_xml = " <global>\
            theta = var(\'theta\');\
            r = RotationMatrix; \
            xhat = [1,0,0];\
            zhat = [0,0,1];\
            yhat = [0,1,0]; \
            m = r(xhat,  - pi/2 )  * r(zhat, - pi/2 ) *  r(xhat, pi/2) * r(zhat, pi/2);\
            v,th = RotationArguments(m)\
            </global> "
                    
        question1 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [ [ 0,0,1],[1,0,0],[0,1,0] ] </expression>\
                <istrue> $$ == r([1,1,1]/sqrt(3), 2 * pi / 3 ) </istrue>\
              </question>"
            
        question2 =  "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [[ 0,-1,0],[1,0,0],[0,0,1]] </expression>\
                <istrue> $$ == r( [0,0,1] ,  pi/2 ) </istrue>\
              </question>"
            
        question3 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [[ 1,0,0],[0,0,-1],[0,1,0]] </expression>\
                <istrue> $$ == r( [1,0,0] ,  pi/2 ) </istrue>\
              </question>"
            
        question4 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> [[0, 0, -1], [1, 0, 0], [0, -1, 0]] </expression>\
                <istrue> $$   == r([ -1,-1, 1] / sqrt(3) , 2 pi / 3 ) </istrue>\
                <istrue> $$ ==  m </istrue>\
              </question>"
            
            
        question5 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression>  th </expression> \
                <istrue> IsEqual( 2 pi / 3 , $$ )  </istrue> \
              </question>"
            
        question6 = "<question key=\"randomkey1\" type=\"matrix\">\
                <expression> 1/sqrt(3) *  [ -1,-1,1]  </expression>\
                <istrue>  $$ == v  </istrue>\
                <isfalse>  $$ == [-1,-1,1]  <if-not-so> Normalize v! </if-not-so>\
                </isfalse>\
              </question>"

        global_xmltree = etree.fromstring( global_xml);
        question_xmls = [question1,question2,question3,question4,question5,question6]
        for question_xml in question_xmls :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "randomkey1";
            question_json['@attr']['type'] ="matrix"
            (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( success == 'success' )

    def test_validate_matrix_entries(self) :
        exerciseassetpath = thispath()
        global_xml = " <global> g = [ [1,2,3 ],[4,5,6]] </global>"
        global_xmltree = etree.fromstring( global_xml);
        question1 =  "<question key=\"key\"> <iscorrect>g[1,2] </iscorrect> <istrue>$$ == g[1,2] </istrue> <istrue>$$ == ( [1,2] )[2] </istrue> <istrue>( [$$ , $$  ] )[1]  == ( [ g[1,1] , g[1,2]]  )[2] </istrue> <expression>2 </expression> </question>"
        for question_xml in [question1] :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "key";
            question_json['@attr']['type'] ="default"
            (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( success == 'success' )


    def test_validate_1_4_8( self ):

        exerciseassetpath = thispath()
        global_xml = " <global>   <vars>x,y,z </vars> s =  var('s') </global>"
        global_xmltree = etree.fromstring( global_xml);

        question1 =   "<question key=\"randomkey1\"> <expression>[ 1/2 * cos(s) , sin(s)] </expression> <isincorrect>[ cos(s) , sin(s) ] </isincorrect> <istrue>4 * (   dot( [1,0]   ,  $$  ))^2 +  ( dot( [0,1]  ,  $$ ))^2 == 1  </istrue> </question>"

        question2 = "<question key=\"randomkey1\"> <expression>[ s, e^s ] </expression> <iscorrect>[ log(s), s ] </iscorrect> <iscorrect>[ log( 4 s), 4  s ] </iscorrect> <istrue>dot( [0,1] , $$ ) == exp( dot( [1,0] , $$ ) ) </istrue> <istrue>$$[2] == exp( $$[1] )   </istrue> </question>"

        for question_xml in [question1,question2] :
            question_xmltree = etree.fromstring( question_xml);
            question_json = {};
            question_json['@attr'] = {}
            question_json['@attr']['key'] = "randomkey1";
            question_json['@attr']['type'] ="matrix"
            (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
            self.assertTrue( success == 'success' )

