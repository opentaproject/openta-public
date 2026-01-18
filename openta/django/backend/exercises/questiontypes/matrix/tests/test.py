# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from unittest import TestCase
#from .matrix import  com
from exercises.questiontypes.matrix import MatrixQuestionOps 
from sympy import expand;
from lxml import etree
import pytest


class Test1_Matrix(TestCase, MatrixQuestionOps):

    def test_commutative_and_noncommutative_operators(self) : 
        # TEST NONCOMMUTATIVE SYMBOLS  DEFINED BY "op" ;
        # AND COMMUTATIVE SYMBOLS DEFINED BY "var";
        print("TEST_COMMUTATIVE_AND_NONCOMMUTATIVE_OPERATORS")
        global_text = f"a = var(\"a\") ; b = var(\"b\") ;"
        self.assertTrue( self.compare_expressions( "a b ", "b a ", global_text ).get('correct',False));
        global_text = f"a = op(\"a\") ; b = op(\"b\")  ; c = op(\"c\") ;" 
        self.assertFalse( self.compare_expressions( "a b ", "b a ", global_text ).get('correct',False));
        # test jacobi identity
        self.assertTrue( self.compare_expressions( "com(a,com(b,c)) + com(b,com(c,a)) + com(c,com(a,b))" , '0' , global_text).get('correct',False));
        self.assertFalse( self.compare_expressions( "com(a,com(b,c)) + com(b,com(c,a)) - com(c,com(a,b))" , '0' , global_text).get('correct',False));

    def test_complex(self):
        print("TEST_COMPLEX")
        global_text = f"a = sqrt( 2  + 3 I ); b = 1.6741492280355400404 + 0.8959774761298381247 I ;"
        self.assertTrue( self.compare_expressions( "a", "b", global_text ).get('correct',False));
        self.assertTrue( self.compare_expressions(" exp( theta *  [[0,-1] ,[1,0] ] ) ", " [[ cos(theta), -sin(theta)],[sin(theta), cos(theta) ]] ", global_text).get('correct',False))



    def test_simple_matrix(self):
        print("TEST_SIMPLE_MATRIX")
        global_text = f"a = [ [ 1,2 ] , [3,4] ] ; b = [ [ 0,1],[1,0] ];";
        self.assertFalse( self.compare_expressions( "a b ", "b a ", global_text ).get('correct',False));
        self.assertTrue( self.compare_expressions( "a + 2 b  ", " 2 b +  a ", global_text ).get('correct',False));

    def test_simple_matrix2(self):
        print("TEST_SIMPLE_MATRIX")
        global_text = f" a = op('a'); b = op('b') ;  M = 12; r = 0.3; L = 2; alpha = 5 pi / 12; g = 118 / 12 ; xhat = [1,0]; yhat = [0,1] ; beta = 5 pi / 36; ";
        self.assertTrue( self.compare_expressions( 
                        " M g ( xhat sin(alpha) + yhat ( 1 - cos(alpha) ) )" ,
                        "sin(alpha) M g xhat + M g ( 1 - cos(alpha)) yhat"
                       , global_text ).get('correct',False));
        self.assertTrue( self.compare_expressions( "a + 2 b  ", " 2 b +  a ", global_text ).get('correct',False));
        self.assertFalse( self.compare_expressions( "a + 2 b a   ", " 2 a  b +  a ", global_text ).get('correct',False));


    def test_simplify( self ):
        print("TEST SIMPLIFY")
        global_xml = "<global>  F = 3 kg meter / second^2; h = 7 meter; b = 5 meter; </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\'1\' type=\'matrix\'><expression> -F*h*b/sqrt(h^2+b^2) </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        r =  self.answer_check(  question_json, question_xmltree, "-F/sqrt(1/h^2+1/b^2)", global_xmltree )
        self.assertTrue( r.get('correct',False ) )

    def test_braces(self) :
        global_xml =" <global>  x = var(\'x\'); y = -7;   z = [[- 1 x^3,3 *y^3],[-x^2,2*x^2]] </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"3\" type=\"default\"><expression> z </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        r =  self.answer_check(  question_json, question_xmltree, " [[- 1 x^3,3 *y^3],[-x^2,2*x^2]] ", global_xmltree )
        self.assertTrue( r.get('correct',False ) )




    def test_shortest_distanc_test(self) :
        global_xml =" <global>   a1 = [1,2,3 ];  a2 = [3,4,5]  ;   b1 = [1,-1,0]; b2 = [1,1,0]  ; a = [1,4,2]  ; b = [3,-1,4]; c = [1,0,1] ; n = cross(a1-a2,b1-b2);  </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\"3\" type=\"default\"><expression>|dot(a,cross(b,c))|/|cross(a-c,b-c)|</expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        r =  self.answer_check(  question_json, question_xmltree, "|dot(a,cross(b,c))|/|cross(a-c,b-c)|", global_xmltree )
        self.assertTrue( r.get('correct',False ) )
        question_xml = "<question key=\"0\" type=\"default\"><expression>| dot( a1-b1, n ) | / |n| </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        r =  self.answer_check(  question_json, question_xmltree, "| dot( a1-b1, cross( a1-a2,b1-b2) ) | / |cross( a1-a2,b1-b2)   |  ", global_xmltree )
        self.assertTrue( r.get('correct',False ) )


    def test_equality( self ):
        print("TEST EQULITIES")
        global_xml = "<global> x = 1.234 ; y = x^3  </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\'1\' type=\'matrix\'><expression> 0 == 0 </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        correct_answer = "0 == 0 ";
        question_json = {'exerciseassetpath' : '.'};
        r =  self.answer_check(  question_json, question_xmltree, "y == x^3 " , global_xmltree )
        self.assertTrue( r['correct'])
        r =  self.answer_check(  question_json, question_xmltree, "x^3 == y  " , global_xmltree )
        self.assertTrue( r['correct'])
        r =  self.answer_check(  question_json, question_xmltree, "y == x " , global_xmltree )
        self.assertFalse( r['correct'] )

    def test_precision( self ):
        global_text = f"two = 2; twothirds = 2/3 ; a = [ [ 1,2 ] , [3,4] ] ; b = [ [ 0,1],[1,0] ];";
        self.assertTrue( self.compare_expressions( "2", "two", global_text ,"", "0" ).get('correct',False));
        self.assertFalse( self.compare_expressions("two","2.0", global_text ,"", "0" ).get('correct',False));
        self.assertTrue( self.compare_expressions( "2.0", "two", global_text ,"", "0.001" ).get('correct',False));
        self.assertTrue( self.compare_expressions( "2.001", "two", global_text ,"", "0.001" ).get('correct',False));
        self.assertFalse( self.compare_expressions( "2.0011", "two", global_text ,"", "0.001" ).get('correct',False));
        self.assertFalse( self.compare_expressions( "2.0022", "two", global_text ,"", "0.1%" ).get('correct',False));
        self.assertTrue( self.compare_expressions( "2.0019", "two", global_text ,"", "0.1%" ).get('correct',False));
        self.assertTrue( self.compare_expressions( "2/3", "twothirds", global_text ,"", "0" ).get('correct',False));
        self.assertFalse( self.compare_expressions(  "twothirds","2/3.0" , global_text ,"" ).get('correct',False));
        self.assertTrue( self.compare_expressions( "twothirds","2/3", global_text ,"", ".000001" ).get('correct',False));


    def test2_Are_EigenvaluesOf(self) :
        global_text = "<global>  b = [[0,1],[1,0]]; </global>";
        global_xmltree = etree.fromstring( global_text)
        question_xml = "<question key=\'1\' type=\'matrix\'><istrue>  AreEigenvaluesOf( b, $$ )  </istrue> <expression> [1,-1] </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        self.assertTrue( self.answer_check(  question_json, question_xmltree, "[1,-1]", global_xmltree ).get('correct') )
        self.assertTrue( self.answer_check(  question_json, question_xmltree, "[-1,1]", global_xmltree ).get('correct') )
        self.assertFalse( self.answer_check(  question_json, question_xmltree, "[-1,-1]", global_xmltree ).get('correct') )




    def test2_Are_EigenvectorsOf(self) :
        global_text = "<global>  m = [[0,1,0],[0,0,1],[0,0,0]]; </global>";
        global_xmltree = etree.fromstring( global_text)
        question_xml = "<question key=\'1\' type=\'matrix\'><istrue> AreEigenvectorsOf(m,$$) </istrue> <expression> [[0,1,1],[1,0,0],[0,0,1]] </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        self.assertFalse( self.answer_check(  question_json, question_xmltree, "[[1,0,0],[0,0,0] ]", global_xmltree ).get('correct') )
        self.assertTrue( self.answer_check(  question_json, question_xmltree, "[[1,0,0 ]]", global_xmltree ).get('correct') )




    def test_Are_EigenvectorsOf(self) :
        global_text = "<global>  m = [[1,0,0],[0,1,0],[0,1,0]]; </global>";
        global_xmltree = etree.fromstring( global_text)
        question_xml = "<question key=\'1\' type=\'matrix\'><istrue> AreEigenvectorsOf(m,$$) </istrue> <expression> [[0,1,1],[1,0,0],[0,0,1]] </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        self.assertFalse( self.answer_check(  question_json, question_xmltree, "[[1,2,3],[4,5,6],[3,2,1]]", global_xmltree ).get('correct') )
        self.assertTrue( self.answer_check(  question_json, question_xmltree, "[[0,1,1],[1,0,0],[0,0,1]]", global_xmltree ).get('correct') )








    def test_user_defined_functions(self):
        print("TEST_USER_DEFINED_FUNCTIONS")
        global_text = "\
            x = Symbol(\'x\');\
            y = Symbol(\'y\');\
            a = .769234 meter ; \
            b = 5.979184 meter ; \
            m = [ [ 1,2 ] , [3,4] ] ; \
            n = [ [ 0,1],[1,0] ]; \
            f(x) := 3 * x ;\
            g(x,y) := 4 * x * (y)**2 ;  \
            x = var(\"x\") ; \
            y = var(\"y\") ; "

        self.assertFalse( self.compare_expressions( "f(3) ", "12", global_text ).get('correct',False));
        self.assertTrue( self.compare_expressions( "f(4) ", "12", global_text ).get('correct',False));
        self.assertTrue(  self.compare_expressions( "g(x,y)",  " 4 x * y^2 ", global_text ).get('correct',False));
        self.assertTrue(  self.compare_expressions( "g(m,n)",  " 4 * m * n * n " , global_text).get('correct',False))
        self.assertFalse( self.compare_expressions( "g(m,n)",  " 4 * n *  m * n" , global_text).get('correct',False))

    #@pytest.mark.xfail
    def test_adding_scalar(self):
        print("TEST_USER_DEFINED_FUNCTIONS")
        global_text =  "\
            x = Symbol(\'x\');\
            y = Symbol(\'y\');\
            a = .769234 meter ; \
            b = 5.979184 meter ; \
            m = [ [ 1,2 ] , [3,4] ] ; \
            n = [ [ 0,1],[1,0] ]; \
            f(x) := 3 * x ;\
            g(x,y) := 4 * x * (y)**2 ;  \
            x = var(\"x\") ; \
            y = var(\"y\") ; "

        self.assertTrue(  self.compare_expressions( "m + 1 ",  " m + Matrix([[1,0],[0,1]]) " , global_text).get('correct',False))
        self.assertFalse(  self.compare_expressions( "m + 1 ",  " m + Matrix([[1,1],[1,1]]) " , global_text).get('correct',False))


    #@pytest.mark.xfail
    def test_scalar_and_matrix(self):
        print("TEST_SCALAR_AND_MATRIX")
        global_text = "\
            x = Symbol(\'x\');\
            y = Symbol(\'y\');\
            a = .769234 meter ; \
            b = 5.979184 meter ; \
            m = [ [ 1,2 ] , [3,4] ] ; \
            n = [ [ 0,1],[1,0] ]; \
            f(x) := 3 * x ;\
            g(x,y) := 4 * x * (y)**2 ;  \
            x = var(\"x\") ; \
            y = var(\"y\") ; "

        self.assertTrue(  self.compare_expressions( " 2 + m ",  "[[1,2],[3,4]] + [[2,0],[0,2]]", global_text ).get('correct',False));
        self.assertTrue(  self.compare_expressions( " x + 2 * m ",  "[[2,4],[6,8]] + [[x,0],[0,x]]", global_text ).get('correct',False));


    def test_sampling(self):
        print("TEST_SAMPLING")
        global_text = "z = sample(0,-1,3) * sample(0,1,-1)";
        self.assertFalse( self.compare_expressions( "e^(abs(z))", "e^(-z)", global_text).get('correct',False) );
        self.assertFalse( self.compare_expressions( "e^(abs(z))", "e^(z)", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "e^(abs(z))", "e^( abs( - z ) )", global_text).get('correct',False) );

    def test_sympy_import(self):
        print("TEST_SYMPY_IMPORT")
        global_text = " B = sympy.binomial; ";
        self.assertTrue( self.compare_expressions( "B(8,3)", "56", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "B(8,5) ", "B(8,3)", global_text).get('correct',False) );


    def test_exact(self):
        print("TEST_EXACT")
        global_text = " F = 3 kg meter / second^2; h = 7 meter; b = 5 meter; "
        self.assertTrue( self.compare_expressions( "sqrt(2)", "1/2 * sqrt(8)", global_text).get('correct', False ) );
        self.assertFalse( self.compare_expressions( "sqrt(2.0000001)", "1/2 * sqrt(8)", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "1/2 * sqrt(8)","sqrt(2.0)" , global_text,"",".0001").get('correct',False) );
        self.assertTrue( self.compare_expressions( "sqrt(2)", "1/2 * sqrt(8)" , global_text,"",".0001").get('correct',False) );
        self.assertFalse( self.compare_expressions( "sqrt(2)", "1/2 * sqrt(8.)" , global_text,"").get('correct',False) );
        self.assertTrue( self.compare_expressions( "1/2 * sqrt(8.0)" , "sqrt(2.0)", global_text).get('correct',False) );
        # THE FOLLOWING FAILS BECAUSE OF PRECISION 
        # IT WILL BE OK IN ANSWER_CHECK  
        self.assertTrue( self.compare_expressions( "-F*h*b/sqrt(h^2+b^2)", "-F/sqrt(1/h^2+1/b^2)", global_text).get('correct',False) );
        self.assertFalse( self.compare_expressions( "F(a)", "F*a", global_text).get('correct',False) );
        self.assertFalse( self.compare_expressions( "F(a)", "Fa", global_text).get('correct', False) );



    def test_syntax(self):
        global_text = "";
        self.assertTrue( self.compare_expressions( "sqrt(2)", "1/2 * sqrt(8)", global_text).get('correct',False) );
        self.assertFalse( self.compare_expressions( "sqrt(2)", "sqrt(2.0)", global_text).get('correct',False ) );
        self.assertTrue( self.compare_expressions( "sqrt(2.0)", "sqrt(2)", global_text).get('correct',False ) );
        self.assertFalse( self.compare_expressions( "e^-1", "1/e", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "e^1", "e", global_text).get('correct',False) );


    def test_clashes(self):
        global_text = " q1dot = 4 ; gam = .9915 ; gamma = 1.9234 ; beta = .7924 ; zeta = .7924 ; N = N(4.0,53) ; Q  = 4 ; FF = 9 ; ff = 92 ; S  = 7 ;  ";
        self.assertTrue( self.compare_expressions( "sin( 2 gam )", "2 sin( gam ) cos(gam) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 gamma )", "2 sin( gamma ) cos(gamma) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 beta )", "2 sin( beta ) cos(beta) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 alpha )", "2 sin( alpha ) cos(alpha) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 zeta )", "2 sin(zeta) cos(zeta) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 z )", "2 sin( z ) cos(z ) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "2 sin( 4 ) cos( N(4.0,53)  ) "," sin( 2 N ) " , global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 Q )", "2 sin( Q ) cos(Q ) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 FF )", "2 sin( FF ) cos( FF ) ", global_text).get('correct',False) ); 
        self.assertTrue( self.compare_expressions( "sin( 2 ff )", "2 sin( ff ) cos( ff ) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 ff )", "2 sin( ff ) cos( ff ) ", global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "sin( 2 S )", "2 sin( S ) cos(S ) ",  global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "2 * q1dot ", " 8  ",  global_text).get('correct',False) );
        self.assertTrue( self.compare_expressions( "zeta/zeta", "1",  global_text).get('correct',False) );













