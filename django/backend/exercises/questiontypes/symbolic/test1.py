from django.test import TestCase
from .symbolic import symbolic_compare_expressions
from .symbolic import symbolic_check_if_true
from exercises.questiontypes.dev_linear_algebra.string_formatting import (
    insert_implicit_multiply as iim,
)
from exercises.questiontypes.dev_linear_algebra.string_formatting import ascii_to_sympy

import logging

logging.disable(logging.DEBUG)


class SymbolicTest1(TestCase):

    
    def test1a( self ):
        variables = [{'name': 'B', 'value': 'curl(A)', 'tex': 'TeX'}, 
                    {'name': 'vE', 'value': '- grad( pphi )  -  dot(A)', 'tex': 'TeX'}, 
                    {'name': 'A', 'value': 'fA(x,y,z,t) ', 'tex': 'TeX'}, 
                    {'name': 'J', 'value': '1/( 4 pi )  ( curl(B) - dot(vE) )', 'tex': 'TeX'}]
        new_funcsubs = [{"name": "fA", "args": "[x,y,z,t]", "value": "funcy1(x,y,z,t) * xhat + funcy2(x,y,z,t) * yhat + funcy3(x,y,z,t) * zhat", "tex": "TeX"}, 
                        {"name": "pphi", "args": "[x,y,z,t]", "value": "pot(x,y,z,t)", "tex": "TeX"}]
        eqs = [ 
            {'div( fA(x,y,z,t)  ) == partial( funcy1(x,y,z,t) ,x) + partial(funcy2(x,y,z,t),y) + partial(funcy3(x,y,z,t) ,z)' : True },
            {'div( A ) == partial( funcy1(x,y,z,t) ,x) + partial(funcy2(x,y,z,t),y) + partial(funcy3(x,y,z,t) ,z)' : True },
            {'1.3 * div( A(x,y,z,t)  ) == partial( funcy1(x,y,z,t) ,x) + partial(funcy2(x,y,z,t),y) + partial(funcy3(x,y,z,t) ,z)' : False},
            {'A - fA(x,y,z,t)  == 0 ' : True},
            ]
        for eqd in eqs :
            eq = list( eqd.keys() )[0]
            val = list( eqd.values() )[0]
            print("DOING ", eq )
            self.assertEqual(
                symbolic_compare_expressions(
                    1e-06, variables, eq, '0==0', False, [], [], new_funcsubs
                )['correct'],
                val,
            )

    def test2a(self) :

        maxwell_varsubs = [
            {"name": "c", "value": "5", "tex": "TeX"},
            {"name": "A", "value": "-y   xhat + x yhat + 2  cos( c t -  z ) xhat", "tex": "TeX"},
            {"name": "pphi", "value": "1 / sqrt( x^2 + y^2 + z^2 )", "tex": "TeX"},
            {"name": "B", "value": "curl(A)", "tex": "TeX"},
            {"name": "vE", "value": "- grad( pphi)  - 1/ c  dot(A)", "tex": "TeX"},
            {"name": "J", "value": "1/( 4 pi )  ( curl(B) - 1/c dot(vE) )", "tex": "TeX"},
            {"name": "rho", "value": "1/( 4 pi )  div(vE)", "tex": "TeX"},
        ]

        maxwell_funcsubs = [
            {"name": "d4", "args": "[Q]", "value": "del2(Q) - 1/c**2 * dot(dot(Q) )", "tex": "TeX"},
            {"name": "ckit", "args": "Q", "value": "Q", "tex": "TeX"},
        ]

        print("DOING MAXWELL")
        eqs = [
            'curl(vE) + 1/c dot(B) == 0',
            'del2(A) == 1/c^2 partial(A,t,t)',
            'd4(A) == 0 ',
            'A ==  - y    xhat + x yhat + 2  cos( c t -  z ) xhat  ',
            ' - y    xhat + x yhat + 2  cos( c t -  z ) xhat  - A  == 0',
            ' cross(xhat,yhat) - zhat == 0 ',
            ' [[1,0,0],[0,1,0],[0,0,1]] * xhat -  [1,0,0] == 0 ',
        ]
        for eq in eqs:
            [eq1, eq2] = eq.split('==')
            print("DOING ", eq1, eq2)
            self.assertEqual(
                symbolic_compare_expressions(
                    1e-06, maxwell_varsubs, eq1, eq2, False, [], [], maxwell_funcsubs
                )['correct'],
                True,
            )

    #def testz(self) :
    #    assert  False, "SUCCESSFUL END OF TEST1 SO THROW ERROR AND STOP"
