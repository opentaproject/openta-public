from sympy import *

# from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import itertools
from sympy.core import S
from .unithelpers import baseunits
from sympy.core.function import AppliedUndef

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


def replace_funcs_once(sexpr, funcsubs):
    for sub in funcsubs:
        func_def = sympy.Function(sub['name'])
        argnames = ','.join([item.name for item in sub['args']])
        funcdefstring = sub['name'] + '(' + argnames + ')'
        func_def = sympy.sympify(funcdefstring)
        func_body = sympy.sympify(sub['value'])
        sexpr = func_sub(sexpr, func_def, func_body)
    return sexpr


def replace_funcs(sexpr, funcsubs):
    # print("INCOMING = ", sexpr)
    while True:
        prev = sexpr
        sexpr = replace_funcs_once(sexpr, funcsubs)
        if sexpr == prev:
            # print("OUTGOING = ", sexpr)
            return sexpr


def parse_sample_variables(variables, funcsubs={}):
    """
    Parses a list of asciimath defined variables into correct sympy representations.

    Args:
        variables: [ { name: string, value: asciimath } , ... ]

    Returns:
        tuple ( subs_rules, varsubs_sympify, sample_variables )
        subs_rules: list of 2-tuples [ (sympy symbol, sympy expression), ... ] used in .subs(...)
        varsubs_sympify: { string(name): sympy symbol } used in sympify(...)
        sample_variables: [ { symbol: sympy Symbol/MatrixSymbol,
                              around: sympy expression ( a point around which to sample (might contain units))
                              }, ... ]

    """
    sym = {}
    vars_ = variables
    subs_rules = []
    varsubs_sympify = {}
    sample_variables = []
    matrix_symbols = {}
    vars_ = []
    for vardict in variables:
        if not vardict['name'] in units:
            vars_ = vars_ + [vardict]
    for var in vars_:
        name = str(var['name'])
        # raise TypeError("A variable cannot be named " + name )
        expr = sympify_with_custom(
            ascii_to_sympy(var['value']), varsubs_sympify, funcsubs, 'PARSE_SAMPLE_VARIABLES'
        )
        nexpr = simplify(expr.subs(baseunits))
        if hasattr(expr, 'shape'):
            sym[name] = sympy.MatrixSymbol(name, *expr.shape)
            matrix_symbols[name] = expr
        elif nexpr.is_Atom:
            sym[name] = sympy.Symbol(name)
        else:
            sym[name] = expr  # sympy.Symbol(var['name'])
        varsubs_sympify[name] = expr
        if expr.has(sympy.Function('sample')):
            [sample] = expr.find(sympy.Function('sample'))
            sample_points = list(sample.args)
            sample_around = [
                expr.replace(sympy.Function('sample'), lambda *args: point).doit()
                for point in sample_points
            ]
            sample_variables.append({'symbol': sym[name], 'around': sample_around})
        else:
            subs_rules.append((sym[name], expr))
    varsubs = list(reversed(subs_rules))
    varsubs_sympify_new = {}
    for key, val in varsubs_sympify.items():
        varsubs_sympify_new[key] = val.subs(varsubs).doit()
    varsubs_sympify = varsubs_sympify_new
    return (varsubs, varsubs_sympify, sample_variables)


def func_sub_single(expr, func_def, func_body):
    # Find the expression to be replaced, return if not there
    for unknown_func in expr.atoms(AppliedUndef):
        # print("REPLACING ", unknown_func , " IN ", expr )
        if unknown_func.func == func_def.func:
            replacing_func = unknown_func
            break
    else:
        # print("RETURNING ", expr )
        return expr
    arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(func_def.args, replacing_func.args)}
    func_body_subst = func_body.subs(arg_sub)
    ret = expr.subs(replacing_func, func_body_subst)
    # print("RETURNING ", ret )
    return ret


def func_sub(expr, func_def, func_body):
    if any(func_def.func == body_func.func for body_func in func_body.atoms(AppliedUndef)):
        raise ValueError('Function may not be recursively defined')

    while True:
        prev = expr
        expr = func_sub_single(expr, func_def, func_body)
        if prev == expr:
            return expr


