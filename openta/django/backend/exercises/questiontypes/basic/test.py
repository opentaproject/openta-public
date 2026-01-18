# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from unittest import TestCase
from .basic import  com
from .basic import BasicQuestionOps 
from sympy import expand;
from lxml import etree


class Test1_Basic(TestCase, BasicQuestionOps):

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

    def test_unary_minus( self ):
        print("TEST UNARY")
        global_xml = "<global>  f1 = 3.99234  kg meter / second^2; f2 = 7.99 kg meter / second^2 </global>"
        global_xmltree = etree.fromstring( global_xml);
        #question_xml = "<question key=\'1\' type=\'basic\'><expression> -F*h*b/sqrt(h^2+b^2) </expression></question>"
        question_xml = "<question key='0'> <ignore>-3*f2/(8*f1)+1/2  </ignore> <expression>1/2 -  3 * f2 / (8*f1)  </expression> </question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        r =  self.answer_check(  question_json, question_xmltree, "1/2 -  3 * f2 / (8*f1) ", global_xmltree )
        self.assertTrue( r.get('correct',False ) )
        r =  self.answer_check(  question_json, question_xmltree, "-3*f2/(8*f1)+1/2", global_xmltree )
        self.assertTrue( r.get('correct',False ) )



    def test_simplify( self ):
        print("TEST SIMPLIFY")
        global_xml = "<global>  F = 3.9899 kg meter / second^2; h = 7.7711  meter; b = 5.919561  meter; </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\'1\' type=\'basic\'><expression> -F*h*b/sqrt(h^2+b^2) </expression></question>"
        question_xmltree = etree.fromstring( question_xml);
        question_json = {'exerciseassetpath' : '.'};
        r =  self.answer_check(  question_json, question_xmltree, "-F/sqrt(1/h^2+1/b^2)", global_xmltree )
        self.assertTrue( r.get('correct',False ) )
        r =  self.answer_check(  question_json, question_xmltree, "-F/sqrt(1/h^2+1/b^2) * 2 /3 ", global_xmltree )
        #self.assertTrue( 'factor' in r.get('warning','') ) # TOOK OUT WARNING OF RATIONAL FACTORS





    def test_equality( self ):
        print("TEST EQULITIES")
        global_xml = "<global> x = 1.234 ; y = x^3  </global>"
        global_xmltree = etree.fromstring( global_xml);
        question_xml = "<question key=\'1\' type=\'basic\'><expression> 0 == 0 </expression></question>"
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
        global_text = f"two = 2; twothirds = 2/3 ; a = [ [ 1,2 ] , [3,4] ] ; b = [ [ 0,1],[1,0] ] ; twometer = 2.0 meter ;";
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
        self.assertTrue( self.compare_expressions( "twometer","2.0 meter ", global_text ,"", ".1" ).get('correct',False));
        self.assertTrue( self.compare_expressions( "twometer","2.1 meter ", global_text ,"", ".1" ).get('correct',False));
        self.assertFalse( self.compare_expressions( "twometer","2.11 meter ", global_text ,"", ".1" ).get('correct',False));




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



    def test_units(self):
        global_text = "F1 = 3.199234 kg meter / second^2; F2 = 7.99 kg meter / second^2"
        R = self.compare_expressions( " 1/2 - 3 * F2 / (8*F1)  ", " 1/2 - 3 * F2 / (8*F1)   ",  global_text)
        print(f"R32 = {R}")
        self.assertTrue( R.get('correct',False ));

        R = self.compare_expressions( " 1/2 - 3 * F2 / (8*F1)  ", " 1/2 F1 - 3 * F2 / (8*F1)   ",  global_text)
        print(f"R33 = {R}")
        self.assertFalse( R.get('correct',False ));
        warning = R.get('warning')
        self.assertTrue('Incorrect units' in warning)
        













