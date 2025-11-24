# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import time

from django.conf import settings
from django.core.cache import cache as core_cache
from exercises.util import get_hash_from_string
from sympy import *

# from sympy.abc import _clash1, _clash2, _clash
from sympy.matrices import *

from .functions import *
from .string_formatting import ascii_to_sympy
from .sympify_with_custom import sympify_with_custom
from .unithelpers import *
from .unithelpers import baseunits


def parse_sample_variables(variables, funcsubs={}, extradefs={}, source="UNDEFINED"):
    sym = {}
    varhash = get_hash_from_string("PARSE" + str(variables) + str(funcsubs) + str(extradefs))
    ret = core_cache.get(varhash)
    time.time()
    docache = settings.DO_CACHE
    if docache and (ret is not None):
        time.time()
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
        if not vardict["name"] in units:
            vars_ = vars_ + [vardict]
    for var in vars_:
        # print("DO VAR = ", var["name"], "=", var["value"])
        name = str(var["name"])
        # raise TypeError("A variable cannot be named " + name )
        expr = sympify_with_custom(
            ascii_to_sympy(var["value"]),
            varsubs_sympify,
            funcsubs,
            extradefs,
            "PARSE_SAMPLE_VARIABLES2",
        )
        # print("EXPR = ", expr )
        nexpr = simplify(expr.subs(baseunits))
        if hasattr(expr, "shape"):
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
        varsubs_sympify_new[key] = (val.subs(varsubs)).doit()
    varsubs_sympify = varsubs_sympify_new
    ret = (varsubs, varsubs_sympify, sample_variables)
    try:
        vs = [(srepr(key), srepr(val)) for key, val in varsubs_sympify.items()]
        v = [(srepr(key), srepr(val)) for key, val in varsubs]
        rets = (v, vs, sample_variables)
        core_cache.set(varhash, rets, 60 * 60)
    except Exception as e:
        raise NameError(f"ERROR PARSERS.PY E66502 CANT CACHE  {type(e).__name__}")

    #print(f"SAMPLE_VARIABLES = {ret}")

    return ret
