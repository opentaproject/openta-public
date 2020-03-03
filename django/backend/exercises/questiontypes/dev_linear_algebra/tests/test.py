from django.test import TestCase
from ..linear_algebra import linear_algebra_compare_expressions
from ..linear_algebra import linear_algebra_check_if_true
from ..string_formatting import insert_implicit_multiply as iim
from ..string_formatting import ascii_to_sympy

import logging

logging.disable(logging.DEBUG)


class DevLinearAlgebraTest(TestCase):
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

    def test_complex(self):
        precision = 1e-6
        variables = [{'name': 'b', 'value': '[[-1 , I],[ -I, 1 ]]'}]
        res = linear_algebra_compare_expressions(
            precision,
            variables,
            '[[0, e^( 2 I )],[e^(-2 I), 0 ]]',
            ' And( Ge( RankOf( $$ ), 2 ), And( And(  Not( IsDiagonal( $$)  ) , IsUnitary( $$ ) ) , IsNotEqual( $$, Transpose($$) ) ) ) == 1 ',
        )
        #self.assertEqual(res['correct'], True)
        res = linear_algebra_compare_expressions(
            precision,
            variables,
            '[[0.9238795325112867 , I 0.3826834323650898 ],  [ 0.3826834323650898 I,0.9238795325112867 ]]',
            ' IsDiagonalizationOf(  b, $$   )  == 1 ',
        )
        self.assertEqual(res['correct'], True)

    def notest_units(self):
        precision = 1e-5
        variables = [
            {'value': '[3, 5, 1] * meter', 'name': 'R1'},
            {'value': '[4, 3, 5] * meter', 'name': 'R2'},
            {'value': '[5, 1, 2] * N', 'name': 'F1'},
            {'value': '[5, 1, 2] * N', 'name': 'F2'},
            {'value': '[1,0,0]', 'name': 'i'},
            {'value': '[0,1,0]', 'name': 'j'},
            {'value': '[0,0,1]', 'name': 'k'},
            {'value': '1.0 * kg * meter / second^2', 'name': 'N'},
            {'value': '0.9933050613503256', 'name': 'meter'},
            {'value': '0.11838608798050299', 'name': 'kg'},
            {'value': '0.13461329316885673', 'name': 'second'},
        ]
        student_answer = '( [5, 1, 2] + [5, 1, 2] ) N'
        correct = ' ( [5, 1, 2] + [5, 1, 2] )kg meter / second^2 *N/N '
        res = linear_algebra_compare_expressions(precision, variables, student_answer, correct)
        self.assertEqual(res['correct'], True)
        variables = [
            {'value': '[3, 5, 1] * meter', 'name': 'R1'},
            {'value': '[4, 3, 5] * meter', 'name': 'R2'},
            {'value': '[5, 1, 2] * N', 'name': 'F1'},
            {'value': '[5, 1, 2] * N', 'name': 'F2'},
            {'value': '[1,0,0]', 'name': 'i'},
            {'value': '[0,1,0]', 'name': 'j'},
            {'value': '[0,0,1]', 'name': 'k'},
            {'value': '1.0 * kg * meter / second^2', 'name': 'N'},
            {'value': '0.9933050613503256', 'name': 'second'},
            {'value': '0.11838608798050299', 'name': 'meter'},
            {'value': '0.13461329316885673', 'name': 'kg'},
        ]
        student_answer = '( cross([3, 5, 1],[5, 1, 2]) + cross([5, 1, 2],[5, 1, 2]) ) N meter'
        correct = '( cross([3, 5, 1],[5, 1, 2]) + cross([5, 1, 2],[5, 1, 2]) ) N /N kg meter^2 / second^2 '
        res = linear_algebra_compare_expressions(precision, variables, student_answer, correct)
        self.assertEqual(res['correct'], True)

    def test_variable(self):
        precision = 1e-6
        variables = [
            {'name': 'x', 'value': '2'},
            {'name': 'y', 'value': '2 kg'},
            {'name': 'z', 'value': 'sample(3)'},
        ]
        res = linear_algebra_compare_expressions(
            precision, variables, 'x*y*z*(1/(1+z)+z/(1+z))+1-sqrt(1)', 'x*y*z'
        )
        self.assertEqual(res['correct'], True)

    def test_vector1(self):
        precision = 1e-6
        variables = [
            {'name': 'a', 'value': 'sample(2)'},
            {'name': 'v1', 'value': '[1,1,0]'},
            {'name': 'v2', 'value': '[0,1,0]'},
            {'name': 'v3', 'value': '[0,0,1]'},
        ]
        # True equalities
        var = '[[1,1 + I ], [ 1 - I, 1 ]  ]'
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, ' IsHermitian([[1,I],[-I,1]]) ', ' 1 '
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_check_if_true(
                precision, variables, ' IsHermitian( $$ ) ', '[[1,I],[-I,1]]'
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_check_if_true(
                precision,
                variables,
                'And(Ge(RankOf($$),2),Not(IsDiagonal($$)),IsUnitary($$),IsNotEqual($$,Transpose($$)))',
                '[[0,1],[-I,0]]',
            )['correct'],
            True,
            msg='Test4',
        )
        self.assertEqual(
            linear_algebra_check_if_true(
                precision, variables, 'Not( IsDiagonalizable( $$ ) )  ', '[[0,1],[0,0]]'
            )['correct'],
            True,
            'Test5',
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, 'v1', '[1,1,0]')['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, 'dot(v1,-v2)', '-dot(v1,v2)')[
                'correct'
            ],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, '-cross(v1,v2)', 'cross(v2,v1)'
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, 'dot(v1, cross(v2, v3))', 'dot(v3, cross(v1, v2))'
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, 'dot(v1, cross(a v2, v3))', 'a dot(v3, cross(v1, v2))'
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, 'v3', 'cross(v1, v2)')[
                'correct'
            ],
            True,
        )
        # False equalities
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, 'dot(v1, cross(v2, v3))', 'a dot(v3, cross(v1, v2))'
            )['correct'],
            False,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, '[a, 2, 0]', '[a+0.01, 2, 0.01]'
            )['correct'],
            False,
        )

    def test_shortest_distance(self):
        precision = 1e-6
        variables = [
            {'name': 'a1', 'value': '[1,2,3] '},
            {'name': 'a2', 'value': '[3,4,5]'},
            {'name': 'b1', 'value': '[1,-1,0]'},
            {'name': 'b2', 'value': '[1,1,0]'},
            {'name': 'a', 'value': '[1,4,2]'},
            {'name': 'b', 'value': '[3,-1,4]'},
            {'name': 'c', 'value': '[1,0,1]'},
            {'name': 'n', 'value': 'cross(a1-a2,b1-b2)'},
        ]
        # True equalities
        print("TESTING SHORTEST-1")
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, 'a1 ', '[1,2,3]')['correct'],
            True,
        )
        print("TESTING SHORTEST-2")
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, '|a1 - a2| ', '2 sqrt(3)')[
                'correct'
            ],
            True,
        )
        print("TESTING SHORTEST-3")
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, 'cross( a1,a2)', '[-2,4,-2]')[
                'correct'
            ],
            True,
        )
        print("TESTING SHORTEST-4")
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, 'cross( a1 - b1 ,a2 - b1)', '[0.0,6.0,-6.0]'
            )['correct'],
            True,
        )
        print("TESTING SHORTEST-5")
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, 'cross( a1 - b1 ,a2 - b1)/| a1 - a2 | ', 'sqrt(3.0) [ 0,1,-1 ] '
            )['correct'],
            True,
        )
        print("TESTING SHORTEST-6")
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision,
                variables,
                'cross( a1 - b1 ,a2 - b1)/| a1 - a2 | ',
                'cross( a1 - b1 ,a2 - b1)/| a1 - a2 |',
            )['correct'],
            True,
        )
        print("TESTING PERMUTATION OF VECTOR PRODUCT")
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision,
                variables,
                '|dot(c,cross(a,b))|/|cross(a-c,b-c)|',
                ' |dot(a,cross(b,c))|/|cross(a-c,b-c)|',
            )['correct'],
            True,
        )
        print(
            "TESTING ABS and DOT and SUBSTITUTION; check that zero vector is handled in dot and cross product "
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision,
                variables,
                '| dot( a1-b1,  cross( a2 - a1, b1 - b2 ) ) | / | cross( b1 - b2 , a1 - a2 ) |',
                ' | dot( a1-b1,  n ) | / |n| ',
            )['correct'],
            True,
        )

    def test_triple_product(self):
        precision = 1e-6
        variables = [
            {'name': 'va', 'value': '[1 , 0 , -1]'},
            {'name': 'vb', 'value': '[0 , 1 , 0]'},
            {'name': 'vc', 'value': '[0 , 1 , 1]'},
            {'name': 'a', 'value': '| va |'},
            {'name': 'b', 'value': '| vb |'},
            {'name': 'c', 'value': '| vc |'},
            {'name': 'ahat', 'value': 'va / a'},
            {'name': 'bhat', 'value': 'vb / b'},
            {'name': 'chat', 'value': 'vc / c'},
            {'name': 'cab', 'value': 'dot(ahat , bhat)'},
            {'name': 'cac', 'value': 'dot(ahat , chat)'},
            {'name': 'cbc', 'value': 'dot(bhat , chat)'},
        ]
        print("TESTING TRIPLE-PRODUCT-1")
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, ' a * b   ', ' a * b ')[
                'correct'
            ],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision,
                variables,
                '  cross( va, cross( vb,vc)) ',
                ' a b c ( bhat cac - chat cab) ',
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision,
                variables,
                '  cross( va, cross( vb,vc))  + ahat ',
                ' a b c ( bhat cac - chat cab) ',
            )['correct'],
            False,
        )
        print("TESTING TRIPLE-PRODUCT-2")
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision,
                variables,
                'cross( bhat, cross(ahat,chat))  ',
                'cross( bhat, cross(ahat,chat)) ',
            )['correct'],
            True,
        )

    def test_equality(self):
        print("TESTING EQUALITY")
        precision = 1e-4
        variables = [
            {'name': 'omega', 'value': '3.1 / second'},
            {'name': 'r0', 'value': '2  / meter'},
            {'name': 'v', 'value': 'omega r0'},
        ]
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, 'v == r0 omega ', 'v/r0 == omega '
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision,
                variables,
                '[[0,I],[-I,0]]',
                '  And( Ge( RankOf( $$ ), 2 ), Not( IsDiagonal( $$)  ) , IsUnitary( $$ ) , IsNotEqual( $$, Transpose($$) ) ) == 1 ',
            )['correct'],
            True,
        )

    def test_complex_matrices(self):
        precision = 1e-6
        variables = [
            {'name': 'x', 'value': '[[0,1],[1,0]]'},
            {'name': 'p', 'value': '[[1,9],[1,4]]'},
            {'name': 'id', 'value': '[[1,0],[0,1]]'},
            {'name': 'hbar', 'value': '.155'},
            {'name': 'n', 'value': '7'},
        ]
        variables = [
            {'value': '[[0,1],[1,0]]', 'name': 'x'},
            {'value': '[[1,9],[1,4]]', 'name': 'p'},
            {'value': '[[1,0],[0,1]]', 'name': 'id'},
            {'value': '.155', 'name': 'hbar'},
            {'value': '7', 'name': 'n'},
        ]
        res = linear_algebra_compare_expressions(
            precision,
            variables,
            '2 hbar^2  * id +   4 I hbar x * p ',
            'Or(  IsEqual( x * x - p * p , ( $$ )  )   ,  IsEqual( ( ( 2 hbar^2  * id  )  + ( 4 I hbar x * p )) , ( $$  ) ) )  ==  1 ',
            False,
        )
        print('COMPLEX_MATRICES res = ', res)
        self.assertEqual(res['correct'], True)
        res = linear_algebra_compare_expressions(
            precision,
            variables,
            'x * x - p * p ',
            'Or(  IsEqual( x * x - p * p , ( $$ )  )   ,  IsEqual( ( ( 2 hbar^2  * id  )  + ( 4 I hbar x * p )) , ( $$  ) ) )  ==  1  ',
            False,
        )
        print('COMPLEX_MATRICES res = ', res)
        self.assertEqual(res['correct'], True)
        res = linear_algebra_compare_expressions(
            precision,
            variables,
            'x - p*p',
            'Or(  IsEqual( x * x - p * p , ( $$ )  )   ,  IsEqual( ( ( 2 hbar^2  * id  )  + ( 4 I hbar x * p )) , ( $$  ) ) )   == 1  ',
            False,
        )
        print('COMPLEX_MATRICES res = ', res)
        self.assertEqual(res['correct'], False)

        # self.assertEqual(
        # self.assertEqual(
        #    linear_algebra_compare_expressions(precision,variables,  '|cross( a1 - a2, a2 - b1 )/| a1 - a2| ', '|cross( a1 - a2 , a2 - b1 )/| a1 - a2|' )['correct'],
        #    True)
        # False equalities
