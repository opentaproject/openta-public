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
        ]
        # True equalities
        funcsubs = [
            {'name': 'ff', 'value': 'sinh(x)', 'tex': 'TeX'},
            {'name': 'gg', 'value': 'cosh(x)', 'tex': 'TeX'},
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
                precision, variables, '-cross(v1,v2)', 'cross(v2,v1)', False, [], ['v1', 'v2'],
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
                'tanh(cosh(x))\'',
                'sinh(x) / cosh( cosh(x) )^2 ',
                False,
                [],
                ['x'],
            )['correct'],
            True,
        )
        eqs = [
            "D( gg( ff(x) ) , x ) == gg\'( ff(x) ) ff\'(x)",
            ' ( cos( gg(x) ) )\' ==  - sin( gg(x) ) gg\'(x) ',
            '( gg( ff( gg(x) ) ))\' == gg\'(  ff( gg( x )  ) )  ff\'( gg(x)  ) gg\'( x ) ',
        ]
        for eq in eqs:
            print("\nTESTING \n ", eq )
            self.assertEqual(
                symbolic_compare_expressions(
                    precision, variables, eq, '0==0', False, [], ['x'], funcsubs
                )['correct'],
                True,
            )
            print("\nEND\n")
