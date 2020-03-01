from sympy import *
from sympy.matrices import *
from exercises.util import get_hash_from_string
from copy import deepcopy

# from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import re as resub
import random
import itertools
from sympy.core import S
from .unithelpers import baseunits
from sympy.core.function import AppliedUndef
from exercises.util import index_of_matching_right_paren
import time

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
from .functions import *
from sympy.matrices import Matrix
from .descend import dematrixify, tokenify, new_func_replace, pre

def replace_funcs_once(sexpr, funcsubs, subrule):
    for sub in funcsubs:
        func_def = sympy.Function(sub['name'])
        args = (sub['args']).lstrip('[').rstrip(']')
        funcdefstring = sub['name'] + '(' + args + ')'
        func_def = sympy.sympify(funcdefstring)
        func_body = sympy.sympify(sub['value'])
        sexpr = func_sub(sexpr, func_def, func_body, subrule)
    return sexpr


def replace_funcs(sexpr, funcsubs, subrule):
    # print("INCOMING = ", sexpr)
    while True:
        prev = sexpr
        sexpr = replace_funcs_once(sexpr, funcsubs, subrule)
        if sexpr == prev:
            # print("OUTGOING = ", sexpr)
            return sexpr



def func_sub_single(expr, func_def, func_body, subrule):
    # Find the expression to be replaced, return if not there
    # print("DO FUNC_SUB_SINGLE")
    funcatoms = expr.atoms(AppliedUndef)
    if len(funcatoms) == 0:
        return expr
    for unknown_func in funcatoms:
        # print("REPLACING ", unknown_func , " IN ", expr )
        if unknown_func.func == func_def.func:
            replacing_func = unknown_func
            break
    else:
        # print("RETURNING ", expr)
        return expr.subs(subrule).doit()
    arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(func_def.args, replacing_func.args)}
    func_body_subst = func_body.subs(arg_sub)
    ret = expr.subs(replacing_func, func_body_subst)
    # ret = sympify( str(ret), myscope )
    ret = ret.subs(subrule).doit()
    return ret


def func_sub(expr, func_def, func_body, myscope):
    # print("FUNCSUB", expr)
    if any(func_def.func == body_func.func for body_func in func_body.atoms(AppliedUndef)):
        raise ValueError('Function may not be recursively defined')

    while True:
        prev = expr
        expr = func_sub_single(expr, func_def, func_body, myscope)
        if prev == expr:
            return expr


def tokenify(xtest,vsubs=[]):
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
            vsub['name'] = bodyhash ;
            vsub['value'] = sympify(body);
            xtest = head + '(' + bodyhash + ')' + tail
            vsubs = vsubs + [vsub]
            nit = nit + 1
    except:
        print("FAILED WITH ", xtest)
        raise TypeError("FAILED WITH " + xtest)
    return (xtest, vsubs)


class iden(sympy.Function):
    @classmethod
    def eval(cls, x):
        return x

def dematrixify( sexpr,varsubs) :
    matrix_subs = {}
    matrix_subs['xhat'] = Matrix([1,0,0])
    matrix_subs['yhat'] = Matrix([0,1,0])
    matrix_subs['zhat'] = Matrix([0,0,1])
    newvarsubs = {}
    vsubs = []
    for key,val in varsubs.items() :
        (newval,vsub) = tokenify(str(val) )
        newvarsubs[key] = sympify( newval )
        for item in vsub:
            (n,m) = item['value'].shape
            matrix_subs[ item['name']] =  item['value']  
    (xtest, vsubs) = tokenify(sexpr)
    for item in vsubs:
        (n,m) = item['value'].shape
        matrix_subs[ item['name'] ] =  item['value']  
    return (xtest, newvarsubs, matrix_subs)


def expr_are_equal( ex1, ex2 ):
    ex1 = sympy.sympify(ex1)
    ex2 = sympy.sympify(ex2)
    try: 
        print("COMPARE ", srepr(ex1), srepr(ex2) )
        if ex1.is_Matrix and ex2.is_Matrix :
            return sympy.simplify( ex1 - ex2 ).norm() == 0 
        elif ex1.is_Matrix :
            if ex2 == sympy.sympify('0') and ex1.norm() == 0 :
                return True
            else:
                return False
        elif ex2.is_Matrix :
            if ex1 == sympy.sympify('0') and ex2.norm() == 0 :
                return True
            else:
                return False
        else :
            diff1 = sympy.simplify( ex1 - ex2 )
            return diff1.is_zero 
    except Exception as e :
        print("ERROR WAS " + str(e) )
        return False 
        

