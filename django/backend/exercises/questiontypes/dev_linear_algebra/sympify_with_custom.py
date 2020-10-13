from sympy import *
from sympy.matrices.matrices import  ShapeError
import hashlib
from sympy.matrices import *
from django.core.cache import cache as core_cache
from exercises.util import get_hash_from_string
from django.conf import settings
from copy import deepcopy

# from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
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
from .string_formatting import (
    ascii_to_sympy,
    matrixify,
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
    while True:
        prev = sexpr
        sexpr = replace_funcs_once(sexpr, funcsubs, subrule)
        if sexpr == prev:
            return sexpr


def func_sub_single(expr, func_def, func_body, subrule):
    # Find the expression to be replaced, return if not there
    # #print("DO FUNC_SUB_SINGLE")
    funcatoms = expr.atoms(AppliedUndef)
    if len(funcatoms) == 0:
        return expr
    for unknown_func in funcatoms:
        # #print("REPLACING ", unknown_func , " IN ", expr )
        if unknown_func.func == func_def.func:
            replacing_func = unknown_func
            break
    else:
        # #print("RETURNING ", expr)
        return expr
        # return expr.subs(subrule).doit()
    arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(func_def.args, replacing_func.args)}
    func_body_subst = func_body.subs(arg_sub)
    ret = expr.subs(replacing_func, func_body_subst)
    # ret = sympify( str(ret), myscope )
    # ret = ret.subs(subrule).doit()
    return ret


def func_sub(expr, func_def, func_body, myscope):
    # #print("FUNCSUB", expr)
    if any(func_def.func == body_func.func for body_func in func_body.atoms(AppliedUndef)):
        raise ValueError('Function may not be recursively defined')

    while True:
        prev = expr
        expr = func_sub_single(expr, func_def, func_body, myscope)
        if prev == expr:
            return expr


def tokenify(xtest, vsubs=[]):
    orig = xtest
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
        #print("FAILED WITH ", xtest)
        raise TypeError("Failed to parse")
    return (xtest, vsubs)


class iden(sympy.Function):
    @classmethod
    def eval(cls, x):
        return x


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


def expr_are_equal(ex1, ex2):
    ex1 = sympy.sympify(ex1)
    ex2 = sympy.sympify(ex2)
    try:
        # #print("COMPARE ", srepr(ex1), srepr(ex2) )
        if ex1.is_Matrix and ex2.is_Matrix:
            return sympy.simplify(ex1 - ex2).norm() == 0
        elif ex1.is_Matrix:
            if ex2 == sympy.sympify('0') and ex1.norm() == 0:
                return True
            else:
                return False
        elif ex2.is_Matrix:
            if ex1 == sympy.sympify('0') and ex2.norm() == 0:
                return True
            else:
                return False
        else:
            diff1 = sympy.simplify(ex1 - ex2)
            return diff1.is_zero
    except Exception as e:
        return False


class ncarefuladd(sympy.Function):
    nargs = (0, 1, 2, 3, 4, 5, 6, 7)

    @classmethod
    def eval(cls, *args):
        rank = 1
        for arg in args:
            if hasattr(arg, 'shape'):
                if arg.is_square:
                    rank = shape[0]
        if not rank == 1:
            newargs = []
            for arg in args:
                if not hasattr(arg, 'shape'):
                    newargs = newargs + [eye(shape) * arg]
                else:
                    newargs = newargs + [arg]
            return Add(*newargs)
        else:
            return Add(*args)


