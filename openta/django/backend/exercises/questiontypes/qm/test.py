# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from unittest import TestCase
from .qm import  com,  QuantumQuestionOps
from sympy import expand;
from lxml import etree
from .fockspace import FiniteBosonFockSpace;

#import sympy
#from sympy import *
#from sympy.core.sympify import SympifyError
#from sympy.physics.quantum.operatorordering import normal_ordered_form 
#from sympy.physics.quantum.boson import BosonOp, BosonFockKet, BosonFockBra ;
#from sympy.physics.quantum import TensorProduct
#from sympy.physics.quantum import Dagger, qapply 
#try :
#    from .fockspace import *
#except :
#    from fockspace import *



class Test1_QM(TestCase, QuantumQuestionOps):

    def test_intro(self):
        global_text = 'f = FiniteBosonFockSpace(\"a\"); a = f.B; ad = dagger(a); n = var(\"n\")  ; ket = f.ket; bra = f.bra; ';
        self.assertTrue(self.compare_expressions("a ad ", "1 +   ad a ", global_text)['correct'])
        self.assertTrue(self.compare_expressions("2 ad a + ad^2 a^2 ", "a ad^2 a", global_text)['correct'])
        self.assertTrue(self.compare_expressions("bra(n) a ad^2 a ket(n)  ", "n*(n+1)", global_text)['correct'])

    def test_single_particle_boson_fock_space(self):
        global_text = "f = FiniteBosonFockSpace(\"a\"); \
            a = f.B; \
            ad = f.Bd;  \
            n = var(\"n\")  ; \
            ket = f.ket; \
            bra = f.bra; \
            omega =  var(\"omega\") ; \
            hbar =  var(\"hbar\"); \
            N = ad * a;  \
            H = hbar * omega * ( N + 1/2 ) ; "
        # N ket(n)
        self.assertTrue(self.compare_expressions("N ket(n)  ", "n  ket(n)  ", global_text)['correct'])
        # N ad ket(n) 
        s1 = "sqrt( n+1)^3 ket(n+1)";
        s2 = "N * ad * ket(n)";
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        # N a ket(n) 
        s1 = "sqrt( n ) * ( n-1) *  ket(n-1)";
        s2 = "N * a * ket(n)";
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        # N^2 ket(n)
        s1 = "n^2 ket(n)";
        s2 = "N^2 ket(n)";
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        # H ket(n)
        s1 =" hbar omega ( n + 1/2 )   ket(n)";
        s2 = "H ket(n)";
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        # H a ket(n)
        s1 =" hbar omega ( n - 1/2 ) a   ket(n)";
        s2 = "H a ket(n)";
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        s1 =" hbar omega ( n - 1/2 ) sqrt(n)   ket(n-1)";
        s2 = "H a ket(n)";
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])

    def test_single_particle_boson_commutator(self):
        global_text = "f = FiniteBosonFockSpace(\"a\"); \
            hbar = var(\"hbar\"); \
            omega = var(\"omega\"); \
            a = f.B; \
            ad = dagger(a);  \
            n = var(\"n\")  ; \
            ket = f.ket; \
            bra = f.bra; \
            N  = ad * a ;  \
            H= hbar * omega * ( ad * a + 1/2 ); \
            "
        # N ad ket(n) 
        s1 = "( a * ad - ad * a ) "
        s2 = "( 1 )";
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        s1 = "com(a,N)"
        s2 = "a"
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        s1 = "com(ad,a^2)"
        s2 = " - 2 a "
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        s1 = "com(a,ad^3)";
        s2 = " 3 ad^2" ;
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        s1 = "com(a,ad^3)";
        s2 = " 3 ad^2 "
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])
        s1 = "com(H,ad)";
        s2 = "hbar omega ad " ;
        self.assertTrue(self.compare_expressions(s1,s2, global_text)['correct'])

    def test_commutative_and_noncommutative_operators(self) : 
        # TEST NONCOMMUTATIVE SYMBOLS  DEFINED BY "op" ;
        # AND COMMUTATIVE SYMBOLS DEFINED BY "var";
        global_text = f"a = var(\"a\") ; b = var(\"b\") ;"
        self.assertTrue( self.compare_expressions( "a b ", "b a ", global_text )['correct']);
        self.assertTrue( self.compare_expressions( "com(a,b)", "0 ", global_text )['correct']);
        global_text = f"a = op(\"a\") ; b = op(\"b\")  ; c = op(\"c\") ;" 
        self.assertFalse( self.compare_expressions( "a b ", "b a ", global_text )['correct']);
        r = self.compare_expressions( "com(a,b)", "0" ,  global_text )
        print(f"R = {r}")
        self.assertFalse( self.compare_expressions( "com(a,b)", "0",  global_text )['correct'] )
        # test jacobi identity
        self.assertTrue( self.compare_expressions( "com(a,com(b,c)) + com(b,com(c,a)) + com(c,com(a,b))" , "0", global_text)['correct']);
        self.assertFalse( self.compare_expressions( "com(a,com(b,c)) + com(b,com(c,a)) - com(c,com(a,b))" ,  "0", global_text)['correct']);


    #def test_simple_matrix(self):
    #    global_text = f"a = [ [ 1,2 ] , [3,4] ] ; b = [ [ 0,1],[1,0] ];";
    #    self.assertFalse( self.compare_expressions( "a b ", "b a ", global_text )['correct']);
    #    self.assertTrue( self.compare_expressions( "a + 2 b  ", " 2 b +  a ", global_text )['correct']);










    #def test_always_fails(self):
    #    self.assertTrue(False)
