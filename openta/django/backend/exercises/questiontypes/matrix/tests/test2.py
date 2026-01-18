# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.test import TestCase
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

    def test_isDiagonalizable(self):
        exerciseassetpath = thispath()
        global_xml = "<global/>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = " <question key='5'> <isfalse>IsDiagonalizable( $$ ) <if-so>Is not diagonalizable ! Good ! </if-so> <if-not-so>Your matrix can be diagonalized </if-not-so> </isfalse> <expression>[[1,1],[0,1]] </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " [[2,1],[0,2]] ", global_xmltree  )
        print(f"R5 = {r}")



    def test_rotation_matrix(self) :
        exerciseassetpath = thispath()
        global_xml = "<global> theta = var(\'theta\'); \
            r = RotationMatrix; \
            xhat = [1,0,0]; \
            zhat = [0,0,1]; \
            yhat = [0,1,0]; \
            m = RotationMatrix(xhat,  - pi/2 )  * RotationMatrix(zhat, - pi/2 ) *  RotationMatrix(xhat, pi/2) * RotationMatrix(zhat, pi/2); \
            v,th = RotationArguments(m)\
            </global>"
        question_json  = {}
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"randomkey1\" type=\"matrix\">  <expression> [ [ 0,0,1],[1,0,0],[0,1,0] ] </expression>\
                <istrue> $$ == RotationMatrix([1,1,1]/sqrt(3), 2 * pi / 3 ) </istrue> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, " [ [ 0,0,1],[1,0,0],[0,1,0] ]", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " RotationMatrix([ 1,1,1]/sqrt(3), 2 * pi / 3 )", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " RotationMatrix( hat([ 1,1,1]), 2 * pi / 3 )", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " 2/3 RotationMatrix( hat([ 1,1,1]), 2 * pi / 3 )", global_xmltree  )
        print(f"R_MATRIX_TEST2 = {r}")
        self.assertFalse( r.get('correct',False) )



    def test_hat_inside( self ) :
        exerciseassetpath = thispath()
        global_xml = "<global> e1 = [1,1,0]; \
            e2 = [1,-1,1];\
            e3 = [1,-1,-2];\
            m1 = e1 / | e1 |;\
            m2 = e2 / | e2 |;\
            m3 = e3 / | e3 |;\
            M = [  m1,m2,m3 ] </global>"
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS TRUE SO IT ACCEPTS EVERYTHING
        ## THIS IS THE DEFAULT FOR istrue
        ## 
        question_xml = f" <question key=\"0\" type=\"default\"><expression>\
                1.0 * [[1/sqrt(2), 1/sqrt(2), 0], [1/sqrt(3), -(1/sqrt(3)), 1/sqrt(3)], [1/sqrt(6), -(1/sqrt(6)), -sqrt(2/3)]] \
                </expression> </question> "
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " 1.0 * [[1/sqrt(2), 1/sqrt(2), 0], [1/sqrt(3), -(1/sqrt(3)), 1/sqrt(3)], [1/sqrt(6), -(1/sqrt(6)), -sqrt(2/3)]]  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );

        r =  self.answer_check(  question_json, question_xmltree, " M  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "[m1,m2,m3] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "[hat(e1),e2/|e2| ,hat( 3 * e3)] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );


    def test_hat_and_cross( self ) :
        exerciseassetpath = thispath()
        global_xml = "<global> x = [1,2,3]; \
            y = [4,5,6]; \
            m = [[1,2,3],[4,5,6],[7,8,9]]; \
            e1 = [1,1,0]; \
            e2 = [1,-1,1]; \
            e3 = [1,-1,-2]; \
            M = [   e1  ,  e2  ,  e3  ] \
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS TRUE SO IT ACCEPTS EVERYTHING
        ## THIS IS THE DEFAULT FOR istrue
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
                <expression>[-(1/sqrt(6)), sqrt(2/3), -(1/sqrt(6))] </expression> \
                </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " hat( cross(x,y) ) ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        question_xml = " <question type=\"matrix\" key=\"5\"> <expression> M.C.I.T.A </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        r =  self.answer_check(  question_json, question_xmltree, "M.C.I.T.A", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, "Adjoint(Transpose(Inverse(Conjugate(M))))", global_xmltree  )
        self.assertTrue( r.get('correct',False) );

    def test_simple( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4 kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS TRUE SO IT ACCEPTS EVERYTHING
        ## THIS IS THE DEFAULT FOR istrue
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        self.assertTrue( IS_CORRECT in r.get('comment'));

        r =  self.answer_check(  question_json, question_xmltree, "  Fa * v1   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'ndefined' in r.get('warning',"") and 'v1' in r.get('warning',"") );

        r =  self.answer_check(  question_json, question_xmltree, "  Fa * vf( 43)    ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'ndefined' in r.get('warning',"") and 'vf' in r.get('warning',"") );


        r =  self.answer_check(  question_json, question_xmltree, "  Fa * Fb * vf( 43)    ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'ndefined' in r.get('warning',"") and 'vf' in r.get('warning',"") );



    def test_isfalse( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4 kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS FALSE SO IT ACCEPTS EVERYTHING
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue> $$ ==   sqrt( Fa^2 + Fb^2) \
                    <if-so> PASS1 </if-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2); </expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        self.assertTrue( 'PASS1' in r.get('comment','') )

        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        #self.assertTrue( 'PASS1' in r.get('comment',"") );
        #self.assertTrue( 'Units OK' in r.get('warning',"") );


        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );
        #self.assertTrue( 'Units OK' in r.get('warning',"") );


        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );
        #elf.assertTrue( 'Units OK' in r.get('warning',"") );



    def test_isfalse0( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3.298  kg meter / second^2;\
                Fb = 4.8882  kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        ##
        ## NOTE SUFFICIENCY CONDITION IS TRUE SO IT ACCEPTS EVERYTHING
        ## THIS IS THE DEFAULT FOR istrue
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue> $$ ==   sqrt( Fa^2 + Fb^2 ) \
                    <if-so> PASS1 </if-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        self.assertTrue( 'PASS1' in r.get('comment'));
        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        self.assertFalse( r.get('correct',True) ); # SINCE SUFFICIENT = False it goes on to test expression
        #self.assertTrue( 'NOSUM' in r.get('error',"") );
        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );
        r =  self.answer_check(  question_json, question_xmltree, " newvar * Fa + Fb   ", global_xmltree  )
        print(f"R777 = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'ndefined' in r.get('warning',"") and 'newvar' in r.get('warning',"") );



    def test_isfalse1( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4 kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);

        ##
        ## NOTE SUFFICIENCY CONDITION IS FALSE SO IT GOES ON TO TEST FURTHER
        ## 
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue> $$ ==    sqrt( Fa^2 + Fb^2 ) \
                    <if-so> PASS1 </if-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        #print(f"R = {r}")
        self.assertTrue( r.get('correct',False) );

        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        #self.assertTrue( 'NOSUM' in r.get('error',"") );
        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );



        #r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        #print(f"R = {r}")
        #self.assertFalse( r.get('correct',False) );
        #self.assertTrue( 'Units OK' in r.get('warning',"") );
        #self.assertTrue( 'NOMAG' in r.get('error',"") );



    def test_isfalse2( self ):

        exerciseassetpath = thispath()
        global_xml = "  <global>\
                Fa = 3 kg meter / second^2;\
                Fb = 4.2342  kg meter / second^2;\
                alpha = .799234;\
                </global>\
                "
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f" <question key=\"0\" type=\"default\">\
            <istrue sufficient=\"False\" > $$ ==   sqrt( Fa^2 + Fb^2 ) \
                    <if-not-so> NOMAG </if-not-so>\
            </istrue>\
            <isfalse> ( $$ ) == Fa + Fb \
                    <if-not-so> NOSUM </if-not-so>\
            </isfalse>\
            <isfalse> ( $$ ) == Fa - Fb \
                    <if-not-so> NODIFF </if-not-so>\
            </isfalse>\
            <expression>sqrt(Fa^2+Fb^2)</expression>\ </question> "

        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " sqrt(Fa^2+Fb^2)  ", global_xmltree  )
        #print(f"R = {r}")
        self.assertTrue( r.get('correct',False) );
        r =  self.answer_check(  question_json, question_xmltree, " Fa + Fb   ", global_xmltree  )
        print(f"RSUM = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOSUM' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " Fa - Fb   ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NODIFF' in r.get('error',"") );

        r =  self.answer_check(  question_json, question_xmltree, " sqrt( Fa * Fb )   ", global_xmltree  )
        print(f"R8888 = {r}")
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'NOMAG' in r.get('error',"") );
        #self.assertTrue( 'Units OK' in r.get('warning',"") );







    def test_istrue( self ):

        exerciseassetpath = thispath()
        global_xml = "<global/>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\'1\' type=\'matrix\' exerciseassetpath=\"{exerciseassetpath}\">\
            <istrue>  BB( ( ( $$ ) ).row(0),  ( ( ( $$ ) ).row(1) ).T )  \
                <if-so>OK</if-so> \
                <if-not-so>Not OK</if-not-so> \
            </istrue>\
            <expression> [[ 1,2,3],[-2,1,0]] </expression> \
            </question>";
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        r =  self.answer_check(  question_json, question_xmltree, " [[ 1,2,3],[-2,1,0]] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        self.assertTrue( r.get('comment',"")  == 'OK');
        r =  self.answer_check(  question_json, question_xmltree, " [[ 1,4,3],[-2,1,0]] ", global_xmltree  )
        self.assertFalse( r.get('correct',False) );
        self.assertTrue( 'Not OK' in r.get('error',"") );

    def test_istrue2( self ):

        exerciseassetpath = thispath()
        global_xml = "<global/>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\'1\' type=\'matrix\' exerciseassetpath=\"{exerciseassetpath}\">\
            <istrue>  IsNotEqual( ( $$ ).row(1) ,   ( $$ ).row(0) )  \
                <if-so>OK</if-so> \
                <if-not-so>Not OK</if-not-so> \
            </istrue>\
            <expression> [[ 1,2,3],[-2,1,0]] </expression> \
            </question>";
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        # CHECK THAT FIRST ROW IS NOT EQUAL TO SECOND ROW
        r =  self.answer_check(  question_json, question_xmltree, " [[ 1,2,3],[-2,1,0]] ", global_xmltree  )
        self.assertTrue( r.get('correct',False) );
        self.assertTrue( r.get('comment',"")  == 'OK');

        r =  self.answer_check(  question_json, question_xmltree, " [[ 1,2,3],[1,2,3]] ", global_xmltree  )
        #print(f"R = {r}")
        self.assertFalse( r.get('correct',True) );
        self.assertTrue( 'Not OK' in r.get('error',"") );

    def test_validate_scalar1( self ):

        exerciseassetpath = thispath()
        global_xml = " <global> z = sample(  33 / 31.0 , - 34 / 32.0)   ;  </global>";
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



    def test_validate_matrix1( self ):

        exerciseassetpath = thispath()
        global_xml = " <global/>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"1\" type=\"matrix\">\
                <text> Unitary matrix </text>\
                <istrue> IsUnitary( $$ ) </istrue>\
                <isfalse> ( $$ ) == Transpose( $$ ) \
                    <if-not-so> Your matrix must be complex and have off diagonal elements </if-not-so>\
                </isfalse>\
                <isfalse> ( $$ ) == Conjugate( $$ ) \
                    <if-not-so> Your matrix must be complex </if-not-so>\
                </isfalse>\
                <istrue> Rank( $$ ) > 1 \
                    <if-not-so> Your matrix must have rank greater than 1 </if-not-so>\
                </istrue>\
              <expression> [[0,I],[-I,0]] </expression>\
              <iscorrect> [[0,I],[-I,0]] </iscorrect>\
              <isincorrect> [[0,1],[1,0]] </isincorrect>\
               <isincorrect> [[1,0],[0,1]] </isincorrect>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "1";
        question_json['@attr']['type'] ="matrix"
        (success,msg) = self.validate_question(question_json, question_xmltree, global_xmltree)
        self.assertTrue( success == 'success' )



    def test_validate_matrix2( self ):

        exerciseassetpath = thispath()
        global_xml = " <global> \
            e1 = [1,1,0] ; \
            e2 = [1,-1,1] ;\
            e3 = [1,-1,-2] ;\
            m1 = e1 / | e1 | ;\
            m2 = e2 / | e2 | ;\
            m3 = e3 / | e3 | ;\
            M = [   m1  , m2  ,  m3  ] ; \
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" type=\"default\">\
            <istrue>  Rank( $$ ) == 3 <if-not-so> Rank must be 3 </if-not-so> </istrue>\
            <expression> [[1/sqrt(2), 1/sqrt(2), 0], [1/sqrt(3), -(1/sqrt(3)), 1/sqrt(3)], [1/sqrt(6), -(1/sqrt(6)), -sqrt(2/3)]] </expression>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "randomkey1";
        question_json['@attr']['type'] ="matrix"
        r =  self.answer_check(  question_json, question_xmltree, "M", global_xmltree  )
        self.assertTrue(r.get('correct'))
        question_xml = f"<question key=\"randomkey2\" type=\"default\">\
            <local>  q = $$(randomkey1)  </local> \
            <istrue>  IsDiagonal( $$ * Transpose( $$  )  ) <if-not-so> The matrix is not orthogonal </if-not-so>  </istrue>\
            <istrue>  Trace( $$ *Transpose($$) ) == 3 <if-not-so> Trace is wrong </if-not-so>  </istrue>\
            <expression> q  </expression>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "randomkey1";
        question_json['@attr']['type'] ="matrix"
        question_json["other_answers"] = {"randomkey1" : "M" };
        question_json['@attr']['is_staff'] = False
        r =  self.answer_check(  question_json, question_xmltree, "q", global_xmltree  )
        self.assertTrue(r.get('correct'))
        r =  self.answer_check(  question_json, question_xmltree, "q 2.0", global_xmltree  )
        self.assertFalse(r.get('correct',False))
        r =  self.answer_check(  question_json, question_xmltree, " 2 q", global_xmltree  )
        self.assertTrue('Trace is wrong' in r.get('error','') )

    def test_validate_matrix3( self ):

        exerciseassetpath = thispath()
        global_xml = " <global> \
            e1 = [1,1,0] ; \
            e2 = [1,-1,1] ;\
            e3 = [1,-1,-2] ;\
            q = [   e1  ,  e2  ,  e3  ] ; \
            M = [[1,1,0],[1,-1,1],[1,-1,-2]]\
            </global>"
        self.is_staff  = False;
        global_xmltree = etree.fromstring( global_xml);
        question_json = {};
        question_json['@attr'] = {}
        question_json['@attr']['key'] = "randomkey3";
        question_json['@attr']['type'] ="matrix"
        question_json['used_variable_list'] = ['M']


        question_xml = f"<question key=\"randomkey3\" type=\"matrix\">\
            <expression>Transpose(Inverse(Conjugate( Adjoint(M))))</expression>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        #print(f"ISSTAFF", self.is_staff)
        self.is_staff = False
        r =  self.answer_check(  question_json, question_xmltree, "(((M.A).C).I).T", global_xmltree  )
        print(f"R = {r}")
        self.assertTrue(r.get('correct'))
        r =  self.answer_check(  question_json, question_xmltree, "M.A.C.I.T", global_xmltree  )
        print(f"R = {r}")
        self.assertTrue(r.get('correct'))
        #r =  self.answer_check(  question_json, question_xmltree, "ABC", global_xmltree  )
        #self.assertTrue('ndefined symbols' in r['warning'] and 'ABC' in r['warning'] );
        #r =  self.answer_check(  question_json, question_xmltree, "", global_xmltree  )
        #self.assertTrue(r['error'] == 'syntax error in ^')



    
    
    def test_blacklist(self) :

        exerciseassetpath = thispath()
        global_xml = " <global> \
            a = 1.3 ; \
            b = 1.8 ; \
            i = 0 ; \
            j = 0 ; \
            <blacklist><token> i </token></blacklist>\
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" type=\"default\">\
            <blacklist><token>j</token></blacklist>\
            <expression> a * b   </expression>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        full_question = {};
        full_question['@attr'] = {}
        full_question['@attr']['key'] = "randomkey1";
        full_question['@attr']['type'] ="matrix"
        full_question['used_variable_list'] = ['a','b'];
        full_question['is_staff'] = True;
        full_question["exposeglobals"] = False;
        full_question["feedback"] = True;
        full_question["expression"] = {};
        full_question["expression"]['$'] = "a * b ;";
        safe_question = self.json_hook(   full_question, full_question, '1', '1' ,'exercise_key', feedback=True) 
        #print(f"SAFE_QUESTION = {safe_question}")
        self.used_variable_list = ['a','b'] ; # THIS SUPPOSES BLACKLIST HAS BEEN PARSED PROPERLY by json_hook
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        print(f"RR0 = {r}")
        self.assertTrue( r['correct'] );
        safe_question['is_staff'] = False ;
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        print(f"RR1 = {r}")
        self.assertTrue( r['warning'] == 'Not valid variables:: i' );
        r =  self.answer_check(  safe_question, question_xmltree, "a b + j ", global_xmltree  )
        print(f"RR2 = {r}")
        self.assertTrue( r['warning'] == 'Not valid variables:: j' );


    def test_exposeglobals(self) :

        exerciseassetpath = thispath()
        global_xml = " <global> \
            a = 1.3 ; \
            b = 1.8 ; \
            i = 0 ; \
            j = 0 ; \
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" exposeglobals=\"True\" type=\"matrix\">\
            <expression> a * b  ;  </expression>\
            </question>"
        question_xmltree = etree.fromstring( question_xml);
        full_question = {};
        full_question['@attr'] = {}
        full_question['@attr']['key'] = "randomkey1";
        full_question['@attr']['exposeglobals'] = 'True'
        full_question['@attr']['type'] ="matrix"
        full_question['used_variable_list'] = ['a','b','i','j'];
        full_question['is_staff'] = False ;
        full_question["exposeglobals"] = "True" ;
        full_question["feedback"] = True;
        full_question["expression"] = {};
        full_question["expression"]['$'] = "a * b ;";
        safe_question = self.json_hook(   full_question, full_question, 'randomkey1', '1' ,'exercise_key', feedback=True) 
        safe_question['used_variable_list'] = ['a','b','i','j']; # THIS SHOULD BE OBTAINED BY JSON_HOOK BUT IT IS TOO CONVOLUTED
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        self.assertTrue( r['correct'] )
        safe_question = self.json_hook(   full_question, full_question, '1', '1' ,'exercise_key', feedback=True) 
        r =  self.answer_check(  safe_question, question_xmltree, "a b  ", global_xmltree  )
        self.assertTrue(r['correct'] );

        




    def dead_code_test_exposeglobals(self) :

        exerciseassetpath = thispath()
        global_xml = " <global> \
            a = 1.3 ; \
            b = 1.8 ; \
            i = 0 ; \
            j = 0 ; \
            </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = f"<question key=\"randomkey1\" exposeglobals=\"True\" type=\"matrix\">\
            <expression> a * b  ;  </expression>\
            </question>"
        xml = f"<exercise><exercisename> TEST </exercisename>\n\
                {global_xml}\n\
                {question_xml}\n\
                </exercise>"
        exercise_json = exercise_xml_to_json( xml)
        question_xmltree = etree.fromstring( question_xml);
        full_question = {};
        full_question['@attr'] = {}
        full_question['@attr']['key'] = "randomkey1";
        full_question['@attr']['exposeglobals'] = 'True'
        full_question['@attr']['type'] ="matrix"
        full_question['used_variable_list'] = ['a','b','i','j'];
        full_question['is_staff'] = False ;
        full_question["exposeglobals"] = "True" ;
        full_question["feedback"] = True;
        full_question["expression"] = {};
        full_question["expression"]['$'] = "a * b ;";
        safe_question = self.json_hook(   full_question, full_question, 'randomkey1', '1' ,'exercise_key', feedback=True) 
        r =  self.answer_check(  safe_question, question_xmltree, "a b + i ", global_xmltree  )
        safe_question = self.json_hook(   full_question, full_question, '1', '1' ,'exercise_key', feedback=True) 
        r =  self.answer_check(  safe_question, question_xmltree, "a b  ", global_xmltree  )
        self.assertTrue( r.get('warning') == 'i : not valid variables' );

        




