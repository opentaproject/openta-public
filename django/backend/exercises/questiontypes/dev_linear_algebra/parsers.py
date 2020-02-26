from sympy import *
from exercises.util import  get_hash_from_string

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

def index_of_matching_right_paren(beg, expression):
    level = 1
    ind = beg + 1
    while level > 0 and ind < len(expression):
        if expression[ind] == ')':
            level = level - 1
        elif expression[ind] == '(':
            level = level + 1
        ind = ind + 1
    assert expression[beg] == '(', 'LEFT PAREN WRONG'
    assert expression[ind-1] == ')', 'RIGHT PAREN WRONG'
    return ind 



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


def func_sub_single(expr, func_def, func_body, subrule):
    # Find the expression to be replaced, return if not there
    # print("DO FUNC_SUB_SINGLE")
    funcatoms = expr.atoms(AppliedUndef)  
    if len( funcatoms) == 0 :
        return expr
    print("FUNCATOMS = ", funcatoms, len( funcatoms) )
    for unknown_func in funcatoms :
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


def sympify_with_custom(expression, varsubs, funcsubs={}, source='UNKNOWN'):
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
        'cross': crossfunc,
        'Gt': gt,
        'Ge': ge,
        'Lt': lt,
        'Le': le,
        'Or': logicalor,
        'And': logicaland,
        'curl': curl,
        'div': localdiv,
        'grad': grad,
        #'xhat': sympy.sympify(Matrix([1, 0, 0])),
        #'yhat': sympy.sympify(Matrix([0, 1, 0])),
        #'zhat': sympy.sympify(Matrix([0, 0, 1])),
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
        'sample': sample,
    }
    myscope = scope
    subrule = []
    for key, val in myscope.items():
        if 'Function' in str(type(val)):
            subrule = subrule + [(Function(key), val)]
        else:
            subrule = subrule + [(Symbol(key), val)]

    if source == "PARSE_SAMPLE_VARIABLES":
        scope.update({'sample': sample})
    sexpr = ascii_to_sympy(declash(expression), {})
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
    vals = [str(item) for item in varsubs.values()]
    xtest = sexpr
    try :
        nit = 0
        vsub = {}
        while True : 
            previous = xtest
            p = resub.compile(r'Matrix')
            allm = list(p.finditer(xtest))
            if len(allm) == 0 :
                    break
            m = allm[0]
            (ibeg, ileft) = m.span()
            iright =  index_of_matching_right_paren(ileft,xtest)
            head = xtest[0:ibeg]
            body = xtest[ibeg:iright];
            tail = xtest[iright: ]
            print("HEAD = ", head)
            print("BODY = ", body )
            print("TAIL = ", tail )
            bodyhash = get_hash_from_string(body)
            bodyhash = resub.sub(r'[0-9]','',bodyhash)
            print("BODY = ", body , bodyhash)
            vsub[bodyhash] = sympify( body )
            xtest = head + 'vq(\'' + bodyhash + '\')' + tail  
            nit = nit + 1
            
        xtest = resub.sub('div','mydiv',xtest)
        xtest = resub.sub('And','gAnd',xtest)
        xtest = resub.sub('Nnd','gNot',xtest)
        stest = sympify( xtest ,evaluate=False)
        print("DID", srepr( stest ) )
        print("VSUB = ", vsub )
    except :
        print("FAILED WITH ", xtest )
        raise TypeError("FAILED WITH " + xtest )
    try :
        location = 'A'
        if resub.search(r'[xyz]hat', sexpr) or 'Matrix' in sexpr :
            location += 'B'
            scope.update(scope_symbolic)
            location += 'C'
            sexpr = sympy.sympify(sexpr, scope)
            location += 'D'
        else:
            location += 'E'
            print("sexpr = ", sexpr)
            if 'dalem' in sexpr and len( sexpr.split('-') ) == 2 :
                [s1,s2] = sexpr.split('-')
                print("S1 = ", s1 )
                print("S2 = ", s2 )
                s1s = sympy.sympify(s1,scope)
                s1s = replace_funcs(s1s, funcsubs, subrule)
                s2s = sympy.sympify(s2,scope)
                s2s = replace_funcs(s2s, funcsubs, subrule)
                print("S1s = ", s1s )
                print("S2s = ", s2s )
                sexpr = s1s - s2s
            else :
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
    except :
        raise TypeError("path " + location + 'failed with expression '  + sexpr  )
    return sexpr


def pre(expr, level=0):
    '''
     #
     # TEST WITH 
     from sympy import *
     pre( sympify('1 + tanh(x)')
     #
     '''
    name = 'NONAME' if not hasattr(expr, 'name') else getattr(expr, 'name')
    newargs = None
    if expr.is_Function:
        if str(expr.func) == "tanh":
            print("TANH FOUND")
            expr = Function('cosh')(*expr.args)
        print("FOUND FUNCTION", expr.func)
    elif expr.is_Symbol:
        # if name == "x" :
        #    expr.name = name + 'j'
        # else :
        #    expr = expr
        expr = expr
        print("FOUND SYMBOL ", name)
    elif expr.is_Atom:
        expr = expr
        print("ATOM FOUND", name)
    else:
        print("COMPLEX EXPRESSION", expr)
        newargs = [pre(item, level) for item in expr.args]
        expr = expr.__class__(*newargs)
    print("NEW = ", expr)
    return expr


def test(expression):
    pre(expression)


#'''
# from exercises.questiontypes.dev_linear_algebra.parsers import *
# funcsubs = [{'name': 'f', 'args': '[q]', 'value': '3 * q'}, {'name': 'g', 'args': '[x,y]', 'value': 'G(x)'}]
# expression = '(f(yhat) )-( yhat)'
# expression = 'f(q)'
# sexpr = sympify( expression )
# sympify_with_custom(expression,{}, funcsubs)
#'''
