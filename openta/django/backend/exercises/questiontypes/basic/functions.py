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
from exercises.questiontypes.core.functions import core_defs, Partial

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


class Wedge( sympy.Function ):

    @classmethod
    def eval( cls, *arg ):
        m = [ *arg ];
        rul =  m.pop()
        atoms = rul.atoms(Symbol);
        res = Add( expand( Mul( *m ) , evaluate=True).doit() , 0 )
        funcname = res.func.__name__
        if funcname == 'Add' :
            s = 0
            addargs = res.args
            for a in addargs:
                a = simplify( a.subs(rul) )
                if a.func.__name__ == 'Mul' :
                    margs = a.args;
                    prod = 1 ;
                    diffs = [ i for i in margs if i in atoms  ]
                    ndiffs = [ i for i in margs if not i in atoms ]
                    prod = 1;
                    if ndiffs :
                        prod = Mul( *ndiffs );
                    if diffs :
                        nprod = Mul( *diffs ).subs(rul)
                        prod = prod * nprod
                    a = prod
                s = s + a;
            res = s 
        resn = simplify( res.subs(rul) , evaluate=True).doit()
        return resn


class dD( sympy.Function ):

    # d( g) :=  dr D( g, r ) + dtheta D(g, theta ) + dzp D( g, zp );
    nargs = 4;
    @classmethod
    def eval(cls, fF , dd,vx,vv ):
        ismatrix = False
        spold = (0,0)
        if 'Matrix' in str( type( fF) ) :
            F = flatten( fF )
            ismatrix = True
            spold = shape( fF)
        else :
            F = list( [fF] )
        res3 = [];
        for f in F :
            dd = list( dd)
            xx = [Symbol(str(i)[1:] ) for i in dd ];
            #xx = list( xx )
            #print(f"TYPE = {type(vv)}")
            spold = None
            vflat = flatten( vv);
            #print(f"VFLAT = {vflat}")
            row_size = len( vx );
            if len( vflat) == row_size :
                vv = vflat
            else :
                vv = [ vflat[ i * row_size  : ( i+1) * row_size  ]  for i in range( 0, int( len(vflat)/row_size ) ) ]
            #print(f"VV = {vv}")
            res = 0
            i = 0;
            for ds in dd :
                res = res + ( ds * Partial( f , xx[i] )  ) 
                i = i + 1;
            i = 0;
            subrule = {};
            for x in xx :
                subrule.update({ xx[i] :   vx[i],  } );
                i = i + 1
            i = 0 ;
            for ds in dd :
                if isinstance(vv[i],  list ):
                    vv[i] = Matrix( vv[i] )
                #print(f"TYPE = {type( vv[i] )}")
                subrule.update({ sympify( ds )  :  vv[i] ,} );
                i  = i + 1;
            #print(f"RES = {res}")
            #print(f"SUBRULE = {subrule}")
            res2 = res.subs( subrule )
            res3.append( res2 )
        if ismatrix and 'list' in str( type( res3 ) ) :
            try :
                rows = len( vv );
                i = 0;
                res4 = 0 * ( vv[0] * res3[0].T )
                for r in res3 :
                    res4 =  res4 + ( vv[i] ) * r.T
                    i = i + 1
                res4 = res4
            except Exception as e :
                res4 = Transpose( Matrix( res3 ) )
        elif ismatrix :
            res4 = Transpose( Matrix(res3) )
        else :
            res4 = res3[0];
        return res4










basic_defs = {
    "myPartial" : partial,
    "Wedge": Wedge,
    "dD" : dD, 
}

basic_defs.update(core_defs)
