# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging

import numpy
import sympy
from sympy import *
from sympy import DiagonalOf

# from sympy.abc import _clash1, _clash2, _clash, x, y, z
from sympy.abc import x, y, z
from sympy.matrices import Matrix

from sympy import symbols, simplify;
from sympy.physics.quantum.operatorordering import normal_ordered_form 
from sympy.physics.quantum.boson import BosonOp as BosonOp;
from sympy.physics.quantum import Dagger, Commutator

b = "b";


logger = logging.getLogger(__name__)


class Norm(sympy.Function):
    @classmethod
    def eval(cls, x):
        # logger.debug("Norm is entered with x = %s", x )
        # logger.debug("type = %s", type(x) )
        if isinstance(x, sympy.MatrixBase):
            res = N(x.norm())
            # logger.debug("result = %s", res )
            return res
        # else:
        #    return Abs(x)
        elif isinstance(x, Number):
            # logger.debug("identified float")
            return abs(x)
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
            # logger.debug("EV = %s", ev )
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
            diff = ev - Sort(x)
            mag = numpy.vdot(diff, diff)  # conjugate(diff).dot(diff)
            if mag <= 1e-6:
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")
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
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")

        else:
            return None


class mymul(sympy.Function):
    nargs = (1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *arg):
        for a in arg:
            if not isinstance(a, sympy.MatrixBase):
                return None
        return sympy.MatMul(*arg)


class localtranspose(sympy.Function):
    @classmethod
    def eval(cls, x):
        print(f"LOCAL_TRANSPOSE_UTILS")
        if isinstance(x, sympy.MatrixBase):
            return x.T
        else:
            return None


class rankof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            # logger.debug("MATREIX FOUND RANKOF %s", x)
            sp = x.shape
            rank = sp[1]
            return sympy.sympify(rank)
        else:
            # logger.debug("MATREIX FOUND RANKOF %s", x)
            return None


class is_zero_matrix(sympy.Function):
    @classmethod
    def eval(cls, x):
        logger.debug("X  = %s", x)
        if max(map(abs, list(x))) < 1.0e-6:
            return sympy.sympify("1")
        else:
            return sympy.sympify("0")


