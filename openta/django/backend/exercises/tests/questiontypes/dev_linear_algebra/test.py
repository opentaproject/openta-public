# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.test import TestCase
import pytest
from exercises.utils.string_formatting import ascii_to_sympy
from exercises.utils.string_formatting import insert_implicit_multiply as iim

from exercises.questiontypes.dev_linear_algebra.linear_algebra import (
    linear_algebra_check_if_true,
    linear_algebra_compare_expressions,
)

# logging.disable(logging.DEBUG)


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
        # self.assertEqual(iim("(1+x) (2+x)"), "(1+x)*(2+x)")
        # self.assertEqual(iim("(1+x)y"), "(1+x) * y ")
        self.assertEqual(iim("sin(x) y"), "sin(x) * y")
        # self.assertEqual(iim("sin(x)y"), "sin(x) * y ")

    def test_variable(self):
        precision = 1e-6
        variables = [
            {"name": "x", "value": "2"},
            {"name": "y", "value": "2 kg"},
            {"name": "z", "value": "sample(3)"},
        ]
        res = linear_algebra_compare_expressions(precision, variables, "x*y*z*(1/(1+z)+z/(1+z))+1-sqrt(1)", "x*y*z")
        self.assertEqual(res["correct"], True)


    def test_sample(self):
        precision = 1e-6
        variables = [
            {"name": "z", "value": "sample(3,0,-3)"},
        ]
        res = linear_algebra_compare_expressions(precision, variables, "exp( -abs( z ) ) ", "exp( - z )")
        self.assertEqual(res["correct"], False)
        res = linear_algebra_compare_expressions(precision, variables, "exp( -abs( z ) ) ", "exp(  z )")
        self.assertEqual(res["correct"], False)
        res = linear_algebra_compare_expressions(precision, variables, "exp( -abs( z ) ) ", "exp(  -  sqrt(z^2)  )")
        self.assertEqual(res["correct"], True)

    def test_matrix(self):
        precision = 1e-6
        variables = [
            {"name": "A", "value": "[[1,2,3],[4,5,6],[7,8,9]]"},
            {"name": "B", "value": "[[0,1,1],[0,0,3],[-1,0,2]]"},
            {"name": "AA", "value": "[[0,1,1],[0,0,3],[-1,0,2]]"},
        ]
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, " A * B * A * B * A *  B ", " (A * B)^3 ")[
                "correct"
            ],
            True,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(
                precision, variables, " A *  Mul( B , A ) * ( B * A ) * B ", " (A * B)^3 "
            )["correct"],
            True,
        )

        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, " B * A * B * A * B *  A ", " (A * B)^3 ")[
                "correct"
            ],
            False,
        )

    @pytest.mark.xfail
    def test_matrix_fails(self):
        precision = 1e-6
        variables = [
            {"name": "A", "value": "[[1,2,3],[4,5,6],[7,8,9]]"},
            {"name": "B", "value": "[[0,1,1],[0,0,3],[-1,0,2]]"},
            {"name": "AA", "value": "[[0,1,1],[0,0,3],[-1,0,2]]"},
        ]
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, " A * ( B * A )^2  * B ", " (A * B)^3 ")[
                "correct"
            ],
            True,
        )

    def test_vector(self):
        precision = 1e-6
        variables = [
            {"name": "a", "value": "sample(2)"},
            {"name": "v1", "value": "[1,1,0]"},
            {"name": "v2", "value": "[0,1,0]"},
            {"name": "v3", "value": "[0,0,1]"},
        ]
        # True equalities
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, " IsHermitian([[1,I],[-I,1]]) ", " 1 ")["correct"],
            True,
        )
        self.assertEqual(
            linear_algebra_check_if_true(precision, variables, " IsHermitian( $$ ) ", "[[1,I],[-I,1]]")["correct"],
            True,
        )
        self.assertEqual(
            linear_algebra_check_if_true(
                precision,
                variables,
                "And(Ge(RankOf($$),2),Not(IsDiagonal($$)),IsUnitary($$),IsNotEqual($$,Transpose($$)))",
                "[[0,1],[-I,0]]",
            )["correct"],
            True,
            msg="Test4",
        )
        self.assertEqual(
            linear_algebra_check_if_true(precision, variables, "Not( IsDiagonalizable( $$ ) )  ", "[[0,1],[0,0]]")[
                "correct"
            ],
            True,
            "Test5",
        )
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
                precision,
                variables,
                "dot(v1, cross(a v2, v3))",
                "a dot(v3, cross(v1, v2))",
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
                precision,
                variables,
                "dot(v1, cross(v2, v3))",
                "a dot(v3, cross(v1, v2))",
            )["correct"],
            False,
        )
        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, "[a, 2, 0]", "[a+0.01, 2, 0.01]")["correct"],
            False,
        )

        self.assertEqual(
            linear_algebra_compare_expressions(precision, variables, "[a, 2, 0]", "[2, 2, 0 ]")["correct"],
            False,
        )
