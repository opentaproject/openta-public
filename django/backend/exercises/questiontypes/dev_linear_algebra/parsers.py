from sympy import *
import json
from sympy.matrices import *
from exercises.util import get_hash_from_string
from django.conf import settings
from copy import deepcopy
from django.core.cache import cache as core_cache
from exercises.util import get_hash_from_string
import time

# from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import re as resub
import random
import itertools
from sympy.core import S
from exercises.questiontypes.dev_linear_algebra.unithelpers import baseunits
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
    sym = {}
    varhash = get_hash_from_string(str(variables) + str(funcsubs))
    ret = core_cache.get(varhash)
    tbeg = time.time()
    docache = settings.DO_CACHE
    if docache  and (ret is not None):
        timebeg = time.time()
        (v, vs, sample_variables) = ret
        varsubs_sympify = {sympify(key): sympify(val) for key, val in vs}
        varsubs = [(sympify(key), sympify(val)) for key, val in v]
        rets = (varsubs, varsubs_sympify, sample_variables)
        return rets

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
        #print("VAR = ", var['name'] , '=' , var['value'] )
        name = str(var['name'])
        # raise TypeError("A variable cannot be named " + name )
        expr = sympify_with_custom(
            ascii_to_sympy(var['value']), varsubs_sympify, funcsubs, 'PARSE_SAMPLE_VARIABLES'
        )
        #print("EXPR = ", expr )
        nexpr = simplify(expr.subs(baseunits))
        if hasattr(expr, 'shape'):
            sym[name] = sympy.MatrixSymbol(name, *expr.shape)
            matrix_symbols[name] = expr
        elif nexpr.is_Atom:
            sym[name] = sympy.Symbol(name)
        else:
            sym[name] = expr  # sympy.Symbol(var['name'])
        varsubs_sympify[name] = expr
        subs_rules.append((sym[name], expr))
    varsubs = list(reversed(subs_rules))
    varsubs_sympify_new = {}
    for key, val in varsubs_sympify.items():
        varsubs_sympify_new[key] = (val.subs(varsubs) ).doit()
    varsubs_sympify = varsubs_sympify_new
    ret = (varsubs, varsubs_sympify, sample_variables)
    try:
        vs = [(srepr(key), srepr(val)) for key, val in varsubs_sympify.items()]
        v = [(srepr(key), srepr(val)) for key, val in varsubs]
        rets = (v, vs, sample_variables)
        core_cache.set(varhash, rets, 60 * 60)
    except Exception as e:
       raise NameError("CANT CACHE ")

    return ret
