from django.test import TestCase
from .symbolic import symbolic_compare_expressions
from .symbolic import symbolic_check_if_true
from exercises.questiontypes.dev_linear_algebra.string_formatting import (
    insert_implicit_multiply as iim,
)
from exercises.questiontypes.dev_linear_algebra.string_formatting import ascii_to_sympy

import logging

logging.disable(logging.DEBUG)


class SymbolicTest(TestCase):
    def test_ascii_to_sympy(self):
        # Note that the matrix implicit multiplication works because it gets wrapped in Matrix before the implicit multiply formatting is applied
        self.assertEqual(ascii_to_sympy("[1,2,3] [[4,5,6]]"), "Matrix([1,2,3]) * Matrix([[4,5,6]])")
        self.assertEqual(ascii_to_sympy("2x + 1 == 3y"), "(2*x + 1 ) - ( 3*y)")

    def test_implicit_multiply(self):
        self.assertEqual(iim("2x"), "2*x")
        self.assertEqual(iim("2 x"), "2 * x")
        self.assertEqual(iim("2x 3y"), "2*x * 3*y")
        self.assertEqual(iim("2 x 3 y"), "2 * x * 3 * y")
        self.assertEqual(iim("(1+x)(2+x)"), "(1+x)*(2+x)")
        self.assertEqual(iim("(1+x)y"), "(1+x) * y ")
        self.assertEqual(iim("sin(x) y"), "sin(x) * y")
        self.assertEqual(iim("sin(x)y"), "sin(x) * y ")

    def test_variable(self):
        precision = 1e-6
        variables = [
            {'name': 'x', 'value': '2'},
            {'name': 'y', 'value': '2 kg'},
            {'name': 'z', 'value': 'sample(3)'},
        ]
        res = symbolic_compare_expressions(
            precision, variables, 'x*y*z*(1/(1+z)+z/(1+z))+1-sqrt(1)', 'x*y*z'
        )
        self.assertEqual(res['correct'], True)

    def test_vector(self):
        precision = 1e-6
        variables = [
            {'name': 'a', 'value': '2'},
            {'name': 'v1', 'value': '[1,1,0]'},
            {'name': 'v2', 'value': '[0,1,0]'},
            {'name': 'v3', 'value': '[0,0,1]'},
            {'name': 'phi', 'value': 'x + y + z '},
            {'name': 'vE', 'value': 'grad(phi)'},
        ]
        # True equalities
        nfuncsubs = [
            {'name': 'fg', 'args': 'x', 'value': 'sinh(x)', 'tex': 'TeX'},
            {'name': 'gg', 'args': 'x', 'value': 'cosh(x)', 'tex': 'TeX'},
            {'name': 'FG', 'args': 'x', 'value': 'F(x)', 'tex': 'TeX'},
            {'name': 'GG', 'args': 'x', 'value': 'G(x)', 'tex': 'TeX'},
            {'name': 'squared', 'args': 'x', 'value': 'x**2', 'tex': 'TeX'},
        ]

        var = '[[1,1 + I ], [ 1 - I, 1 ]  ]'

        self.assertEqual(
            symbolic_compare_expressions(
                precision, variables, ' IsHermitian([[1,I],[-I,1]]) ', ' 1 '
            )['correct'],
            True,
        )
        self.assertEqual(
            symbolic_check_if_true(precision, variables, ' IsHermitian( $$ ) ', '[[1,I],[-I,1]]')[
                'correct'
            ],
            True,
        )
        self.assertEqual(
            symbolic_check_if_true(
                precision,
                variables,
                'And(Ge(RankOf($$),2),Not(IsDiagonal($$)),IsUnitary($$),IsNotEqual($$,Transpose($$)))',
                '[[0,1],[-I,0]]',
            )['correct'],
            True,
            msg='Test4',
        )
        self.assertEqual(
            symbolic_check_if_true(
                precision, variables, 'Not( IsDiagonalizable( $$ ) )  ', '[[0,1],[0,0]]'
            )['correct'],
            True,
            'Test5',
        )

        self.assertEqual(
            symbolic_compare_expressions(precision, variables, 'v1', '[1,1,0]', False, [], ['v1'])[
                'correct'
            ],
            True,
        )
        self.assertEqual(
            symbolic_compare_expressions(precision, variables, 'v1', '[1,1,0]', False, [], ['v1'])[
                'correct'
            ],
            True,
        )
        self.assertEqual(
            symbolic_compare_expressions(
                precision, variables, 'dot(v1,-v2)', '-dot(v1,v2)', False, [], ['v1', 'v2'],
            )['correct'],
            True,
        )
        self.assertEqual(
            symbolic_compare_expressions(
                precision, variables, 'v1  -cross(v1,v2)', 'v1 + cross(v2,v1)', False, [], ['v1', 'v2'],
            )['correct'],
            True,
        )
        self.assertEqual(
            symbolic_compare_expressions(
                precision,
                variables,
                'dot(v1, cross(v2, v3))',
                'dot(v3, cross(v1, v2))',
                False,
                [],
                ['v1', 'v2', 'v3'],
            )['correct'],
            True,
        )
        self.assertEqual(
            symbolic_compare_expressions(
                precision,
                variables,
                'dot(v1, cross(a v2, v3))',
                'a dot(v3, cross(v1, v2))',
                False,
                [],
                ['v1', 'v2', 'v3'],
            )['correct'],
            True,
        )
        self.assertEqual(
            symbolic_compare_expressions(
                precision, variables, 'v3', 'cross(v1, v2)', False, [], ['v1', 'v2', 'v3'],
            )['correct'],
            True,
        )
        # False equalities
        self.assertEqual(
            symbolic_compare_expressions(
                precision,
                variables,
                'dot(v1, cross(v2, v3))',
                'a dot(v3, cross(v1, v2))',
                False,
                [],
                ['a', 'v1', 'v2', 'v3'],
            )['correct'],
            False,
        )
        self.assertEqual(
            symbolic_compare_expressions(
                precision, variables, '[a, 2, 0]', '[a+0.01, 2, 0.01]', False, [], ['a'],
            )['correct'],
            False,
        )
        self.assertEqual(
            symbolic_compare_expressions(
                precision, variables, 'sin(x)', 'sin\'\'\'\'(x)', False, [], ['x'],
            )['correct'],
            True,
        )

        self.assertEqual(
            symbolic_compare_expressions(
                precision,
                variables,
                '(tanh(cosh(x)))\'',
                'sinh(x) / cosh( cosh(x) )^2 ',
                False,
                [],
                ['x'],
            )['correct'],
            True,
        )

        eqs = [
            "partial( gg( fg(x) ) , x ) == gg\'( fg(x) ) fg\'(x)",
            ' ( cos( gg(x) ) )\' ==  - sin( gg(x) ) gg\'(x) ',
            '( gg( fg( gg(x) ) ))\' == gg\'(  fg( gg( x )  ) )  fg\'( gg(x)  ) gg\'( x ) ',
            '( GG( FG( GG(x) ) ))\' == GG\'(  FG( GG( x )  ) )  FG\'( GG(x)  ) GG\'( x ) ',
            'gg( fg( gg(x) ) )\' == gg\'(  fg( gg( x )  ) )  fg\'( gg(x)  ) gg\'( x ) ',
            '( tanh( cosh(x) ) )\' == tanh\'( cosh(x) ) cosh\'(x)',
            '( fg( cosh(x) ) )\' == fg\'( cosh(x) ) cosh\'(x)',
            '( tanh( fg(x) ) )\' == tanh\'( fg(x) ) fg\'(x)',
            '( FG( cosh(x) ) )\' == FG\'( cosh(x) ) cosh\'(x)',
            '( tanh( FG(x) ) )\' == tanh\'( FG(x) ) FG\'(x)',
            ' vE == [1,1,1] ',
            ' squared(x^2)  == x^4 ',
        ]
        # self.assertEqual(
        #        symbolic_compare_expressions(
        #            precision, [] ,  " tanh( cosh(x) ) )\'" , "tanh\'( cosh(x) ) cosh\'(x)",False, [], [], nfuncsubs
        #        )['correct'],
        #        True,
        #    )

        funcsubs = [
            {"name": "f", "args": "x", "value": "F(x)", "tex": "TeX"},
            {"name": "g", "args": "x", "value": "G(x)", "tex": "TeX"},
            {"name": "fg", "args": "x", "value": "sinh(x)", "tex": "TeX"},
            {"name": "gg", "args": "x", "value": "cosh(x)", "tex": "TeX"},
            {"name": "FG", "args": "x", "value": "F(x)", "tex": "TeX"},
            {"name": "GG", "args": "x", "value": "G(x)", "tex": "TeX"},
            {"name": "iden", "args": "[Q]", "value": "Q", "tex": "TeX"},
        ]
        expressions = [
            "( tanh( cosh(x) ) )\' == tanh\'( cosh(x) ) cosh\'( x )",
            " iden(xhat) == xhat ",
            #" iden(xhat) -  xhat == 0 ",
            #" iden(xhat) - 2 xhat == [-1,0,0]",
        ]

        for expression in expressions:
            self.assertEqual(
                symbolic_compare_expressions(
                    precision, [], expression, " 0 == 0 ", True, [], [], funcsubs
                )['correct'],
                True,
            )

        for eq in eqs:
            print("TESTING ", eq)
            self.assertEqual(
                symbolic_compare_expressions(
                    precision, variables, eq, '0==0', False, [], [], nfuncsubs
                )['correct'],
                True,
            )

        variables = [
            {"name": "c", "value": "1", "tex": "TeX"},
            {"name": "A", "value": "-y xhat + x yhat + 2 cos( t - z ) xhat", "tex": "TeX"},
            {"name": "pphi", "value": "1 / sqrt( x^2 + y^2 + z^2 )", "tex": "TeX"},
            {"name": "B", "value": "curl(A)", "tex": "TeX"},
            {"name": "E", "value": "- grad( pphi)  - 1/ c  dot(A)", "tex": "TeX"},
            {"name": "J", "value": "1/( 4 pi )  ( curl(B) - dot(E) )", "tex": "TeX"},
            {"name": "rho", "value": "1/( 4 pi )  div(E)", "tex": "TeX"},
        ]
        self.assertEqual(
            symbolic_compare_expressions(
                1e-06, variables, "curl(B) ", " 4 pi J + 1/c dot(E)", False, ["A"], []
            )['correct'],
            True,
        )

        self.assertEqual(
            symbolic_compare_expressions(
                1e-06, variables, "div(E) ", " 4 pi rho ", False, ["A"], []
            )['correct'],
            True,
        )

        self.assertEqual(
            symbolic_compare_expressions(1e-06, variables, "div(B) ", " 0 ", False, ["A"], [])[
                'correct'
            ],
            True,
        )

        self.assertEqual(
            symbolic_compare_expressions(
                1e-06, variables, "curl(E) ", "  -  1/c dot(B)", False, ["A"], []
            )['correct'],
            True,
        )

        maxwell_varsubs = [{"name": "c", "value": "5", "tex": "TeX"},
             {"name": "A", "value": "-y   xhat + x yhat + 2  cos( c t -  z ) xhat", "tex": "TeX"},
             {"name": "pphi", "value": "1 / sqrt( x^2 + y^2 + z^2 )", "tex": "TeX"},
             {"name": "B", "value": "curl(A)", "tex": "TeX"}, 
             {"name": "E", "value": "- grad( pphi)  - 1/ c  dot(A)", "tex": "TeX"}, 
             {"name": "J", "value": "1/( 4 pi )  ( curl(B) - 1/c dot(E) )", "tex": "TeX"}, 
             {"name": "rho", "value": "1/( 4 pi )  div(E)", "tex": "TeX"}]
     
        maxwell_funcsubs = [{"name": "d4", "args": "[Q]", "value": "del2(Q) - 1/c**2 * dot(dot(Q) )", "tex": "TeX"}, 
            {"name": "ckit", "args": "Q", "value": "Q", "tex": "TeX"}] 
        
        print("DOING MAXWELL")
        eqs = ['curl(E) + 1/c dot(B) == 0' ,
               'del2(A) == 1/c^2 partial(A,t,t)',
               'd4(A) == 0 ',
               'A ==  - y    xhat + x yhat + 2  cos( c t -  z ) xhat  ',
               ' - y    xhat + x yhat + 2  cos( c t -  z ) xhat  - A  == 0' ,
               ' cross(xhat,yhat) - zhat == 0 '
              ]
        for eq in eqs :
            [eq1,eq2] = eq.split('==')
            print("DOING ", eq1,eq2 )
            self.assertEqual(
                symbolic_compare_expressions(
                    1e-06, maxwell_varsubs, eq1 ,eq2, False, [],[], maxwell_funcsubs
                )['correct'],
                True,
            )

