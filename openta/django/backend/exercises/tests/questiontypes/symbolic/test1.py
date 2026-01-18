# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging

from django.test import TestCase

from exercises.questiontypes.symbolic.symbolic import symbolic_compare_expressions

# logging.disable(logging.DEBUG)

logger = logging.getLogger(__name__)


class SymbolicTest1(TestCase):
    def test1a(self):
        variables = [
            {"name": "B", "value": "curl(A)", "tex": "TeX"},
            {"name": "vE", "value": "- grad( pphi )  -  dot(A)", "tex": "TeX"},
            {"name": "A", "value": "fA(x,y,z,t) ", "tex": "TeX"},
            {"name": "J", "value": "1/( 4 pi )  ( curl(B) - dot(vE) )", "tex": "TeX"},
        ]
        new_funcsubs = [
            {
                "name": "fA",
                "args": "[x,y,z,t]",
                "value": "funcy1(x,y,z,t) * xhat + funcy2(x,y,z,t) * yhat + funcy3(x,y,z,t) * zhat",
                "tex": "TeX",
            },
            {
                "name": "pphi",
                "args": "[x,y,z,t]",
                "value": "pot(x,y,z,t)",
                "tex": "TeX",
            },
        ]
        eqs = [
            {
                "div( fA(x,y,z,t)  ) == partial( funcy1(x,y,z,t) ,x) + partial(funcy2(x,y,z,t),y) + partial(funcy3(x,y,z,t) ,z)": True
            },
            {
                "div( A ) == partial( funcy1(x,y,z,t) ,x) + partial(funcy2(x,y,z,t),y) + partial(funcy3(x,y,z,t) ,z)": True
            },
            {
                "1.3 * div( A(x,y,z,t)  ) == partial( funcy1(x,y,z,t) ,x) + partial(funcy2(x,y,z,t),y) + partial(funcy3(x,y,z,t) ,z)": False
            },
            {"A - fA(x,y,z,t)  == 0 ": True},
            {"div(A) == div( fA(x,y,z,t) )": True},
            # {'vE ==  - grad( pphi )  -  dot(fA) ': True},
        ]
        for eqd in eqs:
            eq = list(eqd.keys())[0]
            val = list(eqd.values())[0]
            print(f"test1a DOING {eq}")
            self.assertEqual(
                symbolic_compare_expressions(1e-06, variables, eq, "0==0", False, [], [], new_funcsubs)["correct"],
                val,
            )

    def test2a(self):

        maxwell_varsubs = [
            {"name": "c", "value": "5", "tex": "TeX"},
            {
                "name": "A",
                "value": "-y   xhat + x yhat + 2  cos( c t -  z ) xhat",
                "tex": "TeX",
            },
            {"name": "pphi", "value": "1 / sqrt( x^2 + y^2 + z^2 )", "tex": "TeX"},
            {"name": "B", "value": "curl(A)", "tex": "TeX"},
            {"name": "vE", "value": "- grad( pphi)  - 1/ c  dot(A)", "tex": "TeX"},
            {
                "name": "J",
                "value": "1/( 4 pi )  ( curl(B) - 1/c dot(vE) )",
                "tex": "TeX",
            },
            {"name": "rho", "value": "1/( 4 pi )  div(vE)", "tex": "TeX"},
        ]

        maxwell_funcsubs = [
            {
                "name": "d4",
                "args": "[v]",
                "value": "del2(v) - 1/c**2 * dot(dot(v) )",
                "tex": "TeX",
            },
            {"name": "ckit", "args": "v", "value": "v", "tex": "TeX"},
        ]

        print("DOING MAXWELL")
        eqs = [
            #'curl(vE) + 1/c dot(B) == 0',
            "del2(A) == 1/c^2 partial(A,t,t)",
            #'d4(A) == 0 ',
            "A ==  - y    xhat + x yhat + 2  cos( c t -  z ) xhat  ",
            " - y    xhat + x yhat + 2  cos( c t -  z ) xhat  - A  == 0",
            " cross(xhat,yhat) - zhat == 0 ",
            " [[1,0,0],[0,1,0],[0,0,1]] * xhat -  [1,0,0] == 0 ",
        ]
        for eq in eqs:
            [eq1, eq2] = eq.split("==")
            print(f"test2 DOING {eq1} == {eq2}")
            self.assertEqual(
                symbolic_compare_expressions(1e-06, maxwell_varsubs, eq1, eq2, False, [], [], maxwell_funcsubs)[
                    "correct"
                ],
                True,
            )

    # def testz(self) :
    #    assert  False, "SUCCESSFUL END OF TEST1 SO THROW ERROR AND STOP"
