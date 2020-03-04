from sympy import *
from sympy.abc import *
from sympy.matrices import *
from copy import deepcopy
from exercises.util import get_hash_from_string
from django.conf import settings
from django.core.cache import cache as core_cache
import time

# from sympy.abc import _clash1, _clash2, _clash
import re as resub
from exercises.util import get_hash_from_string

from .string_formatting import (
    absify,
    insert_implicit_multiply,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
)
from .functions import *


# xtest = Function('myadd')(Symbol('ddachfedic'), Symbol('ieeebggdeb'), Symbol('xhat'), Symbol('zhat'), Function('grad')(Pow(Function('myadd')(Pow(Symbol('x'), Integer(2)), Pow(Symbol('y'), Integer(2)), Pow(Symbol('z'), Integer(2))), Rational(-1, 2))))
#
# matrix_sub =  {'xhat': Matrix([ [1], [0], [0]]), 'yhat': Matrix([ [0], [1], [0]]), 'zhat': Matrix([ [0], [0], [1]]),
#               'ddachfedic': Matrix([ [x/(x**2 + y**2 + z**2)**(3/2)], [y/(x**2 + y**2 + z**2)**(3/2)], [z/(x**2 + y**2 + z**2)**(3/2)]]),
#               'ieeebggdeb': Matrix([ [0], [1], [0]])}
# expr = xtest


def dematrixify(sexpr, varsubs):
    matrix_subs = {}
    matrix_subs['xhat'] = Matrix([1, 0, 0])
    matrix_subs['yhat'] = Matrix([0, 1, 0])
    matrix_subs['zhat'] = Matrix([0, 0, 1])
    newvarsubs = {}
    vsubs = []
    for key, val in varsubs.items():
        (newval, vsub) = tokenify(str(val))
        newvarsubs[key] = sympify(newval)
        for item in vsub:
            (n, m) = item['value'].shape
            matrix_subs[item['name']] = item['value']
    (xtest, vsubs) = tokenify(sexpr)
    for item in vsubs:
        (n, m) = item['value'].shape
        matrix_subs[item['name']] = item['value']
    return (xtest, newvarsubs, matrix_subs)


def tokenify(xtest, vsubs=[]):
    orig = xtest ;
    try:
        nit = 0
        vsubs = []
        while True:
            vsub = {}
            previous = xtest
            p = resub.compile(r'Matrix')
            allm = list(p.finditer(xtest))
            if len(allm) == 0:
                break
            m = allm[0]
            (ibeg, ileft) = m.span()
            iright = index_of_matching_right_paren(ileft, xtest)
            head = xtest[0:ibeg]
            body = xtest[ibeg:iright]
            tail = xtest[iright:]
            bodyhash = get_hash_from_string(body)
            vsub['name'] = bodyhash
            vsub['value'] = sympify(body)
            xtest = head + '(' + bodyhash + ')' + tail
            vsubs = vsubs + [vsub]
            nit = nit + 1
    except:
        print("FAILED WITH ", orig )
        raise TypeError("FAILED WITH " + orig)
    return (xtest, vsubs)


def new_func_replace(expr, func_subs):
    name = str(expr.func)
    if func_subs.get(name):
        newargs = list(expr.args)
        oldargs = func_subs.get(name)['args']
        new = func_subs.get(name)['value']
        subrule = zip(oldargs, newargs)
        old = expr
        oldfunc = old.func
        arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(oldargs, newargs)}
        new = new.subs(arg_sub)
        return new
    else:
        return expr


def pre(expr, newvarsubs, matrix_sub, func_subs, rep, dohash=True, level=0):
    '''
     #
     # TEST WITH 
     from sympy import *
     pre( sympify('1 + tanh(x)')
     #
     '''
    # tbegin  = datetime.datetime.now()
    # print("PARSING expr = ", expr)
    print("DOHASH = ", dohash)
    if expr.is_Number:
        return expr
    varhash = get_hash_from_string(str(newvarsubs) + str(expr) + str(matrix_sub) + str(func_subs) + str(rep) )
    ret = core_cache.get(varhash)
    if dohash and ret is not None:
        return sympify(ret)
    if level == 0:
        expr = expr.replace(Add, Function('myadd'))
    name = 'NONAME' if not hasattr(expr, 'name') else getattr(expr, 'name')
    newargs = None
    if expr.is_Function:
        # print("FOUND FUNCTION ")
        if len(func_subs) > 0:
            expr = new_func_replace(expr, func_subs)
        newargs = [
            pre(item, newvarsubs, matrix_sub, func_subs, rep, dohash, level + 1)
            for item in expr.args
        ]
        expr = expr.__class__(*newargs)
    elif expr.is_Symbol:
        # print("NEWVARSUBS GETS CALLED")
        while True:
            prev = expr
            expr = expr.subs(newvarsubs).doit()
            expr = expr.subs(matrix_sub).doit()
            if prev == expr:
                break
        # if not expr.is_Symbol :
        #    expr = pre( expr, newvarsubs, matrix_sub, func_subs,rep, level + 1 )
        # print("AFTER PRE ", expr )
        expr = expr.subs(rep).doit()
    elif expr.is_Atom:
        # print("FOUND ATOM")
        expr = expr
    else:
        print("ORIG EXPR.FUNC", expr.func)
        print("MATIX SUB = ", matrix_sub)
        if 'Mul' in str( expr.func  ) :
            expargs = list( expr._args )
            n = 0
            for arg in expargs:
                n = n + 1 if ( str( newvarsubs.get(str(arg),'NOT FOUND')  ) in matrix_sub  ) else n
            if n > 1 :
                raise NameError( "Matrix multiplication must be explicit: violated in " + str(expr)  )
            #print(dir( expr) )
            #for key in dir(expr) :
            #    print(key, getattr( expr,key ) )
        newargs = [
            pre(item, newvarsubs, matrix_sub, func_subs, rep, dohash, level + 1)
            for item in expr.args
        ]
        expr = expr.__class__(*newargs)
        print("BECAME EXPR.FUNC", expr.func )
    expr = expr.subs(rep)
    core_cache.set(varhash, srepr(expr), 60 * 60)
    return expr

