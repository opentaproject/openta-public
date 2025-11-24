# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

class B(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            if (x * x.transpose()).is_diagonal():
                return sympy.sympify("1")  # This is true ; booleans are not used
            else:
                return sympy.sympify("0")  # This is false ; booleans are not used
        else:
            return None


class BB(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            z = x.row_insert(1, y.transpose())
            print(f"In customfunctions.py Z = {z}")
            d = z * z.transpose()
            _, sx = x.shape
            sz, _ = z.shape
            sy, _ = y.shape
            #assert sx == sz and sy == sz, "Wrong dimensions;  "
            #if z.det() == 0:
            #    assert False, "Vectors do not form a basis"
            if (z * z.transpose()).is_diagonal():
                return sympy.sympify("1")  # This is true ; booleans are not used
            else:
                return sympy.sympify("0")  # This is false ; booleans are not used
        else:
            return None

scope.update( {"B": B, "BB": BB})
