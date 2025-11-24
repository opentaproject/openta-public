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
from exercises.util import mychop, COMPARISON_PRECISION, CLEAN_PRECISION

from sympy import symbols, simplify;
from sympy.physics.quantum.operatorordering import normal_ordered_form 
from sympy.physics.quantum.boson import BosonOp as BosonOp;
from sympy.physics.quantum import Dagger, Commutator
from exercises.util import p53

b = "b";

logger = logging.getLogger(__name__)

# SEE ALSO levicivita  in this file

def dear( expr):
    bdefs   = {'MyArray' : {'name' : '',"left":'[' , "right" : ']' } };
    if expr.args :
        f = expr.func.__name__;
        fn = bdefs.get(f,{'name' : f , "left" : '(' , "right" :')'})
        s =  f'{fn["name"]}{fn["left"]}' + ",".join( [  dear( i) for i in expr.args]) + f'{fn["right"]}' 
    else :
        s = str( expr)
    return s;



class matrixElements( sympy.Function ):
    nargs = (0,1,2) 

    @classmethod 
    def eval( cls , *arg ) :
        m = arg[0];
        second = arg[1];
        if second.is_number :
            second = [int( second) ]
        funcname = m.func
        if str(funcname) == 'MyArray' :
            d = sympy.sympify( dear(m) ) 
            ii =  list( second);
            if len( ii ) == 1 :
                res = d[  ii[0] - 1 ]
            else :
                res = d[ ii[0] - 1][ ii[1] - 1 ]
            if isinstance( res , list ) :
                res = Transpose( Matrix( res ) ).doit()
            return res
        elif 'Symbol' in str(funcname) : 
            return None


        dims = list( shape( m ) )
        ii =  list( second);
        #print(f"II = {ii} and dims = {dims}")
        if len(ii) == 1 and len(dims) == 2  and not 1 in dims :
            res = Transpose( m.row( ii[0] - 1 ) ).doit() 
            return res
        assert  not ( len( ii ) == 1 and not 1 in dims  ) , f"You need a pair of  indexes; the array has dimensions {dims} "
        if len(dims) != len( ii ) :
            if dims[1] == 1 :
                ii = [ ii[0] , 1  ]
            elif dims[0] == 1 :
                ii = [1 , ii[0] ]
        assert ii[0] > 0 , "The matrix base is 1,1; dimension zero not allowed"
        assert ii[1] > 0 , "The matrix base is 1,1]; dimension zero not allowed"
        assert ii[0] <= dims[0] , f"index exceeds the dimension {dims[0]}"
        assert ii[1] <= dims[1] , f"index exceeds the dimension {dims[1]}"
        res = m.row(ii[0] - 1 )[ii[1] - 1 ]
        return res



def levi(i,j,k):
    if i == j or i == k or j == k :
        return 0
    elif [i,j,k] in   [ [0,1,2],[1,2,0],[2,0,1]  ] :
        return 1
    else :
        return -1 
    
def RotationMatrix(n,theta ):
    v = [[0,0,0],[0,0,0],[0,0,0] ]
    #print(f"N = ", n )
    for i in  range(0,3) :
        for j in range(0,3):
            s =  ( 1 - cos(theta) ) * n[i] * n[j];
            if i == j :
                s = s + cos(theta) 
            for k in range(0,3):
                    s =  s - n[k] * sin(theta) * levi( i,j,k )
            v[i][j] = s;
    
    return Matrix( v )


def quicksort(arr): 
    sign = 1;
    if len( set(arr) ) != len( arr )  :
        return (arr, 0 );
    if len(arr) <= 1:
        return (arr,sign)
    else:
        pivot = arr[0]
        lessi = [i  for i  in range(0,len(arr) )  if arr[i]  <= pivot ];
        for i in range(0,len(lessi) ) :
            sign = sign * ( -1 )**( lessi[i] - i )
        less = [x for x in arr[1:] if x <=  pivot]
        greater = [x for x in arr[1:] if x > pivot]
        head,s1 = quicksort(less);
        tail,s2 = quicksort( greater)
        sign =  sign * s1 * s2 ;
        if len(head) % 2 == 1 :
            sign = sign * -1 ;
        return ( head + [pivot] + tail, sign)


