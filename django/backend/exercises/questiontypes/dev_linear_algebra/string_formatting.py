"""String conversion functions (Asciimath -> Sympy)

Various functions needed to convert input asciimath into something that sympy can parse with sympify.

"""
import re as resub
from sympy import *


def insert_implicit_multiply(expression):  # {{{
    result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression)
    result = resub.sub(r"((?:\W|^)[0-9]+)([a-zA-Z]+)", r"\1*\2", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)\-])", r"\1)*(\2", result)
    result = resub.sub("\)([A-Za-z0-9]+)", r") * \1 ", result)
    return result  # }}}


def index_of_matching_paren(beg, expression):
    level = 1
    ind = beg + 1
    while level > 0 and ind < len(expression):
        if expression[ind] == ')':
            level = level - 1
        elif expression[ind] == '(':
            level = level + 1
        ind = ind + 1
    return ind - 1


def replace_user_defined_functions(expression, funcsubs):
    defs = list(funcsubs.keys())
    if len(defs) == 0:
        return expression
    searchstring = '(' + '|'.join(defs) + ')'
    # expression = 'ff\'\'(gg(z))*gg\'(z) '
    # expression = resub.sub(r'('+searchstring+')',r" \1",expression)
    p = resub.compile(r'(^|\s|\()' + searchstring + "[\']*(?=\()")
    allm = list(p.finditer(expression))
    it = 0
    while len(allm) > 0 and it < 50:
        m = allm[0]
        (beg, end) = m.span()
        if expression[beg] == '(':
            beg = beg + 1
        ind = index_of_matching_paren(end, expression)
        head = expression[beg:end].strip()
        arg = expression[end : ind + 1]
        ex1 = expression[0:beg]
        ex2 = expression[beg : ind + 1]
        ex3 = expression[ind + 1 :]
        fun = (resub.sub(r'\'*', '', head)).strip()
        rep = funcsubs[fun]
        order = str(head.count('\''))
        fun = '#' + fun
        middle = ' prime(' + fun + arg + ',' + arg + ',' + order + ',' + str(rep) + ') '
        expression = ex1 + middle + ex3
        allm = list(p.finditer(expression))
        it = it + 1
    # expression = resub.sub(r'#','',expression)
    expression = resub.sub(r'#' + searchstring, r"\1", expression)
    return expression


def ascii_to_sympy(expression, funcsubs={}):  # {{{
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

    def my_replace(match):
        match1 = match.group(1)
        fun = str(match1)
        match2 = match.group(2)
        match3 = match.group(3)
        val = funcsubs.get(fun, fun)
        order = str(len(match2))
        ret = "prime(" + match1 + match3 + ',' + match3 + ',' + order + ',' + str(val) + ')'
        return ret

    result = replace_user_defined_functions(result, funcsubs)
    result = resub.sub(r"([A-z]+)([\']+)(\([^\)]+\))", my_replace, result)
    result = resub.sub(r"(^|\s)d\(", '\1 Partial(', result)
    while result.find(')\'') > 0:
        ind = result.index(')\'')
        level = 1
        indbegin = ind
        while level > 0 and ind > 0:
            ind = ind - 1
            if result[ind] == '(':
                level = level - 1
            elif result[ind] == ')':
                level = level + 1
        indend = ind
        while ind > 0 and ' +-/*'.find(result[ind - 1]) == -1:
            ind = ind - 1
        head = result[0:ind]
        piece1 = result[ind:indend]
        piece2 = result[indend:indbegin]
        tail = ')' + result[indbegin + 2 :]
        result = head + ' Partial( ' + piece1 + piece2 + ' ) ' + tail

    return result  # }}}


def matrixify(expression):  # # {{{
    """PUT A MATRIX( ) around outer square brackets
    """
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
                s += " abs( "
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
        s += cr
        if c == '>' and depth == 0:
            s += ")"
        i += 1
    return s  # }}}


def declash(expression):  ### RIDICULOUS beta and gamma are defined as functions# {{{
    result = resub.sub(r"gamma", r"variablegamma", expression)
    result = resub.sub(r"beta", r"variablebeta", result)
    result = resub.sub(r"FF", r"variableFF", result)
    result = resub.sub(r"ff", r"variableff", result)
    result = resub.sub(r"lambda", r"variablelambda", result)
    result = resub.sub(r" d\(", r" partial(", result)
    
    

    return result  # }}}
