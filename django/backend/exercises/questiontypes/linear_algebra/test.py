from django.test import TestCase
from .linear_algebra import linear_algebra_compare_expressions
import logging

logging.disable(logging.DEBUG)


class LinearAlgebraTest(TestCase):
    def test_variable(self):
        variables = [
            {'name': 'x', 'value': '2'},
            {'name': 'y', 'value': '2 kg'},
            {'name': 'z', 'value': 'sample(3)'},
        ]
        res = linear_algebra_compare_expressions(
            variables, 'x*y*z*(1/(1+z)+z/(1+z))+1-sqrt(1)', 'x*y*z'
        )
        self.assertEqual(res['correct'], True)

    def test_vector(self):
        variables = [
            {'name': 'a', 'value': 'sample(2)'},
            {'name': 'v1', 'value': '[1,1,0]'},
            {'name': 'v2', 'value': '[0,1,0]'},
            {'name': 'v3', 'value': '[0,0,1]'},
        ]
        # True equalities
        self.assertEqual(
            linear_algebra_compare_expressions(variables, 'v1', '[1,1,0]')['correct'], True
        )
        self.assertEqual(
            linear_algebra_compare_expressions(variables, 'dot(v1,-v2)', '-dot(v1,v2)')['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(variables, '-cross(v1,v2)', 'cross(v2,v1)')[
                'correct'
            ],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                variables, 'dot(v1, cross(v2, v3))', 'dot(v3, cross(v1, v2))'
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                variables, 'dot(v1, cross(a v2, v3))', 'a dot(v3, cross(v1, v2))'
            )['correct'],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(variables, 'v3', 'cross(v1, v2)')['correct'], True
        )
        # False equalities
        self.assertEqual(
            linear_algebra_compare_expressions(
                variables, 'dot(v1, cross(v2, v3))', 'a dot(v3, cross(v1, v2))'
            )['correct'],
            False,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(variables, '[a, 2, 0]', '[a+0.01, 2, 0.01]')[
                'correct'
            ],
            False,
        )
