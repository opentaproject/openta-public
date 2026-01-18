# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

# from sympy.abc import _clash1, _clash2, _clash
import re as resub
import time
from copy import deepcopy

from django.core.cache import cache as core_cache
from exercises.util import get_hash_from_string
from sympy import *
from sympy.abc import *
from sympy.matrices import *

from .functions import *
from .tokenify import *

# xtest = Function('myadd')(Symbol('ddachfedic'), Symbol('ieeebggdeb'), Symbol('xhat'), Symbol('zhat'), Function('grad')(Pow(Function('myadd')(Pow(Symbol('x'), Integer(2)), Pow(Symbol('y'), Integer(2)), Pow(Symbol('z'), Integer(2))), Rational(-1, 2))))
#
# matrix_sub =  {'xhat': Matrix([ [1], [0], [0]]), 'yhat': Matrix([ [0], [1], [0]]), 'zhat': Matrix([ [0], [0], [1]]),
#               'ddachfedic': Matrix([ [x/(x**2 + y**2 + z**2)**(3/2)], [y/(x**2 + y**2 + z**2)**(3/2)], [z/(x**2 + y**2 + z**2)**(3/2)]]),
#               'ieeebggdeb': Matrix([ [0], [1], [0]])}
# expr = xtest


def new_func_replace(expr, func_subs):
    name = str(expr.func)
    if func_subs.get(name):
        newargs = list(expr.args)
        oldargs = func_subs.get(name)["args"]
        new = func_subs.get(name)["value"]
        zip(oldargs, newargs)
        old = expr
        old.func
        arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(oldargs, newargs)}
        new = new.subs(arg_sub, evaluate=False)
        return new
    else:
        return expr


def traceprint(*exp):
    return ""


def pre(expr, newvarsubs, matrix_sub, func_subs, rep, dohash=True, level=0):
    """
    #
    # TEST WITH
    from sympy import *
    pre( sympify('1 + tanh(x)')
    #
    """
    # tbegin  = datetime.datetime.now()
    # print("PARSING expr = ", expr)
    spaces = " %s" % str(level)
    for i in range(0, level):
        spaces += "    "
    if expr is None:
        return expr
    exprin = resub.sub(r"\n", "", str(expr))
    traceprint("PRE IN: %s" % spaces, exprin)
    deepcopy(expr)
    time.time()
    # print("DOHASH = ", dohash)
    # if not hasattr( expr, 'is_Number') :
    #    print(f"ERROR {expr} {type(expr)} ")
    #    pass
    # else :
    if hasattr(expr, "is_Number") and expr.is_Number:
        traceprint("PREOUT: %s" % spaces, exprin, " -> ", resub.sub(r"\n", "", str(expr)))
        return expr
    varhash = get_hash_from_string(str(newvarsubs) + str(expr) + str(matrix_sub) + str(func_subs) + str(rep) + __file__)
    # if level == 0 :
    #    print("INCOMING LEVEL 0 ", expr )
    ret = core_cache.get(varhash)
    if dohash and ret is not None:
        return sympify(ret)
    if level == 0:
        expr = expr.replace(Add, Function("myadd"))
    name = "NONAME" if not hasattr(expr, "name") else getattr(expr, "name")
    newargs = None
    # print("PRE SPLIT 1 : ", ( time.time() - tbeg )*1000 )
    time.time()
    if hasattr(expr, "is_Function") and expr.is_Function:
        # print("FOUND FUNCTION ",  name, expr )
        if name == "Partial":
            sfree = list(expr.free_symbols)
            for sym in sfree:
                if newvarsubs.get(str(sym)):
                    raise NameError("Cannot diffrentiate with assigned symbol " + str(sym))
        if len(func_subs) > 0:
            expr = new_func_replace(expr, func_subs)
        newargs = [pre(item, newvarsubs, matrix_sub, func_subs, rep, dohash, level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
        # print("FUNC TIMING ", ( time.time() - tbeg_1 )*1000)
    elif hasattr(expr, "is_Symbol") and expr.is_Symbol:
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
        # expr = expr.subs(rep).doit()
        # print("SYMBOL TIMING ", ( time.time() - tbeg_1)*1000)
    else:
        # print("ORIG EXPR.FUNC", expr.func)
        # print("MATIX SUB = ", matrix_sub)
        if hasattr(expr, "func") and "Mul" in str(expr.func):
            expargs = list(expr._args)
            n = 0
            for arg in expargs:
                n = n + 1 if (str(newvarsubs.get(str(arg), "NOT FOUND")) in matrix_sub) else n
            if n > 1:
                raise NameError("Use mul(A,B) for matrix multiply in " + str(expr))
            # print(dir( expr) )
            # for key in dir(expr) :
            #    print(key, getattr( expr,key ) )
        if hasattr(expr, "args"):
            newargs = [pre(item, newvarsubs, matrix_sub, func_subs, rep, dohash, level + 1) for item in expr.args]
            expr = expr.__class__(*newargs)
        # print("ELSE TIMING ", ( time.time() - tbeg_1)*1000)
        # print("BECAME EXPR.FUNC", expr.func )
    # if level == 0 :
    #    #print("OUTGOING LEVEL 0 expr = ", expr )
    # print("PRE SPLIT 2 : ", ( time.time() - tbeg )*1000 )
    # expr = expr.subs(rep,evaluate=False)
    expr = expr.replace(Function("mul"), MatMul).doit()
    expr = expr.subs([(Function("myadd"), Function("carefuladd"))]).doit()
    repadd = [(Function(key), val) for key, val in add_scope.items()]
    expr = expr.subs(repadd).doit()
    # expr = expr.replace(Function('myadd'), Add).doit()
    core_cache.set(varhash, srepr(expr), 60 * 60)
    # print("PRE SPLIT 3 : ", ( time.time() - tbeg )*1000 )
    # print("TIME IN PRE : ", ( time.time() - tbeg )*1000 , " FOR ",  expr_orig)
    traceprint("PREOUT: %s" % spaces, exprin, " -> ", resub.sub(r"\n", "", str(expr)))
    return expr
