import sympy
import numpy
import types
import sys
from pprint import pprint
from sympy import *

# from sympy.abc import _clash1, _clash2, _clash, x, y, z
from sympy.abc import x, y, z, t
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import itertools
from sympy.core import S
from sympy.matrices import Matrix

from exercises.questiontypes.safe_run import safe_run
import logging
import traceback
from .string_formatting import (
    absify,
    insert_implicit_multiply,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
)
from .unithelpers import *
from sympy import DiagonalOf

logger = logging.getLogger(__name__)


class Norm(sympy.Function):
    @classmethod
    def eval(cls, x):
        # print("Norm is entered with x = ", x )
        # print("type = ", type(x) )
        if isinstance(x, sympy.MatrixBase):
            res = N(x.norm())
            # print("result = ", res )
            return res
        elif isinstance(x, Number):
            # print("identified float")
            return N(Abs(x))
        else:
            return None


class diagonalof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return Matrix(DiagonalOf(x))
        else:
            return None


class Trace(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return N(x.trace())
        else:
            return None


class eigenvaluesof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            evdict = x.eigenvals()
            evt = list(map(lambda key: [key] * evdict[key], evdict.keys()))
            evlist = [val for sublist in evt for val in sublist]
            ev = sorted(evlist, key=default_sort_key)
            # print("EV = ", ev )
            return sympy.Matrix(ev)
        else:
            return None


class AreEigenvaluesOf(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, y, x):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            evdict = y.eigenvals()
            evt = list(map(lambda key: [key] * evdict[key], evdict.keys()))
            evlist = [val for sublist in evt for val in sublist]
            ev = Matrix(sorted(evlist, key=default_sort_key))
            # print("ev = ", ev )
            # print("x = ", x )
            diff = ev - Sort(x)
            # print("diff = ", diff )
            mag = conjugate(diff).dot(diff)
            # print("mag = ", mag )
            if mag <= 1e-6:
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class IsDiagonalizationOf(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, m, u):
        if isinstance(u, sympy.MatrixBase) and isinstance(m, sympy.MatrixBase):
            ut = transpose(u)
            diag = ut.inv() * m * ut
            diag = diag.evalf(6, chop=True)
            if diag.is_diagonal():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')

        else:
            return None


class localTranspose(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return x.T
        else:
            return None


class rankof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            sp = x.shape
            rank = sp[1]
            return sympy.sympify(rank)
        else:
            return None


class isunitary(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            sp = x.shape
            target = eye(sp[1])
            # print("target = ", target )
            zer = (x * conjugate(x.T)) - target
            # print("zer = ", zer )
            zer = zer.evalf(6, chop=True)
            if zer.is_zero:
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class IsHermitian(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            zer = x - conjugate(x.T)
            zer = zer.evalf(6, chop=True)
            if zer.is_zero:
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class crossfunc(sympy.Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, *arg):

        if len(arg) == 2:
            x = arg[0]
            y = arg[1]
            if str(x) == '0' or str(y) == '0':
                return 0
            return Cross(x, y)
        else:
            raise TypeError('cross product needs two arguments')


class Cross(sympy.MatrixExpr):
    def __new__(cls, arg1, arg2):
        return sympy.Basic.__new__(cls, arg1, arg2)

    @property
    def shape(self):
        return self.args[0].shape

    def doit(self, **hints):
        x = self.args[0].doit() if isinstance(self.args[0], sympy.Basic) else self.args[0]
        y = self.args[1].doit() if isinstance(self.args[1], sympy.Basic) else self.args[1]
        # print("enter Cross with x  = ", x , type( x ))
        # print("enter Cross with y = ", y , type( y ) )
        if str(x) == '0':
            # print("IDENTIFIED ZERO x ")
            return 0 * y
        elif str(y) == '0':
            # print("IDENTIFIED ZERO x ")
            return 0 * x
        elif isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return x.cross(y)
        else:
            return self


class Sort(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            xs = x.tolist()
            xs = sorted(xs, key=default_sort_key)
            # print("xs = ",  xs )
            return sympy.Matrix(xs)
        else:
            return None


class gt(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            x = x.doit()
            y = y.doit()
            if Gt(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class lt(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            x = x.doit()
            y = y.doit()
            # print("LT x = ", x )
            if Lt(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class ge(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            x = x.doit()
            y = y.doit()
            if Ge(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class le(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            x = x.doit()
            y = y.doit()
            if Le(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class eq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            if (x - y).is_zero:
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (
            isinstance(x, Integer) or isinstance(x, Float)
        ):
            if x.n() == y.n():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class neq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            if (x - y).is_zero:
                return sympy.sympify('0')
            else:
                return sympy.sympify('1')
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (
            isinstance(x, Integer) or isinstance(x, Float)
        ):
            if x.n() == y.n():
                return sympy.sympify('0')
            else:
                return sympy.sympify('1')
        else:
            return None


class logicaland(sympy.Function):
    @classmethod
    def eval(cls, *x):
        tot = 1
        for tval in x:
            if Not(isinstance(tval, sympy.Integer)):
                return None
            tot = And(tot, tval)
        if tot:
            return sympy.sympify('1')
        else:
            return sympy.sympify('0')


class logicalor(sympy.Function):
    @classmethod
    def eval(cls, *x):
        tot = 0
        for tval in x:
            if Not(isinstance(tval, sympy.Integer)):
                return None
            tot = Or(tot, tval)
        if tot:
            return sympy.sympify('1')
        else:
            return sympy.sympify('0')


class logicalnot(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.Integer):
            if x > 0:
                return sympy.sympify('0')
            else:
                return sympy.sympify('1')
        else:
            return None


class Dot(sympy.Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, *arg):

        if len(arg) == 1:
            from sympy.abc import x, y, z, t

            t = sympify('t')
            return diff(arg[0], t).doit()
        if len(arg) == 2:
            x = arg[0]
            y = arg[1]
            if str(x) == '0' or str(y) == '0':
                return 0
            elif isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
                return conjugate(x).dot(y)
            else:
                return None


class Times(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return sympy.matrix_multiply_elementwise(x, y)
        else:
            return None


class IsDiagonal(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            if x.is_diagonal():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')


#
# INCLUDE THIS IN SCOPE OF symbolic
# SO THAT SYMBOLIC QUESTION IS BACKWARD COMPATIBLE
# SINCE SYMBOLIC DOES NOT DO sample
#


class sample(sympy.Function):
    @classmethod
    def eval(cls, x):
        return x


class grad(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, fun):
        from sympy.abc import x, y, z, t

        res = [diff(fun, x), diff(fun, y), diff(fun, z)]
        res = sympy.sympify(Matrix(res))
        res = res.doit()
        return res


class del2(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, fun):
        from sympy.abc import x, y, z, t

        res = diff(fun, x, x) + diff(fun, y, y) + diff(fun, z, z)
        res = res.doit()
        return res


class curl(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, M):
        res = [
            diff(M[2], y) - diff(M[1], z),
            diff(M[0], z) - diff(M[2], x),
            diff(M[1], x) - diff(M[0], y),
        ]
        return sympy.sympify(Matrix(res))


class localdiv(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, M):
        if isinstance(M, sympy.MatrixBase):
            from sympy.abc import x, y, z

            res = diff(M[0], x) + diff(M[1], y) + diff(M[2], z)
            return sympy.sympify(res)


class IsDiagonalizable(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            if x.is_diagonalizable():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')


class Prime(sympy.Function):
    nargs = (1, 2, 3, 4, 5, 6)

    @classmethod
    def eval(cls, *arg):
        # print(" INTO PRIME WITH ", arg )
        first = arg[0]
        fourth = arg[3]
        order = int(arg[2])
        # print("first= ", first)
        # print("second = ", arg[1] )
        # print("third = ", arg[2] )
        # print("FOURTH = ", fourth )
        qqq = sympy.symbols('qqq')
        fun = first.func
        deriv = fun(qqq)
        while order > 0:
            order = order - 1
            deriv = diff(deriv, qqq)
        result = deriv.subs(qqq, arg[1]).doit()
        # print("PRIME RESULT IS ", result)
        return result


class Partial(sympy.Function):
    nargs = (1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *f):
        if len(f) < 1:
            return sympy.sympify('derivative or partial used withouth argument')  # }}}
        elif len(f) == 1:
            fun = f[0]
            x = list(fun.free_symbols)[0]
            return diff(fun, x)
        elif len(f) < 6:
            fun = f[0]
            x = list(fun.free_symbols)
            res = fun
            ind = 1
            while ind < len(f):
                res = diff(res, f[ind])
                ind = ind + 1
            return res
        else:
            return sympy.sympify('derivative or partial used with too many arguments')  # }}}


class partial(sympy.Function):
    nargs = (0, 1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *f):
        if len(f) < 1:
            return sympy.sympify('derivative or partial used withouth argument')  # }}}
        elif len(f) == 1:
            fun = f[0]
            x = list(fun.free_symbols)[0]
            return diff(fun, x)
        elif len(f) < 6:
            fun = f[0]
            x = list(fun.free_symbols)
            res = fun
            ind = 1
            while ind < len(f):
                res = diff(res, f[ind])
                ind = ind + 1
            return res
        else:
            return sympy.sympify('derivative or partial used with too many arguments')  # }}}


class Braket(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return conjugate(x).dot(y)
        else:
            return None


class KetBraBroken(sympy.Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):
        if len(y) == 0:
            if isinstance(x, sympy.MatrixBase) and isinstance(m, sympy.MatrixBase):
                # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
                # print("LINEAR_ALGEBRA m = ", m );
                return x * m.adjoint()
            else:
                return None
        else:
            if (
                isinstance(x, sympy.MatrixBase)
                and isinstance(m, sympy.MatrixBase)
                and isinstance(y[0], sympy.MatrixBase)
            ):
                # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
                # print("LINEAR_ALGEBRA m = ", m );
                # print("LINEAR_ALBEBRA y = ", y[0] );
                return x * m * y[0].adjoint()  # }}}
            else:
                return None


class KetBra(sympy.Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
            # print("LINEAR_ALGEBRA m = ", m );
            return MatMul(x, conjugate(m).T)
        else:
            # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
            # print("LINEAR_ALGEBRA m = ", m );
            # print("LINEAR_ALBEBRA y = ", y[0] );
            return x * (m * conjugate(y[0])).T  # }}}


class NewKetBra(sympy.MatrixExpr):
    """
    This reimplementation of the cross product is necessary for sympify to generate a correct expression tree with
    the correct matrix operators instead of the standard scalar ones. For example sympify('5*cross(a,b)'),
     without any special handling, generates an expression tree with Mul instead of MatMul. Because of how sympy handles
     matrices this will result in a runtime error when eventually the cross products gets replaced with an actual matrix.
    """

    def __new__(cls, arg1, arg2):
        return sympy.Basic.__new__(cls, arg1, arg2)

    @property
    def shape(self):
        return self.args[0].shape

    def doit(self, **hints):
        x = self.args[0].doit() if isinstance(self.args[0], sympy.Basic) else self.args[0]
        y = self.args[1].doit() if isinstance(self.args[1], sympy.Basic) else self.args[1]
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return x * conjugate(y).T
        else:
            return self


class KetMBra(sympy.MatrixExpr):
    """
    This reimplementation of the cross product is necessary for sympify to generate a correct expression tree with
    the correct matrix operators instead of the standard scalar ones. For example sympify('5*cross(a,b)'),
     without any special handling, generates an expression tree with Mul instead of MatMul. Because of how sympy handles
     matrices this will result in a runtime error when eventually the cross products gets replaced with an actual matrix.
    """

    def __new__(cls, arg1, arg2, arg3):
        return sympy.Basic.__new__(cls, arg1, arg2, arg3)

    @property
    def shape(self):
        return self.args[0].shape

    def doit(self, **hints):
        x = self.args[0].doit() if isinstance(self.args[0], sympy.Basic) else self.args[0]
        m = self.args[1].doit() if isinstance(self.args[1], sympy.Basic) else self.args[1]
        y = self.args[2].doit() if isinstance(self.args[1], sympy.Basic) else self.args[2]
        # print("XMY = ", x, m, y )
        if (
            isinstance(x, sympy.MatrixBase)
            and isinstance(m, sympy.MatrixBase)
            and isinstance(y, sympy.MatrixBase)
        ):
            return MatMul(x, (m * conjugate(y)).T)
        else:
            return self


class BraketBroken(Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            return conjugate(x).T.dot(m)
        else:
            return x.adjoint().dot(m * y[0])  # }}}


class nullrank(Function):  # {{{
    nargs = 2

    @classmethod
    def eval(cls, zmat, mvars):
        global varstonumeric  # MAKE THIS CLASS OBJECT INSTEAD
        try:
            subs = varstonumeric
            variables = list(mvars)
            # print( "norm = ", zmat.subs(subs).norm() )
            free1 = list(zmat.subs(subs).free_symbols)
            # print( "free1 = ", free1 )
            if len(free1) > 0:
                return sympify('NONFREE')
            if not (zmat.subs(subs).norm()).equals(0):
                # print("DOES IS NOT EQUAL ZERO")
                return sympy.sympify('NONZERO')
            zlist = list(zmat)
            jac = []
            for zrow in zlist:
                row = []
                for var in variables:
                    row.append(diff(zrow, var))
                jac.append(row)
            jacobian = Matrix(jac).subs(subs)
            null = jacobian.nullspace()
            # print("FREE = ", free1)
            nullrank = len(null)
            # print("NULLRANK RETURNS", nullrank)
            return sympy.sympify(nullrank)
        except Exception as e:
            # print("RETURNING 99")
            return sympy.sympify('UKNOWNERROR')  # }}}
