import sympy
import numpy
from sympy.abc import _clash1, _clash2, _clash
import json
import re as resub
from sympy.core.sympify import SympifyError
from sympy import *
from sympy import I, Trace
from django.utils.translation import ugettext as _
import traceback
import random
from multiprocessing import Queue, Process, Pool, TimeoutError
from queue import Empty
import time
import logging
import pprint
from sympy import Function

logger = logging.getLogger(__name__)

meter, second, kg = sympy.symbols('meter,second,kg', real=True, positive=True)
ns = {}
ns.update(_clash)
ns.update(
    {
        'meter': meter,
        'second': second,
        'kg': kg,
        'pi': sympy.pi,
        'ff': sympy.Symbol('ff'),
        'FF': sympy.Symbol('FF'),
    }
)

uniteval = {meter: random.random(), second: random.random(), kg: random.random()}

lambdifymodules = [
    "numpy",
    "sympy",
    {
        'cot': lambda x: 1.0 / numpy.tan(x),
        'Dot': lambda x, y: float(x.dot(y)),  # dot GETS REWRITTEN IN asciiToSympy
        'Cross': lambda x, y: x.cross(y),
    },
]


class linalgebraUnitError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def insertimplicitmultiply(str):  # {{{
    result = resub.sub(
        r"(?<=[\w)])\s+(?=[(\w])", r" * ", str
    )  # re.sub(r"([a-zA-Z0-9]) ([a-zA-Z0-9])", r"\1*\2", expression)
    result = resub.sub(r"([0-9])([a-zA-Z])", r"\1*\2*", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    result = resub.sub("\)([A-Za-z0-9]+)", r") * \1 ", result)
    return result  # }}}


def asciiToSympy(expression, varsubs):  # {{{
    result = expression
    result = resub.sub(r"([^=]+)==([^=]+)", r"(\1) - ( \2)", result)
    dict = {'^': '**'}

    result = resub.sub(r"\|([^>]+)>\s*<([^|]+)\|", r" KetBra(\1,\2) ", result)
    result = resub.sub(r"\|([^>]+)>([^<]+)<([^|]+)\|", r" KetBra(\1,\2,\3) ", result)
    result = absify(matrixify(braketify(result)))
    result = insertimplicitmultiply(result)
    result = resub.sub(r"cross", r"Cross", result)
    result = resub.sub(r"norm", r"Norm", result)
    result = resub.sub(r"dot", r"Dot", result)
    result = declash(result)
    for old, new in dict.items():
        result = result.replace(old, new)
    result = resub.sub(
        r"\]\s*([^\*]\w+)", r"]* 1.0 * \1", result
    )  # PUT IN IMPLICITY MULTIPLY IN VARIABLE DEFS WITH UNITS
    return result  # }}}


def declash(str):  ### RIDICULOUS beta and gamma are defined as functions# {{{
    result = resub.sub(r"gamma", r"Gamma", str)
    result = resub.sub(r"beta", r"Beta", result)
    result = resub.sub(r"FF", r"variableFF", result)
    result = resub.sub(r"ff", r"variableff", result)
    result = resub.sub(r"lambda", r"variablelambda", result)

    return result  # }}}


def sympyvarsubs(variables):  # {{{
    sym = {}
    subs = {}
    # Decode JSON string into python lists/dictionaries
    # Declare new sympy symbol for every variable
    for var, value in variables.items():
        try:
            avar = declash(var)
            sy = sympy.symbols(avar)
            su = N(sympy.sympify(asciiToSympy(value, {}), ns))  # _clash)
            sym[avar] = sy
            subs[sym[avar]] = su
        except Exception as e:
            raise Exception(_("Error subsituting  for variable" + var + " = " + value))

    return subs  # }}}


def sympyvarsubs2(variables):  # {{{
    sym = {}
    subs = {}
    # Decode JSON string into python lists/dictionaries
    # Declare new sympy symbol for every variable
    for var, value in variables.items():
        avar = declash(var)
        sym[avar] = sympy.symbols(avar)
        subs[avar] = N(sympy.sympify(asciiToSympy(value, {}), ns))  # _clash)
    return subs  # }}}


def to_latex(expression):  # {{{
    latex = ""
    try:
        latex = " RESTORE FUNCTIONALITY IN linalgebra"
    except SympifyError as e:
        print(e)
        latex = "error"
    return latex  # }}}


def sanitize(prefix, string):  # {{{
    res = string
    if "Error" in res:
        res = "illegal expression"
    res = resub.sub(r"<class \'sympy.core.[^>]*>", "scalar", res)
    res = resub.sub(r"<class \'sympy.matrices.immutable.ImmutableMatrix\'>", "matrix", res)
    res = resub.sub(r"<class *\'int\'>", "scalar", res)
    res = resub.sub(r"<class *\'float\'>", "scalar", res)
    res = resub.sub(r"<class *\'Symbol\'>", "symbol", res)
    res = resub.sub(r"shape *\( *\)", "scalar ", res)
    res = resub.sub(r"shape *\([0-9]+, *1\)", "vector", res)
    res = resub.sub(r"shape *\([0-9]+, [0-9]+\)", "matrix", res)
    res = resub.sub(r"matrix", "vector or matrix", res)
    res = resub.sub(r"and", "to", res)
    res = resub.sub(r"as_base_exp\(\).*", r"error: function without argument?", res)
    res = resub.sub(r"eval\(\)([^:]*):.*", r"\1", res)
    res = resub.sub(r"\<", "LEFTBRACKET", res)
    res = resub.sub(r"\>", "RIGHTBRACKET", res)
    print("return " + prefix + "  " + res)
    return prefix + ': ' + res  # }}}


class Norm(Function):  # {{{
    @classmethod
    def eval(cls, x):
        if isinstance(x, ImmutableMatrix):
            res = x.norm()
            return res
        else:
            return Abs(x)
            print("ILLEGAL TYPES IN NORM")
            print(type(x))
            print(type(y))  # }}}


class isEqual(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        res = 1 if x.equals(y) else 0
        return res  # }}}


class isLE(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        res = 1 if (x <= y) else 0
        return res  # }}}


class isLT(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        res = 1 if (x < y) else 0
        return res  # }}}


class isGT(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        res = 1 if (x > y) else 0
        return res  # }}}


class isGE(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        res = 1 if (x >= y) else 0
        return res  # }}}


class isNotEqual(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        res = 0 if x.equals(y) else 1
        return res  # }}}


class Not(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x):
        if x == 0:
            res = 1
        else:
            res = 0
        return res  # }}}


class Cross(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, ImmutableMatrix) and isinstance(x, ImmutableMatrix):
            res = x.cross(y)
            return res
        else:
            print("ILLEGAL TYPES IN CROSS")
            print(type(x))
            print(type(y))  # }}}


class Dot(Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, ImmutableMatrix) and isinstance(y, ImmutableMatrix):
            res = x.dot(y)
            return res
        else:
            print("ILLEGAL TYPES IN DOT")
            print(type(x))
            print(type(y))  # }}}


class Braket(Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            return conjugate(x).T.dot(m)
        else:
            return conjugate(x).T.dot(m * y[0])  # }}}


class KetBra(Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            return x * conjugate(m).T
        else:
            return x * m * conjugate(y[0].T)  # }}}


class nullrank(Function):  # {{{
    nargs = 2

    @classmethod
    def eval(cls, zmat, mvars):
        global varstonumeric  # MAKE THIS CLASS OBJECT INSTEAD
        try:
            subs = varstonumeric
            variables = list(mvars)
            print("norm = ", zmat.subs(subs).norm())
            free1 = list(zmat.subs(subs).free_symbols)
            print("free1 = ", free1)
            if len(free1) > 0:
                return sympify('NONFREE')
            if not (zmat.subs(subs).norm()).equals(0):
                print("DOES IS NOT EQUAL ZERO")
                return sympy.sympify('NONZERO')
            zlist = list(zmat)
            jac = []
            for zrow in zlist:
                row = []
                for var in variables:
                    row.append(diff(zrow, var))
                jac.append(row)
            jacobian = Matrix(jac).subs(subs)
            null = jacobian.nullspace()
            print("FREE = ", free1)
            nullrank = len(null)
            print("NULLRANK RETURNS", nullrank)
            return sympy.sympify(nullrank)
        except Exception as e:
            print("RETURNING 99")
            return sympy.sympify('UKNOWNERROR')  # }}}


def matrixify(str):  # PUT A MATRIX( ) around outer square brackets# {{{
    l = len(str)
    i = 0
    s = ''
    depth = 0
    while i < l:
        c = str[i]
        if c == '[':
            if depth == 0:
                s += "Matrix("
            depth -= 1
        if c == ']':
            depth += 1
        s += str[i]
        if c == ']' and depth == 0:
            s += ")"
        i += 1
    return s  # }}}


def absify(str):  # {{{
    l = len(str)
    i = 0
    s = ''
    # print("STR1 = ",str)
    depth = 0
    while i < l:
        c = str[i]
        if c == '|':
            if depth == 0:
                s += " Norm( "
                depth = -1
            elif depth == -1:
                depth = 0
        else:
            s += str[i]
        if c == '|' and depth == 0:
            s += " ) "
        i += 1
    if depth == 0:
        return s
    else:
        return sstr  # }}}


def braketify(str):  # {{{
    rep = {}
    rep['>'] = ''
    rep['<'] = ''
    rep['|'] = ','
    l = len(str)
    i = 0
    s = ''
    # print("STR1 = ",str)
    depth = 0
    while i < l:
        c = str[i]
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


def isnumericallyequal(n1, n2):  # {{{
    print("n1 = ", n1)
    print("n2 = ", n2)
    yesno = round(Norm(n1 - n2), 6) == 0
    return yesno  # }}}


def internal(variables, expression1, expression2):  # {{{
    global varstonumeric
    response = {}
    invalid_strings = ['_', '#', '&', '$']
    for i in invalid_strings:
        if i in expression1:
            raise Exception(_("ILLEGAL CHARACTER " + i))
    try:
        # Parse variables into substitution dictionary
        try:
            varsubs = sympyvarsubs(variables)
            varstonumeric = {k: v.subs(uniteval) for k, v in varsubs.items()}
        except Exception as e:
            print("Caught:  " + str(e))
            response['warning'] = str(e)
            return response
        nvars = {}
        for var, value in varsubs.items():
            nvars[var] = sympy.sympify(
                (value.subs(uniteval)).evalf()
            )  # XXXX should have a float around it

        varsubs2 = sympyvarsubs2(variables)
        nscomplete = varsubs2.copy()
        nscomplete.update(ns)
        nscomplete['Cross'] = Cross
        nscomplete['Dot'] = Dot
        nscomplete['Norm'] = Norm
        nscomplete['isEqual'] = isEqual
        nscomplete['isLE'] = isLE
        nscomplete['isNotEqual'] = isNotEqual
        nscomplete['Not'] = Not
        nscomplete['Braket'] = Braket
        nscomplete['KetBra'] = KetBra
        nscomplete['Trace'] = numpy.trace
        nscomplete['i'] = I
        nscomplete['pi'] = pi
        nscomplete['exp'] = exp
        nscomplete['abs'] = abs
        nscomplete['nullrank'] = nullrank
        nscomplete['variables'] = varstonumeric
        try:
            lhs = None
            lhsrhs = expression2.split("===")
            if len(lhsrhs) == 2:
                lhs = insertimplicitmultiply(lhsrhs[0])
                expression2 = lhsrhs[1]
                print(" INITIALLY lhs = ", lhs)
        except Exception as e:
            print(e)

        try:
            print("SEXPRESSION1")
            sexpression1 = asciiToSympy(expression1, varsubs)
            sympy1 = sympy.sympify(sexpression1, nscomplete).subs(varsubs)
        except Exception as e:
            print("sympy1 failed: ERROR = ")
            w = sanitize('Q ', str(e))
            print(w)
            logger.error([str(e), expression1, expression2])
            response['warning'] = w
            return response

        try:
            sexpression2 = asciiToSympy(expression2, varsubs)
            sympy2 = sympy.sympify(sexpression2, nscomplete).subs(varsubs)
            s2 = sympy.sympify(sexpression2)
        except Exception as e:
            logger.error([str(e), expression2, expression2])
            print("GOT A PARSING ERROR HERE IN  " + expression2)
            try:
                response['warning'] = sanitize(
                    '8', _("Error in facit: " + expression2 + "  " + str(e))
                )
            except Exception as e:
                response['warning'] = (
                    "parsing error in \'"
                    + expression2
                    + "\'  "
                    + sanitize('E8', _("Error in facit: " + str(e)))
                )
                return response
        tvars = tuple(varsubs.keys())
        try:
            s1sub = sympy1  # .subs(uniteval) #.subs(nvars).evalf()
            if not (lhs is None):
                lhsn = asciiToSympy(lhs, varsubs)
                sympy1c = (
                    sympy.sympify(asciiToSympy(sexpression1, varsubs), nscomplete)
                    .subs(varsubs)
                    .subs(uniteval)
                )
                nscomplete['ans'] = sympy1c
                s1 = sympy.sympify(sexpression1)
                nscomplete['sans'] = s1
                s1sub = sympy.sympify(lhsn, nscomplete).subs(varsubs)
                print("S1SUB = ", type(s1sub), s1sub)
            else:
                s1sub = sympy1  # .subs(uniteval) #.subs(nvars).evalf()
                s1 = sympy.sympify(sexpression1)
            s2sub = sympy2
            unitset = set([kg, meter, second])
            free1 = s1sub.free_symbols
            print("TEST EQUALITY BETWEEN")
            print("SYMBOLICALLY s1 = ", s1)  ### THIS IS THE SYMBOLIC STUDENT ANSWER
            print("SYMBOLICALLY s2 = ", s2)  ### THIS IS THE SYMBOLIC CORRECT ANSWER
            print("S1SUB = ", str(s1sub))  ### UNITFULL STUDENT WRAPPED ANSWER
            print("S2SUB = ", str(s2sub))  ### UNITFULL CORRECT ANSWER
            ns1sub = N(s1sub.subs(uniteval))
            ns2sub = N(s2sub.subs(uniteval))
            print(
                "NUMERICALLY s1 = ", type(ns1sub), str(ns1sub)
            )  ## THIS IS THE  STUDENT ANSWER WRAPPED BY LHS
            print(
                "NUMERICALLY s2 = ", type(ns2sub), str(ns2sub)
            )  ## THIS IS NUMERICALLY CORRECT ANSWER
            if not (lhs is None):
                print("LHS = ", lhs)
            undefs = free1.difference(unitset)
            if len(undefs) > 0:
                response['warning'] = 'Undefined symbols: ' + str(list(undefs))
                return response
            m1 = isinstance(ns1sub, ImmutableMatrix) or isinstance(ns1sub, MutableDenseMatrix)
            m2 = isinstance(ns2sub, ImmutableMatrix) or isinstance(ns2sub, MutableDenseMatrix)
            if m1 == m2:
                print("m1 = m2")
                iseq = isnumericallyequal(ns1sub, ns2sub)
            else:
                response['warning'] = ns1sub
                return response
            print("ISEQ", iseq)
            if iseq == None:
                response['warning'] = 'unparsable'
                return response
            s1s2 = str(s1sub) + str(s2sub)
            hasunits = 'kg' in s1s2 or 'second' in s1s2 or 'meter' in s1s2
            if hasunits and not iseq:
                if m1 and m2:
                    mag1 = trace(s1sub * s1sub.T)
                    mag2 = trace(s2sub * s2sub.T)
                else:
                    mag1 = s1sub * s1sub
                    mag2 = s2sub * s2sub
                rat = sympy.simplify(mag1 / mag2)
                free = rat.free_symbols
                if len(free) == 0:
                    print("UNITS WORK OUT")
                else:
                    mag1str = str(mag1)
                    pluscount = len(resub.findall(r"[+-]", mag1str))
                    print("UNITS NOT OK")
                    response['warning'] = 'incorrect units'
                    if pluscount > 0:
                        response['warning'] = "inconsistent units"

        except Exception as e:
            print("UNEXPECTED ERROR IN TEST EQUALITY BETWEEN")
            if not (lhs is None):
                response['warning'] = sanitize(
                    "E5",
                    "Check LHS syntax: error comparint "
                    + expression1
                    + " and  "
                    + lhs
                    + '==='
                    + expression2,
                )
            else:
                response['warning'] = sanitize(
                    "E5", "Cannot compare " + expression1 + " and  " + expression2
                )
            response['correct'] = False
            return response
        if iseq:
            response['correct'] = True
        else:
            response['correct'] = False
        return response
    except Exception as e:
        print("UNCAUGHT ERROR")
        response['warning'] += 'UNCAUGHT ERROR: ' + +sanitize('G', e)
        return response


def runner(variables, expression1, expression2, q):
    response = internal(variables, expression1, expression2)
    q.put(response)


def runner_pool(variables, expression1, expression2):
    return internal(variables, expression1, expression2)


def pool(variables, expression1, expression2):  # {{{
    """
    Starts a process with internal that will be terminated if it takes too long. This implementation uses multiprocessing.Pool. This can be used instead of the implementation with Process with less code but with less control over termination.
    """
    # invalid_strings = ['_', '.', '[', ']']
    # invalid_strings = ['_','#','&','$']
    # for i in invalid_strings:
    #    if i in expression1:
    #        return {'error': _('FROM POOL INVALID CHARACTER') + i }
    with Pool(processes=1) as pool:
        result = pool.apply_async(runner, (variables, expression1, expression2))
        try:
            response = result.get(1)
            return response
        except TimeoutError:
            logger.error(
                'Sympy timed out with expressions ['
                + expression1
                + ', '
                + expression2
                + '] and variables '
                + json.dumps(variables)
            )
            pool.terminate()
            pool.join()
            return {'error': _('Expression could not be parsed.')}  # }}}


def linalgebra(variables, expression1, expression2):
    """
    Starts a process with internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_', '#', '&', '$']
    for i in invalid_strings:
        if i in expression1:
            raise Exception(_("E2-illegal character " + i))
            return {'error': _('1-Answer contains invalid character ') + i}
    q = Queue()
    p = Process(target=runner, args=(variables, expression1, expression2, q))
    p.start()
    try:
        starttime = time.perf_counter()
        response = q.get(True, 6)
        timedelta = time.perf_counter() - starttime
        p.join(1)
        if p.is_alive():
            p.terminate()
            p.join(1)
        return response
    except Empty as e:
        logger.error(
            'Sympy timed out with expressions ['
            + expression1
            + ', '
            + expression2
            + '] and variables '
            + json.dumps(variables)
        )
        p.terminate()
        p.join(1)
        if p.is_alive():
            logger.error(
                'Sympy process still alive after termination with expressions ['
                + expression1
                + ', '
                + expression2
                + '] and variables '
                + json.dumps(variables)
            )
        return {'error': _('Could not parse expression')}