def sympify_with_custom(expression, varsubs, funcsubs={}, source='UNKNOWN'):
    """
    Convert asciimath expression into sympy using extra context
    Args:
        expression: asciimath
        varsubs: { string(name): substitution, ... }

    Returns:
        Sympy expression
    """
    scope = openta_scope
    myscope = deepcopy( scope )
    subrule = []
    for key, val in myscope.items():
        if 'Function' in str(type(val)):
            subrule = subrule + [(Function(key), val)]
        else:
            subrule = subrule + [(Symbol(key), val)]

    if source == "PARSE_SAMPLE_VARIABLES":
        scope.update({'sample': sample})
    scope.update(ns)
    scope.update(varsubs)
    scope_symbolic = {
        'x': sympy.sympify('x'),
        'y': sympy.sympify('y'),
        'z': sympy.sympify('z'),
        't': sympy.sympify('t'),
        'xhat': sympy.sympify(Matrix([1, 0, 0])),
        'yhat': sympy.sympify(Matrix([0, 1, 0])),
        'zhat': sympy.sympify(Matrix([0, 0, 1])),
    }
    try :
        tbeg = time.time() 
        sexpr = ascii_to_sympy(declash(expression), {})
        (xtest,newvarsubs, matrix_subs ) = dematrixify( sexpr , varsubs)
        print("XTEST IS ", xtest )
        #for key,val in newvarsubs.items() :
        #    print("NEWVARSUBS KEY = ", srepr(key) )
        #    print("NEWVARSUBS VALUE = ", srepr(val) )
        print("newvarsubs = ", newvarsubs)
        print("matrix_subs = ", matrix_subs)
        func_subs = {  sub['name'] : {
                'args' :  [  Symbol(arg) for arg  in  sub['args'].lstrip('[').rstrip(']').split(',') ] , 
                'value' : sympify( sub['value']  )  }  for sub in funcsubs}
        print("func_subs = ", func_subs)
        xtest = sympify(xtest,ns).replace(Add,Function('myadd') )
        print("xtest = ", srepr( xtest ) )
        new1 = pre(xtest,newvarsubs, matrix_subs,func_subs,myscope) 
        print("NEW1 = ", new1 )
        rep = [ (Function(key), val ) for key,val in myscope.items() ]
        new2 = new1.subs(rep)
        print("NEW2 = ", new2 )
        new3 = new2.replace(Function('myadd'), Add).doit() 
        print("NEW3 = ", new3 )
        new4 = simplify( new3 )
        print("NEW4 = ", new4)
        tend = time.time()
        print("TIME SPENT IN SYMPIFY WITH CUSTOM = ", (tend - tbeg) * 1000 , " MILLISECONDS")
    except :
        pass
    print("NEW4 AGAIN = ", new4 ) 
    #print("XTEST = ", xtest )
    #abc = {
    #    'x': sympy.sympify('x'),
    #    'y': sympy.sympify('y'),
    #    'z': sympy.sympify('z'),
    #    't': sympy.sympify('t'),
    #    }
 
    #newscope.update( abc )
    #test1 = sympify( xtest, ns )
    #print("0 TESTING = ", test1 )
    #test2 = test1.subs(newvarsubs)
    #test2 = test2.replace(Add, Function('myadd') )
    #print("1 TEST2 = ", test2 )
    #print("1 TEST2 = ", srepr( test2 ) )
    #sxtest = sympify(xtest, newscope)
    #print("1 SXTEST = ", srepr( sxtest) )
    #sxtest = sxtest.subs(newvarsubs)
    #print("2 SXTEST = ", srepr( sxtest ) )
    #sxtest = sxtest.subs(matrix_subs)
    #print("3 SXTEST = ", sxtest.replace(Function('matmul'), MatMul ).doit() )
    #rep = []
    #for key,val in myscope.items()  :
    #    rep = rep + [( Function(key), val )]
    #print("4 SXTEST = ", sxtest.subs( rep  ).doit() )
    #print("FUNCSUBS = ", funcsubs )
    #try :
    #    restored = sxtest.subs(matrix_subs).doit() # .replace(Function('vq'),sample) 
    #    #print("RESTORED = ", restored)
    #    #print("matrix_subs = ",  matrix_subs )
    #except :
    #    print("xtest = ", xtest )
    #    print("matrix_subs = ", matrix_subs )
    #    print("sxtest = ", sxtest )
    #    raise TypeError("expr  = ", sexpr )
    if False  :
        location = 'A'
        if resub.search(r'[xyz]hat', sexpr) or 'Matrix' in sexpr:
            location += 'B'
            scope.update(scope_symbolic)
            location += 'C'
            sexpr = sympy.sympify(sexpr, scope)
            location += 'D'
        else:
            location += 'E'
            sexpr = sympy.sympify(sexpr, scope)
            location += 'F'
        if len(funcsubs) > 0:
            location += 'G'
            sexpr = replace_funcs(sexpr, funcsubs, subrule)
            location += 'H'
        location += 'I'
        sexpr = sexpr.subs(scope_symbolic)
        location += 'J'
        sexpr = sexpr.subs(varsubs)
        location += 'K'
        sexpr = sexpr.doit()
        location += 'L'
    return  new4



#'''
# from exercises.questiontypes.dev_linear_algebra.parsers import *
# funcsubs = [{'name': 'f', 'args': '[q]', 'value': '3 * q'}, {'name': 'g', 'args': '[x,y]', 'value': 'G(x)'}]
# expression = '(f(yhat) )-( yhat)'
# expression = 'f(q)'
# sexpr = sympify( expression )
# sympify_with_custom(expression,{}, funcsubs)
#'''
