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
        tuple ( subs_rules, sympify_rules, sample_variables )
        subs_rules: list of 2-tuples [ (sympy symbol, sympy expression), ... ] used in .subs(...)
        sympify_rules: { string(name): sympy symbol } used in sympify(...)
        sample_variables: [ { symbol: sympy Symbol/MatrixSymbol,
                              around: sympy expression ( a point around which to sample (might contain units))
                              }, ... ]

    """
    sym = {}
    vars = variables
    subs_rules = []
    sympify_rules = {}
    sample_variables = []
    matrix_symbols = {}
    for var in vars:
        expr = sympify_with_custom(ascii_to_sympy(var['value']), matrix_symbols)
        if hasattr(expr, 'shape'):
            sym[var['name']] = sympy.MatrixSymbol(var['name'], *expr.shape)
            matrix_symbols[var['name']] = sym[var['name']]
        else:
            sym[var['name']] = sympy.Symbol(var['name'])
        sympify_rules[var['name']] = sym[var['name']]
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
    return (list(reversed(subs_rules)), sympify_rules, sample_variables)


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
    sexpr = sympy.sympify(ascii_to_sympy(expression), scope)
    return sexpr
