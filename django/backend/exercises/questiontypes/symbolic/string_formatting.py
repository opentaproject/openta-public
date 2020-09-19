"""String conversion functions (Asciimath -> Sympy)

Various functions needed to convert input asciimath into something that sympy can parse with sympify.

"""
import re as resub
from sympy import *
from exercises.util import index_of_matching_left_paren, index_of_matching_right_paren


def insert_implicit_multiply(expression):  # {{{
    result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression)
    result = resub.sub(r"((?:\W|^)[0-9]+)([a-zA-Z]+)", r"\1*\2", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)\-])", r"\1)*(\2", result)
    result = resub.sub("\)([A-Za-z0-9]+)", r") * \1 ", result)
    return result  # }}}


def oldreplace_user_defined_functions(expression, funcsubs):
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
        ind = oldindex_of_matching_right_paren(end, expression)
        head = expression[beg:end].strip()
        arg = expression[end : ind + 1]
        ex1 = expression[0:beg]
        ex2 = expression[beg : ind + 1]
        ex3 = expression[ind + 1 :]
        add_paren = False
        if ex3:
            if ex3[0] == "\'":
                ex3 = ex3[1:]
                add_paren = True
        fun = (resub.sub(r'\'*', '', head)).strip()
        rep = funcsubs[fun]
        order = str(head.count('\''))
        fun = '#' + fun
        middle = ' Prime(' + fun + arg + ',' + arg + ',' + order + ',' + str(rep) + '()) '
        expression = ex1 + middle + ex3
        if add_paren:
            expression = '(' + expression + ')\''
        allm = list(p.finditer(expression))
        it = it + 1
    # expression = resub.sub(r'#','',expression)
    expression = resub.sub(r'#' + searchstring, r"\1", expression)
    return expression


def replace_primes(expression, funcsubs):
    paren_check(expression, 'INTO REPLACE_PRIMES')
    searchstring = '([A-z0-9_]+)'
    # expression = 'ff\'\'(gg(z))*gg\'(z) '
    # expression = resub.sub(r'('+searchstring+')',r" \1",expression)
    p0 = resub.compile(r'(^|\s|\()' + searchstring + "[\']*(?=\()")
    p1 = resub.compile(r'(^|\s|\()' + searchstring + "[\']+(?=\()")
    allm = list(p1.finditer(expression))
    it = 0
    while len(allm) > 0 and it < 50:
        m = allm[0]
        (beg, end) = m.span()
        if expression[beg] == '(':
            beg = beg + 1
        ind = index_of_matching_right_paren(end, expression)
        head = expression[beg:end].strip()
        arg = expression[end:ind]
        ex1 = expression[0:beg]
        ex2 = expression[beg : ind + 1]
        ex3 = expression[ind:]  # if ind < len(expression) else ''
        add_paren = False
        if ex3:
            if ex3[0] == "\'":
                ex3 = ex3[1:]
                add_paren = True
        fun = (resub.sub(r'\'*', '', head)).strip()
        rep = funcsubs.get(fun, fun)
        order = str(head.count('\''))
        fun = '#' + fun
        middle = ' Prime(' + fun + arg + ',' + arg + ',' + order + ')'  # + ',' + str(rep) + '(x)) '
        expression = ex1 + middle + ex3
        if add_paren:
            expression = '(' + expression + ')\''
        allm = list(p1.finditer(expression))
        it = it + 1
    expression = resub.sub(r'#', '', expression)
    expression = resub.sub(r'#' + searchstring, r"\1", expression)
    paren_check(expression, 'OUT OF REPLACE_PRIMES')
    return expression


# def index_of_matching_left_paren(result, indbegin):
#    level = 1
#    ind = indbegin
#    while level > 0 and ind > 0:
#        ind = ind - 1
#        if result[ind] == '(':
#            level = level - 1
#        elif result[ind] == ')':
#            level = level + 1
#    assert result[indbegin] == ')', "RIGHT PAREN  MISSING"
#    assert result[ind] == '(', "LEFT PAREN  MISSING"
#    return ind


def paren_check(expression, msg):
    should_be_end = index_of_matching_right_paren(0, '(' + expression + ')')
    assert should_be_end == len(expression) + 2, msg + " : " + expression


def ascii_to_sympy(expression, funcsubs={}):  # {{{
    should_be_end = index_of_matching_right_paren(0, '(' + expression + ')')
    assert should_be_end == len(expression) + 2, (
        "MATCHING PAREN ERROR IN ASCII_TO_SYMPY " + expression
    )
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

    # result = resub.sub(r"\]\s*([^\*]\w+)", r"]* 1.0 * \1", result)
    paren_check(result, 'CHECK1 ')
    result = replace_primes(result, funcsubs)
    paren_check(result, 'CHECK2 ')

    it = 0
    # REPLACE ALL )\' CONSTRUCTIONS
    while result.find(')\'') > 0 and it < 20:
        indend = result.index(')\'')
        indbegin = index_of_matching_left_paren(result, indend)
        ind = indbegin
        while ind > 0 and not result[ind - 1] in ' +-/*':
            ind = ind - 1
        left = result[0 : max(0, ind - 1)]
        middle = result[ind : indend + 1]
        right = result[indend + 2 :]
        result = left + 'Partial(' + middle + ")" + right
        it = it + 1
    paren_check(result, 'MATCHING PAREN COMING OUT OF ASCII_TO_SYMPY ')

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
    print("SYMBOLIC DECLASH")
    result = resub.sub(r"gamma", r"variableGamma", expression)
    result = resub.sub(r"beta", r"variableBeta", result)
    result = resub.sub(r"FF", r"variableEffEff", result)
    result = resub.sub(r"ff", r"variableeffeff", result)
    result = resub.sub(r"lambda", r"variableLambda", result)
    result = resub.sub(r"(\W|\A)e\^", r"\1 E^", result)
    result = resub.sub(r"(\W|\A)e\*\*", r"\1 E**", result)
    clashes = [
        {'And': 'localAnd'},
        {'Not': 'localNot'},
        {'div': 'localdiv'},
        {'Or': 'localOr'},
        {'Ge': 'localGe'},
        {'d': 'partial'},
        {'cross': 'crossfunc'},
        {'Transpose': 'localTranspose'},
    ]
    expression = resub.sub(r',', ' ,', expression)
    for clash in clashes:
        key = list(clash.keys())[0]
        if key in expression:
            result = resub.sub(r"(\A|\s|,|\()" + key + "\(", r"\1 " + clash[key] + "(", result)
    result = resub.sub(r' ,', ',', result)
    return result  # }}}
