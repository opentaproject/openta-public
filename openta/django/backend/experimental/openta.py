# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import re as resub


def index_of_matching_right_paren(beg, expression):
    level = 1
    ind = beg + 1
    while level > 0 and ind < len(expression):
        if expression[ind] == ")":
            level = level - 1
        elif expression[ind] == "(":
            level = level + 1
        ind = ind + 1
    assert expression[beg] == "(", "LEFT PAREN WRONG"
    assert expression[ind - 1] == ")", "RIGHT PAREN WRONG"
    return ind


def index_of_matching_left_paren(indbegin, result):
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


def parenparse(ex, level=0):
    indbegin = ex.find("(")
    if indbegin == -1:
        return "leaf_node[" + ex + "]" if len(ex) > 0 else ""
    funbegin, _ = resub.search(r"[0-9A-Za-z_]*[\']*\(", ex).span()
    head = ex[0:funbegin]
    fun_name = ex[funbegin:indbegin]
    indend = index_of_matching_right_paren(indbegin, ex)
    body = ex[indbegin:indend]
    bodybody = ex[indbegin + 1 : indend - 1]
    tail = ex[indend:]
    prime_beg, prime_end = resub.search(r"[\']*", tail).span()
    prime_beg = prime_beg + indend
    prime_end = prime_end + indend
    tail = ex[prime_end:]
    primes = ex[prime_beg:prime_end]
    tail = ex[prime_end:]
    pieces = ">" + head + "<>" + fun_name + "<>" + body + "<>" + primes + "<>" + tail
    assert ex == head + fun_name + body + primes + tail, "PIECES DONT ADD UP"
    return (
        parenparse(head, level + 1)
        + " function_node["
        + fun_name
        + parenparse(bodybody, level + 1)
        + primes
        + "] "
        + parenparse(tail, level + 1)
        + " "
    )


ex1 = " ( q + sin( 42 y ) + cos''( 35 x ) - ( 93  sin( 45 x )'' + 3 )^5  )"


def replace_user_defined_functions(expression, funcsubs):
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
        ind = index_of_matching_right_paren(end, expression)
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
        middle = " Prime(" + fun + arg + "," + arg + "," + order + "," + str(rep) + ") "
        expression = ex1 + middle + ex3
        if add_paren:
            expression = "(" + expression + ")'"
        allm = list(p.finditer(expression))
        it = it + 1
    # expression = resub.sub(r'#','',expression)
    expression = resub.sub(r"#" + searchstring, r"\1", expression)
    return expression