def sympify_with_custom(expression, varsubs, funcsubs={}, source='UNKNOWN'):
    #print("SOURCE = ", source )
    tbeg = time.time()
    expression_orig = expression
    varhash = get_hash_from_string(expression + str(varsubs) + str(funcsubs) + source   + __file__ )
    #print( varhash, " SYMPIFY_WITH_CUSTOM IN", expression)
    docache = settings.DO_CACHE
    ret =  core_cache.get(varhash) 
    try :
        if not ret == None and docache :
            ret = sympy.sympify( ret  )
            if isinstance(ret, sympy.Float ):
                if abs( ret - 1 ) < 1.e-12 :
                    ret = sympy.sympify( 1.0 )
                elif abs( ret ) < 1.e-12 :
                    ret = sympy.sympify( 0.0 )
        #print( varhash, " RET = ", ret )
            return ret
    except: 
        pass
    tbeg = time.time()
    should_be_end = index_of_matching_right_paren(0, '(' + expression + ')')
    assert should_be_end == len(expression) + 2, (
        "MATCHING PAREN ERROR IN  SYMPIFY WITH CUSTOM " + expression
    )
    #print("     TIME A1 %s" , 1000 * ( time.time() - tbeg) )
    expression = ascii_to_sympy( declash( expression) )
    tbeg = time.time()
    scope = openta_scope
    scope.update( unitbaseunits )
    myscope = deepcopy(scope)
    subrule = []
    for key, val in myscope.items():
        if 'Function' in str(type(val)):
            subrule = subrule + [(Function(key), val)]
        else:
            subrule = subrule + [(Symbol(key), val)]

    #if source == "PARSE_SAMPLE_VARIABLES":
    #    scope.update({'sample': sample})
    #print("     TIME A2 %s" , 1000 * ( time.time() - tbeg) )
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
    rep = [(Function(key), val) for key, val in myscope.items()]
    repadd = [(Function(key), val) for key, val in add_scope.items()]
    sexpr = ascii_to_sympy(expression, {})
    new = sexpr
    (xtest, newvarsubs, matrix_subs) = dematrixify(sexpr, varsubs)
    new = xtest
    #print("     TIME A3 %s" , 1000 * ( time.time() -  tbeg) )
    func_subs = {
        sub['name']: {
            'args': [Symbol(arg) for arg in sub['args'].lstrip('[').rstrip(']').split(',')],
            'value': sympify(sub['value']),
        }
        for sub in funcsubs
    }
    #print("     TIME A4 %s" , 1000 * ( time.time() -  tbeg) )
    xtest = sympify(xtest, ns, evaluate=False).subs(ns).doit().replace(Add, Function('myadd'))
    new = xtest
    #print("     TIME A5 %s" , 1000 * ( time.time() -  tbeg) )
    #print("XTEST = ", xtest)
    #print("NEWVARSUBS = ", newvarsubs)
    #print("MATRIXSUBS = ", matrix_subs )
    #print("REP = ", rep )
    st = resub.sub(r'\d+','',str(xtest)  )
    atoms1 = set( resub.findall(r'\w+',st) ) 
    atoms2 = set( newvarsubs.keys() )
    atoms3 = set( matrix_subs.keys() )
    atoms4 = set( func_subs.keys() )
    atoms = atoms4.union( atoms1.union(atoms2.union(atoms3) )  )
    rep_optimized = list( filter( lambda item : str( item[0] ) in atoms , rep) )
    #rep_optimized = rep
    #print("REPNEW = ", rep_optimized )
    #try :
    new = pre(xtest, newvarsubs, matrix_subs, func_subs, rep_optimized, docache)
    #except Exception as e :
    #    print("FAILED EXPRESSION = ", expression)
    #    print("rep_optimeze = ", str( rep_optimized) )
    #    print("FAILED IN PRE FOR xtest = ", str( xtest ) )
    #    print("EXCPTION RAISED = ", type(e), str(e) )
    #    print("TRACEBACK ", traceback.format_exc() )  
    #    return xtest
    #print("     TIME A6 %s" , 1000 * ( time.time() -  tbeg) )
    #new  = N(new)
    #st = resub.sub(r'\d+','',str(new)  )
    #atoms = list( set( resub.findall(r'\w+',st) ) ) 
    #print("ATOMES = ",  atoms)
    #print("     TIME A7 %s" , 1000 * ( time.time() -  tbeg) )
    #print("NEW = ", new )
    #print("REP = ", rep )
    #print("REPNEW = ", rep_optimized )
    new = new.subs(rep_optimized).doit()
    tend = time.time()
    #print("     TIME A8 %s" , 1000 * ( time.time() - tbeg) )
    if docache:
        #print("IN SYMPIFY WITH CUSTOM CACHE ", new )
        try :
            core_cache.set(varhash,  str(new), 60 * 60)
        except Exception as e :
            print("COULD NOT CACHE ", type(e) , str(e) ) 
    #print( varhash ,  " SYMPIFY_WITH_CUSTOM OUT", new )
    return new