class isunitary(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            sp = x.shape
            target = eye(sp[1])
            # logger.debug("target = %s", target )
            zer = (x * conjugate(x.T)) - target
            # logger.debug("zer = %s", zer )
            zer = zer.evalf(6, chop=True)
            # logger.debug("ZER = %s", zer)
            return is_zero_matrix(zer)
        else:
            return None


class IsHermitian(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            logger.debug("IsHermitian x = %s", x)
            logger.debug("conjugate(x.T) %s", conjugate(x.T))
            zer = x - conjugate(x.T)
            return is_zero_matrix(zer)
            # zer = list( zer.evalf(5, chop=True) )

            # test =  max( map( abs, zer) )
            # if test < 1.e-6 :
            #    return sympy.sympify('1')
            # else:
            #    return sympy.sympify('0')
        else:
            return None


class crossfunc(sympy.Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, *arg):
        if len(arg) == 2:
            x = arg[0]
            y = arg[1]
            if not (isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase)):
                raise TypeError("cross product has illegal arguments")

            if str(x) == "0" or str(y) == "0":
                return 0
            return x.cross(y)
        else:
            raise TypeError("cross product needs two arguments")


class Cross(sympy.MatrixExpr):
    def __new__(cls, arg1, arg2):
        return sympy.Basic.__new__(cls, arg1, arg2)

    @property
    def shape(self):
        return self.args[0].shape

    def doit(self, **hints):
        x = self.args[0].doit() if isinstance(self.args[0], sympy.Basic) else self.args[0]
        y = self.args[1].doit() if isinstance(self.args[1], sympy.Basic) else self.args[1]
        # logger.debug("enter Cross with x  = %s", x , type( x ))
        # logger.debug("enter Cross with y = %s", y , type( y ) )
        if str(x) == "0":
            # logger.debug("IDENTIFIED ZERO x ")
            return 0 * y
        elif str(y) == "0":
            # logger.debug("IDENTIFIED ZERO x ")
            return 0 * x
        elif isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return x.cross(y)
        else:
            raise TypeError("Illegal argument in cross product")


class Sort(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            xs = x.tolist()
            xs = sorted(xs, key=default_sort_key)
            # logger.debug("xs = %s",  xs )
            return sympy.Matrix(xs)
        else:
            return None


class gt(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        # logger.debug("GT ENTERED")
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            x = x.doit()
            y = y.doit()
            if Gt(x, y):
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")
        else:
            return None


class lt(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            x = x.doit()
            y = y.doit()
            # logger.debug("LT x = %s", x )
            if Lt(x, y):
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")
        else:
            return None


class localge(sympy.Function):
    nargs = (1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, x, y):
        try:
            if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
                try:
                    x = x.doit()
                    y = y.doit()
                    if Ge(x, y):
                        return sympy.sympify("1")
                    else:
                        return sympy.sympify("0")
                except Exception:
                    print("ERROR LOCALEGE {type(e).__name__}")
                    return None
            else:
                return None
        except Exception as e:
            logger.error(f"ERROR LOCALGE2 {type(e).__name__}")
            return sympy.sympify("1")


class ge(sympy.Function):
    nargs = (1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, x, y):
        try:
            return sympy.sympify("1")
            if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
                try:
                    x = x.doit()
                    y = y.doit()
                    if Ge(x, y):
                        return sympy.sympify("1")
                    else:
                        return sympy.sympify("0")
                except Exception as e:
                    logger.error(f"ERROR GE {type(e).__name__}")
                    return None
            else:
                return None
        except Exception as e:
            logger.error(f"ERROR GE2 {type(e).__name__}")
            return sympy.sympify("1")


class le(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            x = x.doit()
            y = y.doit()
            if Le(x, y):
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")
        else:
            return None


class eq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return is_zero_matrix(x - y)
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (isinstance(x, Integer) or isinstance(x, Float)):
            if x.n() == y.n():
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")
        else:
            return None


class neq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return 1 - is_zero_matrix(x - y)
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (isinstance(x, Integer) or isinstance(x, Float)):
            if x.n() == y.n():
                return sympy.sympify("0")
            else:
                return sympy.sympify("1")
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
            return sympy.sympify("1")
        else:
            return sympy.sympify("0")


class logicalor(sympy.Function):
    @classmethod
    def eval(cls, *x):
        tot = 0
        for tval in x:
            if Not(isinstance(tval, sympy.Integer)):
                return None
            tot = Or(tot, tval)
        if tot:
            return sympy.sympify("1")
        else:
            return sympy.sympify("0")


class logicalnot(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.Integer):
            if x > 0:
                return sympy.sympify("0")
            else:
                return sympy.sympify("1")
        else:
            return None


class Dot(sympy.Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, *arg):
        if len(arg) == 1:
            t = sympy.symbols("t")
            res = diff(arg[0], t)
            return res
        if len(arg) == 2:
            x = arg[0]
            y = arg[1]
            if str(x) == "0" or str(y) == "0":
                return 0
            elif isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
                # logger.debug("DOT PRODUCT x %s", x )
                # logger.debug("DOT PRODUCT y %s", y )
                ret = numpy.vdot(x, y)
                # logger.debug("DOT PRODUCT ret = %s", srepr( ret )  )
                return ret
            else:
                logger.debug("X = %s", type(x), x)
                logger.debug("Y = %s", type(y), y)
                raise TypeError("Illegal argument of dot product")


class Times(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return sympy.matrix_multiply_elementwise(x, y)
        else:
            raise TypeError("Illegal arguments of elementwise multiply")


class IsDiagonal(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            if x.is_diagonal():
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")


#
# INCLUDE THIS IN SCOPE OF symbolic
# SO THAT SYMBOLIC QUESTION IS BACKWARD COMPATIBLE
# SINCE SYMBOLIC DOES NOT DO sample
#


# class sample(sympy.Function):
#    @classmethod
#    def eval(cls, *x):
#        return x[0]


class grad(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, fun):
        from sympy.abc import x, y, z

        res = [diff(fun, x), diff(fun, y), diff(fun, z)]
        res = sympy.sympify(Matrix(res))
        res = res.doit()
        return res


class del2(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, fun):
        from sympy.abc import x, y, z

        res = diff(fun, x, x) + diff(fun, y, y) + diff(fun, z, z)
        res = res.doit()
        return res


class curl(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, M):
        if M.is_Matrix:
            res = [
                diff(M[2], y) - diff(M[1], z),
                diff(M[0], z) - diff(M[2], x),
                diff(M[1], x) - diff(M[0], y),
            ]
            return sympy.sympify(Matrix(res))
        else:
            return None


class localdiv(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, M):
        if isinstance(M, sympy.MatrixBase):
            res = diff(M[0], x) + diff(M[1], y) + diff(M[2], z)
            return sympy.sympify(res)


class IsDiagonalizable(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        # logger.debug("IS DIAGONALIZABLE %s", x)
        if isinstance(x, sympy.MatrixBase):
            if x.is_diagonalizable():
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")
        else:
            return None


class oldPrime(sympy.Function):
    nargs = (1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *arg):
        # logger.debug("PRIME ENTERED")
        arg[0]
        fourth = arg[3]
        order = int(arg[2])
        qqq = sympy.symbols("qqq")
        corefunc = "FunctionClass" in str(type(arg[3]))
        if not corefunc:
            deriv = fourth
            # qqq = list(fourth.free_symbols)[0]
            deriv = deriv.func(qqq)
            while order > 0:
                order = order - 1
                deriv = diff(deriv, qqq)
            result = deriv.subs(qqq, arg[1]).doit()
        else:
            fun = fourth
            deriv = fun(qqq)
            while order > 0:
                order = order - 1
                deriv = diff(deriv, qqq)
            result = deriv.subs(qqq, arg[1])
        return result


class Prime(sympy.Function):
    nargs = (1, 2, 3, 4, 5, 6)

    @classmethod
    def eval(cls, *arg):
        # logger.debug(" INTO PRIME WITH %s", *arg)
        first = arg[0]
        # fourth = arg[3]
        order = int(arg[2])
        # logger.debug("first = %s", first)
        # logger.debug("second = %s", arg[1])
        # logger.debug("third = %s", arg[2])
        # logger.debug("FOURTH = %s", fourth )
        qqq = sympy.symbols("qqq")
        fun = first.func
        # logger.debug("FUN = %s", srepr(fun), flush=True)
        deriv = fun(qqq)
        while order > 0:
            order = order - 1
            deriv = diff(deriv, qqq)
        result = deriv.subs(qqq, arg[1]).doit()
        return result


class Partial(sympy.Function):
    nargs = (1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *f):
        if len(f) < 1:
            return sympy.sympify("derivative or partial used withouth argument")  # }}}
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
            return sympy.sympify("derivative or partial used with too many arguments")  # }}}


class carefuladd(sympy.Function):
    @classmethod
    def eval(cls, *args):
        rank = 1
        for arg in args:
            if hasattr(arg, "shape"):
                if arg.is_square:
                    rank = (arg.shape)[0]
        if not rank == 1:
            newargs = []
            for arg in args:
                if not hasattr(arg, "shape"):
                    newargs = newargs + [eye(rank) * arg]
                else:
                    newargs = newargs + [arg]
            return Add(*newargs)
        else:
            return Add(*args)


class partial(sympy.Function):
    nargs = (0, 1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *f):
        # logger.debug("PARTIAL f = %s", f)
        if len(f) < 1:
            return sympy.sympify("derivative or partial used withouth argument")  # }}}
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
            return sympy.sympify("derivative or partial used with too many arguments")  # }}}


class Braket(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return numpy.vdot(x, y)
        else:
            return None


class KetBraBroken(sympy.Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):
        if len(y) == 0:
            if isinstance(x, sympy.MatrixBase) and isinstance(m, sympy.MatrixBase):
                # logger.debug("MULTIPLYING LINEAR_ALGEBRA x = %s", x );
                # logger.debug("LINEAR_ALGEBRA m = %s", m );
                return x * m.adjoint()
            else:
                return None
        else:
            if (
                isinstance(x, sympy.MatrixBase)
                and isinstance(m, sympy.MatrixBase)
                and isinstance(y[0], sympy.MatrixBase)
            ):
                # logger.debug("MULTIPLYING LINEAR_ALGEBRA x = %s", x );
                # logger.debug("LINEAR_ALGEBRA m = %s", m );
                # logger.debug("LINEAR_ALBEBRA y = %s", y[0] );
                return x * m * y[0].adjoint()  # }}}
            else:
                return None


class KetBra(sympy.Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):
        if len(y) == 0:
            # logger.debug("MULTIPLYING LINEAR_ALGEBRA x = %s", x );
            # logger.debug("LINEAR_ALGEBRA m = %s", m );
            return MatMul(x, conjugate(m).T)
        else:
            # logger.debug("MULTIPLYING LINEAR_ALGEBRA x = %s", x );
            # logger.debug("LINEAR_ALGEBRA m = %s", m );
            # logger.debug("LINEAR_ALBEBRA y = %s", y[0] );
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
        # logger.debug("XMY = %s, %s. %s", x, m, y )
        if isinstance(x, sympy.MatrixBase) and isinstance(m, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return MatMul(x, (m * conjugate(y)).T)
        else:
            return self


class iden(Function):  # {{{
    @classmethod
    def eval(cls, x):
        print(f"IDEN {x}")
        return x


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
            # logger.debug( "norm = %s", zmat.subs(subs).norm() )
            free1 = list(zmat.subs(subs).free_symbols)
            # logger.debug( "free1 = %s", free1 )
            if len(free1) > 0:
                return sympify("NONFREE")
            if not (zmat.subs(subs).norm()).equals(0):
                # logger.debug("DOES IS NOT EQUAL ZERO")
                return sympy.sympify("NONZERO")
            zlist = list(zmat)
            jac = []
            for zrow in zlist:
                row = []
                for var in variables:
                    row.append(diff(zrow, var))
                jac.append(row)
            jacobian = Matrix(jac).subs(subs)
            null = jacobian.nullspace()
            # logger.debug("FREE = %s", free1)
            nullrank = len(null)
            # logger.debug("NULLRANK RETURNS %s", nullrank)
            return sympy.sympify(nullrank)
        except Exception as e:
            # logger.debug("RETURNING 99")
            return sympy.sympify(f"UKNOWNERROR {type(e).__name__}")  # }}}

class NormalOrdered(sympy.Function):
    nargs = 1
    @classmethod
    def eval(cls, x):
        from sympy.physics.quantum.operatorordering import normal_ordered_form 
        #from sympy.physics.quantum.boson import BosonOp;
        #from sympy.physics.quantum import Dagger, Commutator
        #from sympy import sympify, srepr;
        bb = "bg";
        print(f"SREPR1_X  = {srepr(x)}")
        x  = eval(f"{x}");
        print(f"SREPR2_X  = {srepr(x)}")
        print(f"NORMAL ORDERED x = {x}  type={ type(x) }  ")
        y = normal_ordered_form(x);
        b = BosonOp("b");
        bd = Dagger(b);
        z = normal_ordered_form(b*bd);
        print(f"p = {b*bd} { type(b*bd)} ")
        assert True , f"x={x} y={y} z={z} ";
        print(f"x={x} y={y} z={z}")
        return sympy.sympify("1");

#scope.update(  { "A" : sympy.physics.quantum.boson.BosonOp("a")  ,
#                 "no" : NormalOrdered
#                 } )


openta_scope = {
    "no" : NormalOrdered,
    "abs": Norm,  # sympy.Function('norm')
    "Abs": Norm,  # sympy.Function('norm')
    "Trace": Trace,
    "Transpose": localtranspose,
    "iden": iden,
    "localtranspose": localtranspose,
    "AreEigenvaluesOf": eigenvaluesof,
    "AreEigenvaluesOf": AreEigenvaluesOf,
    "IsDiagonalizationOf": IsDiagonalizationOf,
    "IsHermitian": IsHermitian,
    "RankOf": rankof,
    "IsUnitary": isunitary,
    "cross": crossfunc,
    "mul": mymul,
    "crossfunc": crossfunc,
    "Gt": gt,
    "localGt": gt,
    "localLt": lt,
    "Ge": ge,
    "localGe": localge,
    "Lt": lt,
    "Le": le,
    "Or": logicalor,
    "localOr": logicalor,
    "And": logicaland,
    "localAnd": logicaland,
    "curl": curl,
    "div": localdiv,
    "localdiv": localdiv,
    "grad": grad,
    "Partial": partial,
    "partial": partial,
    "Prime": Prime,
    "Not": logicalnot,
    "localNot": logicalnot,
    "IsEqual": eq,
    "IsNotEqual": neq,
    "diagonalpart": diagonalof,
    "IsDiagonal": IsDiagonal,
    "IsDiagonalizable": IsDiagonalizable,
    "true": sympy.sympify("1"),
    "false": sympy.sympify("0"),
    "True": sympy.sympify("1"),
    "False": sympy.sympify("0"),
    "times": Times,
    "mydot": Dot,
    "dot": Dot,
    "del2": del2,
    "sort": Sort,
    "Sort": Sort,
    "norm": Norm,
    "KetBra": KetBra,
    "KetMBra": KetMBra,
    "Braket": Braket,
    "NullRank": nullrank,
    #'sample': sample,
}
add_scope = {
    "carefuladd": carefuladd,
}
