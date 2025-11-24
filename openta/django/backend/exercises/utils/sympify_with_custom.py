# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os
from pickle import PicklingError

from sympy.parsing.sympy_parser import parse_expr

"""
from sympy.parsing.sympy_parser import standard_transformations,\
    implicit_multiplication_application
transformations = (standard_transformations + (implicit_multiplication_application,))
ex = parse_expr(' 3^1  *  cos( A * sin(B) ) ( A * B  ) * A * B ', evaluate=False, transformations=transformations)

"""

from sympy import symbols, simplify;
from sympy.physics.quantum.operatorordering import normal_ordered_form as no
from sympy.physics.quantum.boson import BosonOp;
from sympy.physics.quantum import Dagger, Commutator


import re as resub
import time
from copy import deepcopy
from exercises.utils.print_utils import dprint
from exercises.util import get_hash_from_string, index_of_matching_right_paren
from sympy import *
from sympy.core.function import AppliedUndef

# from sympy.abc import _clash1, _clash2, _clash
from sympy.matrices import *
from sympy.matrices import Matrix

from django.conf import settings
from django.core.cache import cache as core_cache

from .descend import dematrixify, pre
from .functions import *
from .string_formatting import ascii_to_sympy, declash
from .unithelpers import *


def replace_funcs_once(sexpr, funcsubs, subrule):
    for sub in funcsubs:
        func_def = sympy.Function(sub["name"])
        args = (sub["args"]).lstrip("[").rstrip("]")
        funcdefstring = sub["name"] + "(" + args + ")"
        func_def = sympy.sympify(funcdefstring)
        func_body = sympy.sympify(sub["value"])
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
        raise ValueError("Function may not be recursively defined")

    while True:
        prev = expr
        expr = func_sub_single(expr, func_def, func_body, myscope)
        if prev == expr:
            return expr


class iden(sympy.Function):
    @classmethod
    def eval(cls, x):
        return x


def expr_are_equal(ex1, ex2):
    ex1 = sympy.sympify(ex1)
    ex2 = sympy.sympify(ex2)
    try:
        # #print("COMPARE ", srepr(ex1), srepr(ex2) )
        if ex1.is_Matrix and ex2.is_Matrix:
            return sympy.simplify(ex1 - ex2).norm() == 0
        elif ex1.is_Matrix:
            if ex2 == sympy.sympify("0") and ex1.norm() == 0:
                return True
            else:
                return False
        elif ex2.is_Matrix:
            if ex1 == sympy.sympify("0") and ex2.norm() == 0:
                return True
            else:
                return False
        else:
            diff1 = sympy.simplify(ex1 - ex2)
            return diff1.is_zero
    except Exception:
        return False


class ncarefuladd(sympy.Function):
    @classmethod
    def eval(cls, *args):
        rank = 1
        for arg in args:
            if hasattr(arg, "shape"):
                if arg.is_square:
                    rank = shape[0]
        if not rank == 1:
            newargs = []
            for arg in args:
                if not hasattr(arg, "shape"):
                    newargs = newargs + [eye(shape) * arg]
                else:
                    newargs = newargs + [arg]
            return Add(*newargs)
        else:
            return Add(*args)


