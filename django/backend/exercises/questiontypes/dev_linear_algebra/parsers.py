from sympy import *
from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import itertools
from sympy.core import S

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


def parse_sample_variables(variables):
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
    # print("PARSE SAMPLE VARIABLES vars_ = ", variables )
    vars_ = []
    for vardict in variables:
        if not vardict['name'] in units:
            vars_ = vars_ + [vardict]
    # print("PARSE SAMPLE VARIABLES NOW vars_ = ", vars_)
    for var in vars_:
        expr = sympify_with_custom(ascii_to_sympy(var['value']), matrix_symbols)
        if hasattr(expr, 'shape'):
            sym[var['name']] = sympy.MatrixSymbol(var['name'], *expr.shape)
            matrix_symbols[var['name']] = sym[var['name']]
        else:
            sym[var['name']] = sympy.Symbol(var['name'])
        varsubs_sympify[var['name']] = sym[var['name']]
        if expr.has(sympy.Function('sample')):
            [sample] = expr.find(sympy.Function('sample'))
            sample_points = list(sample.args)
            sample_around = [
                expr.replace(sympy.Function('sample'), lambda *args: point).doit()
                for point in sample_points
            ]
            sample_variables.append({'symbol': sym[var['name']], 'around': sample_around})
        else:
            subs_rules.append((sym[var['name']], expr))
    varsubs = list(reversed(subs_rules))
    varsubs_sympify_new = {}
    for key, val in varsubs_sympify.items():
        varsubs_sympify_new[key] = val.subs(varsubs).doit()
    varsubs_sympify = varsubs_sympify_new
    # print("subs_rules = ", subs_rules)
    # print("varsubs_sympify = ", varsubs_sympify)
    # print("sample_variables = ", sample_variables)
    return (varsubs, varsubs_sympify, sample_variables)


def sympify_with_custom(expression, varsubs):
    """
    Convert asciimath expression into sympy using extra context
    Args:
        expression: asciimath
        varsubs: { string(name): substitution, ... }

    Returns:
        Sympy expression
    """
    # print("SYMPIFY WITH CUSTOM", expression)
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
        'sort': Sort,
        'Sort': Sort,
        'norm': Norm,
        'KetBra': KetBra,
        'KetMBra': KetMBra,
        'Braket': Braket,
        'NullRank': nullrank,
    }
    scope.update(ns)
    scope.update(varsubs)
    # print("LINEAR_ALGEBRA expression= ", expression)
    # print("LINEAR_ALGEBRA ascii_to_sympy = ", ascii_to_sympy(expression) )
    # print("LINEAR_ALGEBRA varsubs= ", varsubs)
    # print("LINEAR_ALGEBRA scope= ", scope)
    sexpr = sympy.sympify(ascii_to_sympy(expression), scope)
    return sexpr
