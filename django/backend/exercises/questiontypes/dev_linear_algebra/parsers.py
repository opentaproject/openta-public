from sympy import *
from sympy.matrices import *
from exercises.util import get_hash_from_string
from copy import deepcopy
from django.core.cache import cache as core_cache
from exercises.util import get_hash_from_string

# from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import re as resub
import random
import itertools
from sympy.core import S
from .unithelpers import baseunits
from .sympify_with_custom import sympify_with_custom
from sympy.core.function import AppliedUndef
from exercises.util import index_of_matching_right_paren

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
    varhash = get_hash_from_string( str(variables) + str(funcsubs) )
    ret = core_cache.get(varhash)
    if ret is not None:
        return ret
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
    ret = (varsubs, varsubs_sympify, sample_variables)
    core_cache.set(varhash, ret , 60 * 60)
    return ret