def sympify_with_custom(expression, varsubs, funcsubs={}, extradefs={}, source="UNKNOWN"):
    #print(f"SYMPIFY WITH CUSTOM EXRESSION = {expression}")
    orig_expression = expression;
    expression = resub.sub(r"([^a-zA-Z])abs\(", r"\1norm(", expression)
    expression = resub.sub(r"mul\(", "Mul(", expression)
    #print(f"A0 EXPRESSIOn = {expression}")
    original_expression = expression
    tbeg = time.time()
    #print(f"EXTRADEFS = {extradefs}")
    varhash = get_hash_from_string(expression + str(extradefs) + str(funcsubs) + source + __file__)
    # print( varhash, " SYMPIFY_WITH_CUSTOM IN", expression)
    docache = settings.DO_CACHE
    ret = core_cache.get(varhash)
    dprint(f"    ELAPSED FIRST IN CUSTOM { int( (time.time() - tbeg )*1000 ) }")

    try:
        if not ret == None and docache:
            # print(f"GRAB {varhash} from cache")
            # print(f"RET = { type(ret) } {ret}")
            if isinstance(ret, str):
                ret = sympy.sympify(ret)
            if isinstance(ret, sympy.Float):
                if abs(ret - 1) < 1.0e-12:
                    ret = sympy.sympify(1.0)
                elif abs(ret) < 1.0e-12:
                    ret = sympy.sympify(0.0)
            dprint(f"    CACHE ELAPSED IN CUSTOM { (time.time() - tbeg )*1000 }")
            return ret
    except Exception as e:
        logger.error(f"ERROR: SYMPIFY WITH CUSTOM ERROR E9155 {type(e).__name__} {expression}")
    time.time()
    should_be_end = index_of_matching_right_paren(0, "(" + expression + ")")
    assert should_be_end == len(expression) + 2, "MATCHING PAREN ERROR IN  SYMPIFY WITH CUSTOM " + expression
    expression = declash(expression);
    #print(f"A1 EXPRESSIOn = {expression}")
    expression = ascii_to_sympy(declash(expression))
    #print(f"A2 EXPRESSION_NOW IS {expression}")
    time.time()
    scope = openta_scope
    # print(f"EXTRADEFS = {extradefs} TYPE = { type( extradefs) } ")
    if "customfunctions" in extradefs:
        exerciseassetpath = extradefs["exerciseassetpath"]
        localfunctionfile = extradefs["customfunctions"]
        fp = open(os.path.join(exerciseassetpath, localfunctionfile))
        evalstring = fp.read()
        fp.close()
        globaldict = {"sympy": sympy, "numpy": numpy,"quantum" :sympy.physics.quantum, sympy.physics.quantum.boson : "boson" }
        localdict = locals()
        exec(evalstring, globaldict, localdict)
    scope.update(unitbaseunits)
    myscope = deepcopy(scope)
    subrule = []
    for key, val in myscope.items():
        if "Function" in str(type(val)):
            subrule = subrule + [(Function(key), val)]
        else:
            subrule = subrule + [(Symbol(key, commutative=False), val)]

    # if source == "PARSE_SAMPLE_VARIABLES":
    #    scope.update({'sample': sample})
    # print("     TIME A2 %s" , 1000 * ( time.time() - tbeg) )
    scope.update(ns)
    scope.update(varsubs)
    scope_symbolic = {
        "x": sympy.sympify("x"),
        "y": sympy.sympify("y"),
        "z": sympy.sympify("z"),
        "t": sympy.sympify("t"),
        "xhat": sympy.sympify(Matrix([1, 0, 0])),
        "yhat": sympy.sympify(Matrix([0, 1, 0])),
        "zhat": sympy.sympify(Matrix([0, 0, 1])),
    }
    scope_quantum = {
            "BosonOp" : sympy.physics.quantum.boson.BosonOp
            }
            
    scope.update(scope_symbolic)
    scope.update(scope_quantum)
    rep = [(Function(key), val) for key, val in myscope.items()]
    # print(f"REP = {rep}")
    sexpr = ascii_to_sympy(expression, {})
    #print(f"A3 sexpr = {sexpr}")
    new = sexpr
    (xtest, newvarsubs, matrix_subs) = dematrixify(sexpr, varsubs)
    new = xtest
    # print("     TIME A3 %s" , 1000 * ( time.time() -  tbeg) )
    # print(f"FUNCSUBS = {funcsubs}")
    allvars = []
    for sub in funcsubs:
        allvars = allvars + sub["args"].lstrip("[").rstrip("]").split(",")
    # print(f"ALLVARS = {allvars}")
    failed = []
    allvars = list(set(allvars) - set(["x", "y", "z", "t"]))
    for a in allvars:
        try:
            eval(a)
            failed = failed + [a]
        except:
            pass
    if failed:
        raise NameError(f"Variables {failed}  are reserved. Use another dummy variable. ")
    try:
        func_subs = {
            sub["name"]: {
                "args": [Symbol(arg) for arg in sub["args"].lstrip("[").rstrip("]").split(",")],
                "value": sympify(sub["value"]),
            }
            for sub in funcsubs
        }
    except Exception as e:
        logger.error(f" ERROR {type(e).__name__} {str(e)} ")
        raise NameError(f"ERROR {str(e)}")
    # print(f"FUNCSUBS func_subs = {func_subs}")
    # print("     TIME A4 %s" , 1000 * ( time.time() -  tbeg) )
    try:
        sc = deepcopy(varsubs)
        matrices = [
            k for k, v in sc.items() if (isinstance(v, sympy.Matrix) or isinstance(v, sympy.ImmutableDenseMatrix))
        ]
        xtest = resub.sub(r"mul\(", "Mul(", xtest)
        #print(f"XTEST0 = {xtest} SREPR={srepr(xtest)}" )
        sc.update(matrix_subs)
        xtt = parse_expr(xtest, sc, evaluate=False)
        #print(f"XTT = {xtt} SREPR={srepr(xtt)}" )
        xtt = xtt.subs(sc)
        xtest = xtt.subs(ns).doit()  # .replace(Add, Function("myadd"))
    except Exception as e:
        # print(f" NS = {ns}")
        # print(f" XTEST = {xtest}")
        logger.error(f"Error E0248 {type(e).__name__} in {original_expression}")
    new = xtest
    #print(f"NEW0={new}")
    # print("     TIME A5 %s" , 1000 * ( time.time() -  tbeg) )
    # print("XTEST = ", xtest)
    # print("NEWVARSUBS = ", newvarsubs)
    # print("MATRIXSUBS = ", matrix_subs )
    # print("REP = ", rep )
    # print("CHECKING XTEST = ", str( xtest) )
    # print("SCOPE = ", scope.keys() )
    # print("XTEST = ", str( xtest) )
    st = str(xtest)
    atoms0 = set(["partial", "del2", "dot"])
    atoms1 = set(resub.findall(r"[A-Za-z][A-Za-z0-9]*", expression))
    atoms2 = set(newvarsubs.keys())
    atoms3 = set(matrix_subs.keys())
    atoms4 = set(func_subs.keys())
    atoms = atoms0.union(atoms1.union(atoms2.union(atoms3.union(atoms4))))
    #print("ATOMS = ", atoms)
    #print(f"FUNCSUBS = {func_subs}")
    rep_optimized = list(filter(lambda item: str(item[0]) in atoms, rep))
    # print("REP = ", rep )
    # print("OPTIMZIED = ", rep_optimized )
    # print("REPNEW = ", rep_optimized )
    try:
        new = pre(xtest, newvarsubs, matrix_subs, func_subs, rep_optimized, docache)
    except Exception:
        # print("FAILED EXPRESSION = ", expression)
        # print("rep_optimeze = ", str( rep_optimized) )
        # print("FAILED IN PRE FOR xtest = ", str( xtest ) )
        # print("EXCPTION RAISED = ", type(e), str(e) )
        # print(f"RETURN2 FROM CUSTOM")
        #print(f"    EXCEPTION ELAPSED IN CUSTOM { (time.time() - tbeg )*1000 }")
        return sympy.sympify(xtest)
    # print("     TIME A6 %s" , 1000 * ( time.time() -  tbeg) )
    # new  = N(new)
    # st = resub.sub(r'\d+','',str(new)  )
    # atoms = list( set( resub.findall(r'\w+',st) ) )
    # print("ATOMES = ",  atoms)
    # print("     TIME A7 %s" , 1000 * ( time.time() -  tbeg) )
    # print("NEW = ", new )
    # print("REP = ", rep )
    # print("REPNEW = ", rep_optimized )
    new = new.subs(rep_optimized).doit()
    #print(f"NEW3={new}")
    time.time()
    # print("     TIME A8 %s" , 1000 * ( time.time() - tbeg) )
    if docache:
        # print("IN SYMPIFY WITH CUSTOM CACHE ", new )
        try:
            core_cache.set(varhash, new, settings.SYMPY_CACHE_TIMEOUT)
            # print(f"PICKLE OK")
        except PicklingError as e:
            # print(f"EXCEPTION TYPE={type(e).__name__}" )
            core_cache.set(varhash, str(new), settings.SYMPY_CACHE_TIMEOUT)
        except Exception as e:
            # print(f"EXCEPTION TYPE={type(e).__name__}" )
            logger.error("COULD NOT CACHE ", type(e), str(e))
    # print( varhash ,  " SYMPIFY_WITH_CUSTOM OUT", new )
    dprint(f"    NO_CACHE ELAPSED IN CUSTOM { (time.time() - tbeg )*1000 }")
    return new
