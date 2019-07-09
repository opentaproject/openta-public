from sympy import *
import base64

# from sympy.abc import _clash1, _clash2, _clash # dont impport clashes
import re
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
from sympy import pi
import numpy as np
import re as resub


ns = {}
# Taylor clashes
ns.update(
    {
        'C': C,
        'zeta': zeta,
        'N': N,
        'Q': Q,
        'O': O,
        'beta': beta,
        'S': S,
        'gamma': gamma,
        'ff': Symbol('ff'),
        'FF': Symbol('FF'),
    }
)


lambdifymodules = ["numpy", {'cot': lambda x: 1.0 / numpy.tan(x)}]


def insert_implicit_multiply(expression):  # {{{
    result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression)
    result = resub.sub(r"((?:\W|^)[0-9]+)([a-zA-Z]+)", r"\1*\2", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    result = resub.sub("\)([A-Za-z0-9]+)", r") * \1 ", result)
    return result  # }}}


def ascii_to_sympy(expression):  # {{{
    result = expression
    result = resub.sub(r"([^=]+)==([^=]+)", r"(\1) - (\2)", result)
    dict = {'^': '**'}

    result = resub.sub(r"\|([^>]+)>\s*<([^|]+)\|", r" ( KetBra(\1,\2)  ) ", result)
    result = resub.sub(r"\|([^>]+)>([^<]+)<([^|]+)\|", r" ( KetBra(\1,\2,\3) ) ", result)
    result = braketify(result)
    if "Matrix" not in result:
        result = matrixify(result)
    result = absify(result)
    result = insert_implicit_multiply(result)
    for old, new in dict.items():
        result = result.replace(old, new)
    result = resub.sub(
        r"\]\s*([^\*]\w+)", r"]* 1.0 * \1", result
    )  # PUT IN IMPLICITY MULTIPLY IN VARIABLE DEFS WITH UNITS
    return result  # }}}


def matrixify(expression):  # # {{{
    """PUT A MATRIX( ) around outer square brackets
    """
    # print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVV");
    # print("MATRIXIFY expression = ", expression )
    l = len(expression)
    i = 0
    s = ''
    depth = 0
    while i < l:
        c = expression[i]
        if c == '[':
            if depth == 0:
                s += "Matrix("
            depth -= 1
        if c == ']':
            depth += 1
        s += expression[i]
        if c == ']' and depth == 0:
            s += ")"
        i += 1
    # print("MATRIXIFY, s = ", s )
    # print("^^^^^^^^^^^^^^^^^^^^^^^");
    return s  # }}}


def absify(expression):  # {{{
    l = len(expression)
    i = 0
    s = ''
    depth = 0
    while i < l:
        c = expression[i]
        if c == '|':
            if depth == 0:
                s += " Norm( "
                depth = -1
            elif depth == -1:
                depth = 0
        else:
            s += expression[i]
        if c == '|' and depth == 0:
            s += " ) "
        i += 1
    if depth == 0:
        return s
    else:
        return expression  # }}}


def braketify(expression):  # {{{
    rep = {}
    rep['>'] = ''
    rep['<'] = ''
    rep['|'] = ','
    l = len(expression)
    i = 0
    s = ''
    # print("STR1 = ",expression)
    depth = 0
    while i < l:
        c = expression[i]
        cr = ',' if (c == '|' and depth != 0) else c
        if c == '<':
            cr = ''
            if depth == 0:
                s += "Braket("
            depth -= 1
        if c == '>':
            cr = ''
            depth += 1
        # print( i,c, depth, s )
        s += cr
        if c == '>' and depth == 0:
            s += ")"
        i += 1
    return s  # }}}
