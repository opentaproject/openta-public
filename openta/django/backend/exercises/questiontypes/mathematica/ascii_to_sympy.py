# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""String conversion functions (Asciimath -> Sympy)

Various functions needed to convert input asciimath into something that sympy can parse with sympify.

"""
import re as resub

from exercises.util import index_of_matching_left_paren, index_of_matching_right_paren
from sympy import *


def replace_sample_funcs(expression, scale=None):
    while "sample" in expression:
        m = resub.search(r"sample\(", expression)
        pbeg = m.end(0) - 1
        pend = index_of_matching_right_paren(pbeg, expression)
        samplearg = expression[pbeg + 1 : pend - 1]
        firstarg = samplearg.split(",")[0]
        head = expression[0 : pbeg - 6]
        tail = expression[pend:]
        if scale:
            expression = head + " (" + scale + " *  ( " + firstarg + ") )" + tail
        else:
            expression = head + firstarg + tail

    return expression


def insert_implicit_multiply(expression):  # {{{
    result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression)
    result = resub.sub(r"\)\(", r" ) ( ", result)
    result = resub.sub(r"\)([-+\/*])\(", r" ) \1 ( ", result)
    if "**" in result:
        result = result.replace("**", "##")
    result = resub.sub(r"\)([-+\/*])", r" ) \1 ", result)
    if "##" in result:
        result = result.replace("##", "**")
    result = resub.sub(r"-([A-z])", r"-  \1", result)
    result = resub.sub(r"((?:\W|^)[0-9]+)([a-zA-Z]+)", r"\1*\2", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)\-])", r"\1)*(\2", result)
    result = resub.sub("\)([A-Za-z0-9]+)", r") * \1", result)
    result = resub.sub(r"^-([A-z])", r"- \1", result)
    result = resub.sub(r"[\s\n]+", " ", result)
    return result  # }}}


def oldreplace_user_defined_functions(expression, funcsubs):
    defs = list(funcsubs.keys())
    if len(defs) == 0:
        return expression
    searchstring = "(" + "|".join(defs) + ")"
    # expression = 'ff\'\'(gg(z))*gg\'(z) '
    # expression = resub.sub(r'('+searchstring+')',r" \1",expression)
    p = resub.compile(r"(^|\s|\()" + searchstring + "[']*(?=\()")
    allm = list(p.finditer(expression))
    it = 0
    while len(allm) > 0 and it < 50:
        m = allm[0]
        (beg, end) = m.span()
        if expression[beg] == "(":
            beg = beg + 1
        ind = oldindex_of_matching_right_paren(end, expression)
        head = expression[beg:end].strip()
        arg = expression[end : ind + 1]
        ex1 = expression[0:beg]
        ex2 = expression[beg : ind + 1]
        ex3 = expression[ind + 1 :]
        add_paren = False
        if ex3:
            if ex3[0] == "'":
                ex3 = ex3[1:]
                add_paren = True
        fun = (resub.sub(r"\'*", "", head)).strip()
        rep = funcsubs[fun]
        order = str(head.count("'"))
        fun = "#" + fun
        middle = " Prime(" + fun + arg + "," + arg + "," + order + "," + str(rep) + "()) "
        expression = ex1 + middle + ex3
        if add_paren:
            expression = "(" + expression + ")'"
        allm = list(p.finditer(expression))
        it = it + 1
    # expression = resub.sub(r'#','',expression)
    expression = resub.sub(r"#" + searchstring, r"\1", expression)
    return expression


def replace_primes(expression, funcsubs):
    paren_check(expression, "INTO REPLACE_PRIMES")
    searchstring = "([A-z0-9_]+)"
    # expression = 'ff\'\'(gg(z))*gg\'(z) '
    # expression = resub.sub(r'('+searchstring+')',r" \1",expression)
    p0 = resub.compile(r"(^|\s|\()" + searchstring + "[']*(?=\()")
    p1 = resub.compile(r"(^|\s|\()" + searchstring + "[']+(?=\()")
    allm = list(p1.finditer(expression))
    it = 0
    while len(allm) > 0 and it < 50:
        m = allm[0]
        (beg, end) = m.span()
        if expression[beg] == "(":
            beg = beg + 1
        ind = index_of_matching_right_paren(end, expression)
        head = expression[beg:end].strip()
        arg = expression[end:ind]
        ex1 = expression[0:beg]
        ex2 = expression[beg : ind + 1]
        ex3 = expression[ind:]  # if ind < len(expression) else ''
        add_paren = False
        if ex3:
            if ex3[0] == "'":
                ex3 = ex3[1:]
                add_paren = True
        fun = (resub.sub(r"\'*", "", head)).strip()
        funcsubs.get(fun, fun)
        order = str(head.count("'"))
        fun = "#" + fun
        middle = " Prime(" + fun + arg + "," + arg + "," + order + ")"  # + ',' + str(rep) + '(x)) '
        expression = ex1 + middle + ex3
        if add_paren:
            expression = "(" + expression + ")'"
        allm = list(p1.finditer(expression))
        it = it + 1
    expression = resub.sub(r"#", "", expression)
    expression = resub.sub(r"#" + searchstring, r"\1", expression)
    paren_check(expression, "OUT OF REPLACE_PRIMES")
    return expression


def paren_check(expression, msg):
    should_be_end = index_of_matching_right_paren(0, "(" + expression + ")")
    assert should_be_end == len(expression) + 2, msg + " : " + expression


def ascii_to_sympy(expression, funcsubs={}):  # {{{
    # print("ASCII_TO_SYMPY expression = ", expression)
    expression = str(expression)
    should_be_end = index_of_matching_right_paren(0, "(" + expression + ")")
    assert should_be_end == len(expression) + 2, "E561 unmatched parenthesis in " + expression
    assert expression.count("(") == expression.count(")"), "E562 unmatched parentesis"
    result = expression
    result = resub.sub(r"([^=]+)==([^=]+)", r"(\1) - (\2)", result)
    dict = {"^": "**"}

    result = resub.sub(r"\|([^>]+)>\s*<([^|]+)\|", r" ( KetBra(\1,\2)  ) ", result)
    result = resub.sub(r"\|([^>]+)>([^<]+)<([^|]+)\|", r" ( KetBra(\1,\2,\3) ) ", result)
    result = braketify(result)
    if "Matrix" not in result:
        result = matrixify(result)
    result = absify(result)
    # print(f"RESULT1 {result}")
    result = insert_implicit_multiply(result)
    # print(f"RESULT1b {result}")
    for old, new in dict.items():
        result = result.replace(old, new)
    # print(f"RESULT2 {result}")

    # result = resub.sub(r"\]\s*([^\*]\w+)", r"]* 1.0 * \1", result)
    paren_check(result, "CHECK1 ")
    result = replace_primes(result, funcsubs)
    paren_check(result, "CHECK2 ")

    it = 0
    # REPLACE ALL )\' CONSTRUCTIONS
    while result.find(")'") > 0 and it < 20:
        indend = result.index(")'")
        indbegin = index_of_matching_left_paren(result, indend)
        ind = indbegin
        while ind > 0 and not result[ind - 1] in " +-/*":
            ind = ind - 1
        left = result[0 : max(0, ind - 1)]
        middle = result[ind : indend + 1]
        right = result[indend + 2 :]
        result = left + "Partial(" + middle + ")" + right
        it = it + 1
    paren_check(result, "MATCHING PAREN COMING OUT OF ASCII_TO_SYMPY ")
    # print("ASCII_TO_SYMPY result = ", result)

    return result  # }}}


def matrixify(expression):  # # {{{
    """PUT A MATRIX( ) around outer square brackets"""
    l = len(expression)
    i = 0
    s = ""
    depth = 0
    while i < l:
        c = expression[i]
        if c == "[":
            if depth == 0:
                s += "Matrix("
            depth -= 1
        if c == "]":
            depth += 1
        s += expression[i]
        if c == "]" and depth == 0:
            s += ")"
        i += 1
    return s  # }}}


def absify(expression):  # {{{
    expression = resub.sub(r"([^\w]|^)abs\(", r"\1 norm(", expression)
    l = len(expression)
    i = 0
    s = ""
    depth = 0
    while i < l:
        c = expression[i]
        if c == "|":
            if depth == 0:
                s += " norm( "
                depth = -1
            elif depth == -1:
                depth = 0
        else:
            s += expression[i]
        if c == "|" and depth == 0:
            s += " ) "
        i += 1
    if depth == 0:
        return s
    else:
        return expression  # }}}


def braketify(expression):  # {{{
    rep = {}
    rep[">"] = ""
    rep["<"] = ""
    rep["|"] = ","
    l = len(expression)
    i = 0
    s = ""
    depth = 0
    while i < l:
        c = expression[i]
        cr = "," if (c == "|" and depth != 0) else c
        if c == "<":
            cr = ""
            if depth == 0:
                s += "Braket("
            depth -= 1
        if c == ">":
            cr = ""
            depth += 1
        s += cr
        if c == ">" and depth == 0:
            s += ")"
        i += 1
    return s  # }}}


def expand_power(expr, matrices):
    exp = "**"
    while resub.search(r"\*\*[(0-9)]+", expr):
        i = resub.search(r"\*\*[(0-9)]+", expr).start()
        iend = i - 1
        ibeg = index_of_matching_left_paren(expr, iend)
        while ibeg > 0 and expr[ibeg - 1] != " ":
            ibeg = ibeg - 1
        head = expr[0:ibeg]
        mid = expr[ibeg : iend + 1]
        tail = expr[iend + 2 :]
        p = resub.findall(r"[0-9]+", tail)[0]
        itail = iend + 2 + len(p)
        while expr[itail] != " ":
            itail = itail + 1
        tail = expr[itail:]
        ip = int(p)
        print(f"{head} - {mid} {ip} - {tail}")
        term = mid
        while ip > 1:
            term = f"{term} * {mid}"
            ip = ip - 1
        newstring = f"{head} ( {term}  ) {tail}"
        expr = newstring
    print(f"EXPR = {expr}")
    return expr


def declash(expression):  ### RIDICULOUS beta and gamma are defined as functions# {{{
    # print("DECLASH ", expression )
    result = resub.sub(r"([^e]|^)gamma", r"\1variablegamma", expression)
    # result = resub.sub(r"([ +-*])dot", r"\1Dot", result)
    result = resub.sub(r"([^e]|^)beta", r"\1variablebeta", result)
    result = resub.sub(r"([^e]|^)zeta", r"\1variablezeta", result)
    result = resub.sub(r"([^e]|^)FF", r"\1variableFF", result)
    result = resub.sub(r"([^e]|^)ff", r"a\1variableff", result)
    result = resub.sub(r"([^e]|^)lambda", r"\1variablelambda", result)
    result = resub.sub(r"(\W|\A|^)e\^", r"\1 E^", result)
    result = resub.sub(r"(\W|\A|^)e\*\*", r"\1 E**", result)
    # result = resub.sub(r"(^|\W)(N)(\W|$)",r"\1 newton \3", result)
    result = resub.sub(r"(\W|^)S(\W|$)", r"\1variableS\2", result)
    clashes = [
        {"Gt": "localGt"},
        {"Lt": "localLt"},
        {"And": "localAnd"},
        {"Not": "localNot"},
        {"div": "localdiv"},
        {"Or": "localOr"},
        {"Ge": "localGe"},
        {"d": "partial"},
        # {'cross': 'crossfunc'},
        {"real": "re"},
        {"imag": "im"},
        {"Transpose": "localTranspose"},
    ]
    expression = resub.sub(r",", " ,", expression)
    resultold = ""
    while not resultold == result:
        resultold = result
        for clash in clashes:
            key = list(clash.keys())[0]
            if key in expression:
                result = resub.sub(r"(\A|\s|,|\()" + key + "\(", r"\1 " + clash[key] + "(", result)
    result = resub.sub(r" ,", ",", result)
    # print("RESULT = ", result)
    return result  # }}}
