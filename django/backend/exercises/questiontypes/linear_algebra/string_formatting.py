"""String conversion functions (Asciimath -> Sympy)

Various functions needed to convert input asciimath into something that sympy can parse with sympify.

"""
import re as resub


def insert_implicit_multiply(expression):  # {{{
    result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression)
    result = resub.sub(r"([0-9])([a-zA-Z])", r"\1*\2*", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    result = resub.sub("\)([A-Za-z0-9]+)", r") * \1 ", result)
    return result  # }}}


def ascii_to_sympy(expression):  # {{{
    result = expression
    result = resub.sub(r"([^=]+)==([^=]+)", r"(\1) - ( \2)", result)
    dict = {'^': '**'}

    result = resub.sub(r"\|([^>]+)>\s*<([^|]+)\|", r" KetBra(\1,\2) ", result)
    result = resub.sub(r"\|([^>]+)>([^<]+)<([^|]+)\|", r" KetBra(\1,\2,\3) ", result)
    result = absify(matrixify(braketify(result)))
    result = insert_implicit_multiply(result)
    # result = resub.sub(r"cross", r"Cross", result)
    # result = resub.sub(r"norm", r"Norm", result)
    # result = resub.sub(r"dot", r"Dot", result)
    # result = declash(result)
    for old, new in dict.items():
        result = result.replace(old, new)
    result = resub.sub(
        r"\]\s*([^\*]\w+)", r"]* 1.0 * \1", result
    )  # PUT IN IMPLICITY MULTIPLY IN VARIABLE DEFS WITH UNITS
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


def declash(expression):  ### RIDICULOUS beta and gamma are defined as functions# {{{
    result = resub.sub(r"gamma", r"Gamma", expression)
    result = resub.sub(r"beta", r"Beta", result)
    result = resub.sub(r"FF", r"variableFF", result)
    result = resub.sub(r"ff", r"variableff", result)
    result = resub.sub(r"lambda", r"variablelambda", result)

    return result  # }}}
