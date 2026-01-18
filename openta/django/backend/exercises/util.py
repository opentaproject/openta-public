# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json as JSON
import functools
import re, hashlib
import sympy

COMPARISON_PRECISION = 1.e-8
CLEAN_PRECISION = 1.e-14
p53 = 16


def nested_print(d):
    print(JSON.dumps(d, indent=4))
    return


def deep_get(dictionary, *keys, default=None):
    result = functools.reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)
    if result is None:
        return default
    else:
        return result


def compose(*funcs):
    return lambda x: functools.reduce(lambda v, f: f(v), funcs, x)


def get_hash_from_string(string):
    string_to_hash = str(re.sub(r"(\s|\\n)+", " ", str(string)))  # BE CAREFUL WITH IMPLICIT MULTIPLIES!
    globalhash = (hashlib.md5(string_to_hash.encode("utf-8")).hexdigest())[:10]
    res = ""
    for c in globalhash:
        if c.isdigit():
            c = chr(int(c) + 97)
        res = res + c
    return res


def index_of_matching_right_paren(beg, expression):
    level = 1
    ind = beg + 1
    while level > 0 and ind < len(expression):
        if expression[ind] == ")":
            level = level - 1
        elif expression[ind] == "(":
            level = level + 1
        ind = ind + 1
    assert expression[beg] == "(", "LEFT PAREN WRONG beg = %s, expression = %s , [%s] " % (
        beg,
        expression,
        expression[beg],
    )
    assert expression[ind - 1] == ")", "RIGHT PAREN WRONG = %s , expression= %s , [%s] " % (
        ind - 1,
        expression,
        expression[ind - 1],
    )
    return ind


def index_of_matching_left_paren(result, indbegin):
    level = 1
    ind = indbegin
    while level > 0 and ind > 0:
        ind = ind - 1
        if result[ind] == "(":
            level = level - 1
        elif result[ind] == ")":
            level = level + 1
    assert result[indbegin] == ")", "RIGHT PAREN  MISSING"
    assert result[ind] == "(", "LEFT PAREN  MISSING"
    return ind

def mychop(expr, threshold=1.e-12):
    if expr.is_Atom:  # Base case: if the expression is an atom (e.g., a number or a symbol)
        if expr.is_number and abs(expr.evalf()) < threshold:
            return sympy.S.Zero
        else:
            return expr
    else:  # Recursively process arguments of the expression
        return expr.func(*[mychop(arg, threshold) for arg in expr.args])