def sympify_with_custom(expression, varsubs, funcsubs={}, source='UNKNOWN' ) :
    """
    Convert asciimath expression into sympy using extra context
    Args:
        expression: asciimath
        varsubs: { string(name): substitution, ... }

    Returns:
        Sympy expression
    """
    scope = {
        'abs': Norm,  # sympy.Function('norm')
        'Abs': Norm,  # sympy.Function('norm')
        'Trace': Trace,
        'Transpose': Transpose,
        'Conjugate': conjugate,
        'AreEigenvaluesOf': eigenvaluesof,
        'AreEigenvaluesOf': AreEigenvaluesOf,
        'IsDiagonalizationOf': IsDiagonalizationOf,
        'IsHermitian': IsHermitian,
        'RankOf': rankof,
        'IsUnitary': isunitary,
        'cross': Cross,
        'Gt': gt,
        'Ge': ge,
        'Lt': lt,
        'Le': le,
        'Or': logicalor,
        'And': logicaland,
        'curl': curl,
        'div': div,
        'grad': grad,
        'xhat': sympy.sympify(Matrix([1, 0, 0])),
        'yhat': sympy.sympify(Matrix([0, 1, 0])),
        'zhat': sympy.sympify(Matrix([0, 0, 1])),
        'Partial': partial,
        'partial': partial,
        'Prime': Prime,
        'Not': logicalnot,
        'IsEqual': eq,
        'IsNotEqual': neq,
        'diagonalpart': diagonalof,
        'IsDiagonal': IsDiagonal,
        'IsDiagonalizable': IsDiagonalizable,
        'true': sympy.sympify('1'),
        'false': sympy.sympify('0'),
        'True': sympy.sympify('1'),
        'False': sympy.sympify('0'),
        'times': Times,
        'dot': Dot,
        'del2': del2,
        'sort': Sort,
        'Sort': Sort,
        'norm': Norm,
        'KetBra': KetBra,
        'KetMBra': KetMBra,
        'Braket': Braket,
        'NullRank': nullrank,
        'sample' : sample,
    }
    myscope = scope
    if source == "PARSE_SAMPLE_VARIABLES"  :
        scope.update({ 'sample' : sample } )
    #print("1 EXPRESSION INTO SYMPIFY WITH CUSTOM",source)
    #print("2 EXPRESSION INTO SYMPIFY WITH CUSTOM",expression)
    #print("3 IN SYMPIFY WITH CUSTOM FUNCSUBS = ", funcsubs)
    sexpr = ascii_to_sympy(declash(expression), {})
    # print("NS = ", ns )
    scope.update(ns)
    scope.update(varsubs)
    scope_symbolic = {
        'x': sympy.sympify('x'),
        'y': sympy.sympify('y'),
        'z': sympy.sympify('z'),
        't': sympy.sympify('t'),
    }
    
    #print("3.2 EXPRESSION ", sexpr )
    try :
        # HACK TODO
        # print("SCOPE = ", scope )
        #  TYPE ERROR WHEN DEFININ f(xhat) == xhat
        #  and f i identify function 
        #
        sexpr = sympy.sympify(sexpr, scope)
        #print("4 EXPRESSION 2 AFTER FUNCSUB",sexpr)
    except TypeError as e :
        #print("ERROR = ", str(e), type(e).__name__ )
        pass
    sexpr = replace_funcs(sexpr, funcsubs).doit()
    #print("5 EXPRSSION  AFTER FUNCSUB ", sexpr)
    scope.update(scope_symbolic)
    sexpr = sympy.sympify(str(sexpr), scope).doit()
    #print("6 EXPRESSION 2 AFTER FUNCSUB",sexpr)
    #print(" 6 EXPRESSION3 SYMPIFY_WITH_CUSTOM RESULT IS ", sexpr )
    sexpr = sexpr.doit()
    #print("7 EXPRESSION3 SYMPIFY_WITH_CUSTOM RESULT IS ", sexpr )

    return sexpr