def levicivita(arr) :
    _,sign = quicksort(arr)
    return sign;

def flatten(data ):

    def traverse(o, tree_types=(list, tuple, Matrix)):
        if isinstance(o, tree_types):
            for value in o:
                for subvalue in traverse(value, tree_types):
                    yield subvalue
        else:
            yield o
        
    return list( traverse(data))

class mycross( sympy.Function ):
    nargs = (2)

    @classmethod 
    def eval( cls, x, y ):
        xfunc = str( type(x) )
        yfunc = str( type(y) )
        if 'MyArray' in yfunc :
            y = Matrix( y.args)

        if 'MyArray' in xfunc :
            x = Matrix( x.args)

        res = Matrix(x).cross( Matrix(y) )
        return res

class AreOrthogonal( sympy.Function ):
    nargs = (1,2,3,4,5,6)

    @classmethod
    def eval( cls , *xx ):
        xs = [*xx ]
        x = xs.pop(0)
        while xs :
            r = xs.pop(0)
            (nr,nc) = shape( r )
            if nc == 1 :
                r = r.transpose()
            x = x.row_insert( len(x) ,  r  )
        dim,_ = shape(x)
        for i in range(0, dim ):
            ir = x.row(i);
            res = mychop( ir.dot(ir) )
            if res == 0 :
                assert False, f"{ir} has length 0 "

        for i in range(0,dim):
            for j in  range(0,i):
                res = mychop( ( x.row(i) ).dot( x.row(j) ) )
                if not res == 0 :
                    ir = list( x.row(i) )
                    jr = list( x.row(j) )
                    assert False, f"{ir}  is not orthogonal to {jr}"

        return sympify('1')

class myabs(sympy.Function):
    @classmethod
    def eval(cls, x):
        x = x.doit();
        #logger.error(f"myabsis entered with {x} {type(x)}")
        #logger.error(f"myabs type = {type(x)} {x}")
        name = x.func.__name__
        if 'Matrix' in name :
            vl = list( x );
        elif 'Array' in name :
            vl = list( [ * x.args ] ) 
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


class Norm(sympy.Function):
    @classmethod
    def eval(cls, x):
        # logger.debug("Norm is entered with x = %s", x )
        # logger.debug("type = %s", type(x) )
        if isinstance(x, sympy.MatrixBase):
            res = N(x.norm(), p53)
            # logger.debug("result = %s", res )
            return res
        else:
            return Abs(x)
        #elif isinstance(x, Number):
        #    # logger.debug("identified float")
        #    return abs(x)
        #else:
        #    return None


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
            return N(x.trace(), p53)
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

class Eigenvalues( sympy.Function ):
    nargs = 1 ;

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase) :
            evdict = FiniteSet( * ( x.eigenvals(multiple=True) ))
            return evdict
class oldhat( sympy.Function ):
    @classmethod
    def eval(cls, x):
        args = list( x );
        #print(f"ARGS = ", args )
        #print(f"HAT IS CALLED with {x} ",  )
        if isinstance(x, sympy.MatrixBase) :
            res = x / Norm(x);
            #print(f"X = {x} RES = {res}")
            return res
        else :
            return x


class NullSpaceOf( sympy.Function ):
    nargs = 1 ;

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase) :
            res = x.nullspace()
            return res

