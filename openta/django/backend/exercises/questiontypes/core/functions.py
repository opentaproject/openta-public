# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import re as resub




import numpy
import sympy
from sympy import *
from exercises.util import  mychop, COMPARISON_PRECISION, p53


from sympy.abc import x, y, z

from sympy import symbols, simplify;

logger = logging.getLogger(__name__)

class is_zero_matrix(sympy.Function):
    @classmethod
    def eval(cls, x):
        x = N( x, chop=True )
        if max(map(abs, list(x))) < 1.0e-6:
            res = sympy.sympify("1")
        else:
            res = sympy.sympify("0")
        return res

class myset( sympy.Function ):

    @classmethod
    def eval( cls, *arg ):
        x = arg[0]
        if len( arg ) == 1 :
            y = list(x)
            s = FiniteSet( *y );
        else :
            s = FiniteSet( *arg )
        return s



class myabs(sympy.Function):
    @classmethod
    def eval(cls, x):
        #logger.error(f"myabsis entered with {x} {type(x)}")
        #logger.error(f"myabs type = {type(x)} {x}")
        name = x.func.__name__
        if 'Matrix' in name :
            vl = list( x );
        elif 'Array' in name :
            vl = list( x) 
        elif isinstance( x, list ):
            vl = x ;
        else :
            vl = [x];
        sum = 0;
        for i in vl:
            sum += i*conjugate(i)
        res = sqrt(sum);
        return res
        #    return None


class eq(sympy.Function):
    nargs = (1,2,3,4,5)

    @classmethod
    def eval(cls, *xs ):
        s = f"XS = {xs}"
        s = resub.sub(r"\n",' ', s )
        #print(f"{s}")
        x = simplify( mychop( xs[0] ) );
        y = simplify( mychop( xs[1] ) );
        s = f"EQUAL {x} AND  {y}"
        s = resub.sub(r"\n",' ',s)
        #print(f"{s}")
        if 'Matrix' in str( type(x) ) :
            x = N( x.doit(), p53 );
            y = N( y.doit(), p53 );
            scale = ( myabs(  x )  + myabs(y) )  
            if scale == 0 :
                scale = 1 ;
            diff = simplify( mychop( x - y ) )
            if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
                res = is_zero_matrix(  diff  / scale )
            else  :
                if myabs( diff )  < COMPARISON_PRECISION   * scale :
                    res = sympy.sympify("1")
                else:
                    res = sympy.sympify("0")



        elif (isinstance(x, Integer) or isinstance(x, Float)) and (isinstance(x, Integer) or isinstance(x, Float)):
            res = sympy.sympify("1") if ( abs( x - y ) < COMPARISON_PRECISION )  else  sympy.sympify("0")
        else:
            #res = sympy.sympify("1") if x == y  else  sympy.sympify("0")
            diff = simplify( x - y ) 
            if diff.free_symbols :
                res = sympy.sympify("0")
            else :
                res = sympy.sympify("1") if ( abs( diff ) < COMPARISON_PRECISION )  else  sympy.sympify("0")
        return res



class oldeq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            if myabs( x - y ) == 0  :
                res = sympy.sympify("1")
            else:
                res = sympy.sympify("0")
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (isinstance(x, Integer) or isinstance(x, Float)):
            if x.n() == y.n():
                return sympy.sympify("1")
            else:
                return sympy.sympify("0")
        else:
            return None

        return res


class neq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        #print(f"NOT EQUAL" , srepr(x) , srepr(y) )
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            if x.n() == y.n():
                return sympy.sympify("0")
            else:
                return sympy.sympify("1")
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (isinstance(x, Integer) or isinstance(x, Float)):
            if x.n() == y.n():
                return sympy.sympify("0")
            else:
                return sympy.sympify("1")
        else:
            return None

class Partial(sympy.Function):
    nargs = (1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *f):
        allargs = [*f];
        #logger.error(f"Partial {allargs}")
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



class partial(sympy.Function):
    nargs = (0, 1, 2, 3, 4, 5)

    @classmethod
    def eval(cls, *f):
        if len(f) < 1:
            return sympy.sympify("derivative or partial used withouth argument")  # }}}
        elif len(f) == 1:
            fun = f[0]
            x = list(fun.free_symbols)[0]
            res = diff(fun, x)
            return res
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

class dot( sympy.Function ) :
    nargs = (2)

    @classmethod
    def eval( cls, *arg ):
        x =   arg[0];
        y =   arg[1];
        #if 'Matrix' in str( type(x) ) and 'Matrix' in str( type(y) ) :
        if hasattr( x, 'dot' ):
            ret = x.dot( y.T );
            return ret
        else :
            return None





class myFactorial( sympy.Function):
    nargs = (0,1,2) 

    @classmethod 
    def eval( cls , *arg ) :
        x = list( arg )[0]
        if x.is_number :
            res = factorial(x)
            return res
        else :
            return None







core_defs = {
    "abs": myabs,
    "true": sympy.sympify("1"),
    "false": sympy.sympify("0"),
    "True": sympy.sympify("1"),
    "False": sympy.sympify("0"),
    "exp" : sympy.exp,
    "Partial": Partial,
    "partial": Partial,
    "Prime" : Prime,
    "myFactorial" :  myFactorial,
    "dot" : dot,
    "IsEqual": eq,
    "AreEqual": eq,
    "myabs" : myabs,
    "arcsin" : asin,
    "arccos" : acos,
    "set" : myset,
    "atan" : atan,
    "eq" : eq,
    "IsNotEqual": neq,
    "AreNotEqual": neq,
    "sample": sympy.Function('sample'),

}
