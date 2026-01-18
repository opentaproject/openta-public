# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from exercises.questiontypes.dev_linear_algebra.linear_algebra import (
    linear_algebra_compare_expressions,
)
from exercises.utils.string_formatting import ascii_to_sympy

from django.test import TestCase

# logging.disable(logging.DEBUG)


class LinearAlgebraTest(TestCase):
    def test_ascii_to_sympy(self):
        # Note that the matrix implicit multiplication works because it gets wrapped in Matrix before the implicit multiply formatting is applied
        self.assertEqual(ascii_to_sympy("[1,2,3] [[4,5,6]]"), "Matrix([1,2,3]) * Matrix([[4,5,6]])")
        self.assertEqual(ascii_to_sympy("2x + 1 == 3y"), "(2*x + 1 ) - ( 3*y)")

    def test_variable(self):
        variables = [
            {"name": "x", "value": "2"},
            {"name": "y", "value": "2 kg"},
            {"name": "z", "value": "sample(3) kelvin"},
        ]
        precision = 1e-6
        res = linear_algebra_compare_expressions(precision, variables, "x*y*z*(1/(1+z)+z/(1+z))+1-sqrt(1)", "x*y*z")
        self.assertEqual(res["correct"], True)

    def test_vector(self):
        variables = [
            {"name": "a", "value": "sample(2)"},
            {"name": "v1", "value": "[1,1,0]"},
            {"name": "v2", "value": "[0,1,0]"},
            {"name": "v3", "value": "[0,0,1]"},
        ]
        # True equalities
        precision = 1e-6
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, "v1", "[1,1,0]")["correct"],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, "dot(v1,-v2)", "-dot(v1,v2)")["correct"],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, "-cross(v1,v2)", "cross(v2,v1)")["correct"],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, "dot(v1, cross(v2, v3))", "dot(v3, cross(v1, v2))"
            )["correct"],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, "dot(v1, cross(a v2, v3))", "a dot(v3, cross(v1, v2))"
            )["correct"],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, "v3", "cross(v1, v2)")["correct"],
            True,
        )
        # False equalities
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, "dot(v1, cross(v2, v3))", "a dot(v3, cross(v1, v2))"
            )["correct"],
            False,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, "[a, 2, 0]", "[a+0.01, 2, 0.01]")["correct"],
            False,
        )