class  IsNullSpaceOf(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            n_ = x.nullspace();
            n = [];
            for i in n_ :
                n.append( list(i) );
            n = N(Matrix(n), p53 )
            ni = ( N( n.pinv(), chop=True ) )
            (nnr,nnc) =  shape(x);
            (ynr,ync) = shape(y);
            #assert ynr == nnr , f"Number of rows  in your answer is {ynr}  is not correct"
            assert ync == nnc , f"Your number of columns is  {ync} but should be {nnc}"
            id = N(    y  * ni , 8 , chop=True);
            #print(f"ID = {id}")
            diff = id * n - y ;
            ck = Trace( diff * diff.adjoint() ).doit() 
            #print(f"CK = {ck}")
            if ck < 1.e-16 :
                return sympy.sympify("1")
            else :
                return sympy.sympify("0")


def RotationArguments( m ):
    theta = acos( simplify( 1/2 *  ( Trace(m) -  1 )  )).doit();
    ma = m - Transpose(m);
    c =  simplify( 1/2 *  ( Trace(m) -  1 )  ).doit();
    s = sqrt( 1 - c**2);
    v = Matrix( [ - ma[1,2], ma[0,2],-ma[0,1] ] )/( 2 * s );
    theta = acos(c);
    return ( v, theta )


def ToNestedList( m ):
    #print(f"TO NESTED_LIST M = {m} ")
    (nr,nc) = shape(m);
    l = list(m);
    mn = [];

    for i in range(0,nr) :
        mn.append( l[i * nc : i * nc + nc ] );
    #print(f"RETURN MN {mn}")
    return mn;

def AreEigenvectorsOf(m,mtests):

    sp = [ * shape( mtests ) ]
    if len( sp) > 0 :
        if sp[1] == 1 :
            mtests = mtests
    #print(f"SP = {sp}")
    tests = ToNestedList( mtests )
    try :
        #print(f"MTESTS = {mtests}")
        sp = [ * shape( mtests ) ]
        #print(f"SP = {sp}")
        if len(sp) >  1 :
            if sp[1] == 1 :
                mtests = ToNestedList( mtests.T) 
        #print(f"AREEIVENVECTORSOF M = {m}")
        evcs = m.eigenvects(multiple=False);
        evs = [];
        for evc in evcs:
            _,_,vs = evc
            for v in vs:
                evs.append(list(v));
        mv = Matrix( evs);
        #print(f"MV = {mv}")
        nrin  = len( tests );
        nc  = len( mv.nullspace() )
        #print(f" MTESTSS = {mtests}")
        nct = len( ( Matrix( tests) ).nullspace() )
        ncin = len( tests[0] );
        #print(f"NCIN = {ncin}")
        #print(f"NULL SPACE OF TESTS HA RANK nct = {nct}")
        #print(f"NULLSPACE OF M HA DIM nc = {nc}")
        assert len(tests) == ncin - nc , "Null space of answer does not have correct number of rows" 
        assert nct == nc, "Null space of answer does not have correct rank"
        for t  in tests:
            #print(f"TEST T = {t}")
            res = list( m * Matrix(t) );
            pair = Matrix( [ res , t ] );
            pn1 = len( ( Matrix([t])).nullspace() );
            pn2 =  len( pair.nullspace() )
            assert pn1 == pn2, str(t) + " is not an eigenvector"
    except AssertionError as e:
        return False
    return True


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
        if 'Matrix' in str( type(x) ) :
            (nr,nc)  = shape(x);
            if nc == 1 :
                m = list( x );
                x = Matrix( m )
            res = x.T
            return res

        #if isinstance(x, sympy.MatrixBase):
        #    return x.T
        #else:
        #    return None


class mlog(sympy.Function):
    @classmethod
    def eval(cls, x):
        print(f"MLOG X={x} TYPE = {type(x)}")
        if 'Matrix' in str( type(x) ) :
            return x.applyfunc( log )
        else :
            return None

class mexp(sympy.Function):
    @classmethod
    def eval(cls, x):
        print(f"MEXP X={x} TYPE = {type(x)}")

        if 'Matrix' in str( type(x) ) :
            return x.applyfunc( exp )
        else :
            return None




class localconjugate(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return ( x.C ).doit()
        else:
            return None

class localinverse(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return x.inv()
        else:
            return None


class localadjoint(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return x.H
        else:
            return None

class thisshape(sympy.Function):
    @classmethod
    def eval(cls, x):
        if 'Matrix' in str( type(x) ) :
            (nr,nc)  = shape(x);
            return Matrix( [nr,nc] )



class rankof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if 'Matrix' in str( type(x) ) :
            (nr,nc)  = shape(x);
            if nc == 1 :
                m = list( x );
                x = Matrix( m )
            res = x.rank()
            return res



class oldrankof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            rank = x.rank()
            return sympy.sympify(rank)
        else:
            # logger.debug("MATREIX FOUND RANKOF %s", x)
            return None

class mylen(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            sp = list( shape( x ) )
            return sympy.sympify(sp[0])
        else:
            # logger.debug("MATREIX FOUND RANKOF %s", x)
            return None

class dim(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            sp = Matrix( list( shape( x ) ) )
            return sympy.sympify(sp)
        else:
            # logger.debug("MATREIX FOUND RANKOF %s", x)
            return None





class is_zero_matrix(sympy.Function):
    @classmethod
    def eval(cls, x):
        logger.error("X  = %s", x)
        x = N( x, chop=True )
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
    nargs = (1,2,3,4)

    @classmethod
    def eval(cls, *xx):
        x = xx[0];
        y = xx[1];
        x = N( x.doit(), p53 );
        y = N( y.doit(), p53 );
        scale = ( myabs(  x )  + myabs(y) )  
        if scale == 0 :
            scale = 1 ;
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            res = is_zero_matrix(  ( x - y ) / scale )
        else  :
            if myabs( x - y )  < COMPARISON_PRECISION   * scale :
                res = sympy.sympify("1")
            else:
                res = sympy.sympify("0")
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
        try  :
            if isinstance(x, sympy.MatrixBase):
                x =  N( x , chop=True );
                if x.is_diagonal():
                    return sympy.sympify("1")
                else:
                    return sympy.sympify("0")
        except :
            assert False, "Cannot check if its diagonal"


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



class iden(Function):  # {{{
    @classmethod
    def eval(cls, x):
        return x



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

matrix_defs = {
    "Array" : Array, 
    "abs": myabs,  # sympy.Function('norm')
    "Trace": Trace,
    "iden": iden,

    "Transpose": localtranspose,
    "localtranspose": localtranspose,

    "Conjugate": localconjugate,
    "localconjugate" : localconjugate,

    "Adjoint": localadjoint,
    "localadjoint" : localadjoint,

    "Inverse": localinverse,
    "localinverse" : localinverse,

    "AreEigenvaluesOf": AreEigenvaluesOf,
    "IsDiagonalizationOf": IsDiagonalizationOf,
    "IsHermitian": IsHermitian,
    "xhat" : Matrix([1,0,0]),
    "yhat" : Matrix([0,1,0]),
    "zhat" : Matrix([0,0,1]),
    "RankOf": rankof,
    "Rank": rankof,
    "IsUnitary": isunitary,
    "mul": mymul,
    "cross" : mycross , #  lambda x,y : Matrix(x).cross(Matrix(y)),
    "Gt": gt,
    "len" : mylen, 
    "dim" : dim,
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
    #"Partial": partial,
    #"partial": partial,
    #"Prime": Prime,
    "Not": logicalnot,
    "localNot": logicalnot,
    "IsEqual": eq,
    "eq" : eq,
    "IsNotEqual": neq,
    "diagonalpart": diagonalof,
    "DiagonalOf": diagonalof,
    "IsDiagonal": IsDiagonal,
    "IsDiagonalizable": IsDiagonalizable,
    "true": sympy.sympify("1"),
    "false": sympy.sympify("0"),
    "True": sympy.sympify("1"),
    "False": sympy.sympify("0"),
    "times": Times,
    "exp" : sympy.exp,
    "del2": del2,
    "sort": Sort,
    "Sort": Sort,
    "norm": Norm,
    "NullRank": nullrank,
    "Eigenvalues": Eigenvalues,
    "IsNullSpaceOf" : IsNullSpaceOf,
    "RotationMatrix" : RotationMatrix,
    "RotationArguments" : RotationArguments,
    "AreEigenvectorsOf" : AreEigenvectorsOf,
    "AreOrthogonal" : AreOrthogonal,
    "shape" : thisshape,
    "dimensions" : thisshape,
    "mlog" : mlog,
    "mexp" : mexp, 
    "matrixElements" : matrixElements,
    #"D" : Partial,
    "asin" : asin,
}
