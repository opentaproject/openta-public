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


class ClonedCompareNumericUnitError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def insertimplicitmultiply(str):
    result = resub.sub(
        r"(?<=[\w)])\s+(?=[(\w])", r" * ", str
    )  # re.sub(r"([a-zA-Z0-9]) ([a-zA-Z0-9])", r"\1*\2", expression)
    result = resub.sub(r"([0-9])([a-zA-Z])", r"\1*\2*", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    return result


def asciiToSympy(expression, varsubs):
    result = expression
    dict = {
        '^': '**',
        #        '_': '',
        #        '.': '',
        #        '[': '',
        #        ']': ''
    }
    # print("asciiToSympy: EXPRESSION = ", expression);

    result = resub.sub(r"\|([^>]+)>\s*<([^|]+)\|", r" KetBra(\1,\2) ", result)
    result = resub.sub(r"\|([^>]+)>([^<]+)<([^|]+)\|", r" KetBra(\1,\2,\3) ", result)
    result = absify(matrixify(braketify(result)))
    result = insertimplicitmultiply(result)
    # result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])",r" * ", result)  #re.sub(r"([a-zA-Z0-9]) ([a-zA-Z0-9])", r"\1*\2", expression)
    # result = resub.sub(r"([0-9])([a-zA-Z])", r"\1*\2*", result)
    # result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    result = resub.sub(r"cross", r"Cross", result)
    result = resub.sub(r"norm", r"Norm", result)
    result = resub.sub(r"dot", r"Dot", result)
    for old, new in dict.items():
        result = result.replace(old, new)
    result = resub.sub(
        r"\]\s*([^\*]\w+)", r"]* 1.0 * \1", result
    )  # PUT IN IMPLICITY MULTIPLY IN VARIABLE DEFS WITH UNITS
    # print("asciiToSympy: result = ", result )
    return result


def sympyvarsubs(variables):
    # print("FUNCTION ASSOC sympyvarsubs " + str(variables) )
    sym = {}
    subs = {}
    # Decode JSON string into python lists/dictionaries
    # Declare new sympy symbol for every variable
    for var, value in variables.items():
        # print("var = " + str(var) )
        # print("value = " + str(value))
        try:
            sy = sympy.symbols(var)
            su = N(sympy.sympify(asciiToSympy(value, {}), ns))  # _clash)
            sym[var] = sy
            subs[sym[var]] = su
        except Exception as e:
            # print("BEGIN FAILED IN SYMPYVARSUBS")
            # print(var)
            # print(value)
            # print("END FAIL IN SYMPVARSUBS")
            raise Exception(_("Error subsituting  for variable" + var + " = " + value))

    # print("FUNCTION sympyvarsubs return " + str( subs) )
    return subs


def sympyvarsubs2(variables):
    # print("FUNCTION ASSOC sympyvarsubs " + str(variables) )
    sym = {}
    subs = {}
    # Decode JSON string into python lists/dictionaries
    # Declare new sympy symbol for every variable
    for var, value in variables.items():
        # print("var = " + str(var) )
        # print("value = " + str(value))
        sym[var] = sympy.symbols(var)
        subs[var] = N(sympy.sympify(asciiToSympy(value, {}), ns))  # _clash)
    # print("FUNCTION sympyvarsubs return " + str( subs) )
    return subs


def to_latex(expression):
    latex = ""
    try:
        # latex = sympy.latex(sympy.sympify(asciiToSympy(expression), ns))#_clash))
        latex = " RESTORE FUNCTIONALITY IN cloned_compare_numeric"
    except SympifyError as e:
        print(e)
        latex = "error"
    return latex


def sanitize(prefix, string):
    print("sanitize" + string)
    res = string
    if "Error" in res:
        res = "illegal expression"
    # res = resub.sub(r"<class *.sympy.core.numbers.*","scalar",res)
    res = resub.sub(r"<class \'sympy.core.[^>]*>", "scalar", res)
    # res = resub.sub(r"<class \'sympy.core.mul.Mul\'>","scalar",res)
    res = resub.sub(r"<class \'sympy.matrices.immutable.ImmutableMatrix\'>", "matrix", res)
    res = resub.sub(r"<class *\'int\'>", "scalar", res)
    res = resub.sub(r"<class *\'float\'>", "scalar", res)
    res = resub.sub(r"<class *\'Symbol\'>", "symbol", res)
    res = resub.sub(r"shape *\( *\)", "scalar ", res)
    res = resub.sub(r"shape *\([0-9]+, *1\)", "vector", res)
    res = resub.sub(r"shape *\([0-9]+, [0-9]+\)", "matrix", res)
    res = resub.sub(r"matrix", "vector or matrix", res)
    res = resub.sub(r"and", "to", res)
    # res = resub.sub(r"as_base_([\w\(\)]+).*",r"error: \1",res)
    res = resub.sub(r"as_base_exp\(\).*", r"error: function without argument?", res)
    res = resub.sub(r"eval\(\)([^:]*):.*", r"\1", res)
    res = resub.sub(r"\<", "LEFTBRACKET", res)
    res = resub.sub(r"\>", "RIGHTBRACKET", res)
    print("return " + prefix + "  " + res)
    return prefix + ': ' + res


class Norm(Function):
    # nargs = (1,2)
    @classmethod
    def eval(cls, x):
        # print("Norm Function" )
        # print("x = ", x )
        if isinstance(x, ImmutableMatrix):
            res = x.norm()
            # print("RESULT IS")
            # print( res )
            return res
        else:
            print("ILLEGAL TYPES IN NORM")
            print(type(x))
            print(type(y))


class isEqual(Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        # print("Cross Function" )
        # print("x = ", x )
        # print("y = ", y )
        res = 1 if x.equals(y) else 0
        # print("RESULT IS")
        # print( res )
        return res


#
class isLE(Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        # print("Cross Function" )
        # print("x = ", x )
        # print("y = ", y )
        res = 1 if (x <= y) else 0
        # print("RESULT IS")
        # print( res )
        return res


#
# class isLT(Function):
#        nargs = (1,2)
#        @classmethod
#        def eval(cls, x,y):
#            #print("Cross Function" )
#            #print("x = ", x )
#            #print("y = ", y )
#            res =  1 if ( x < y )   else 0
#            #print("RESULT IS")
#            #print( res )
#            return res
#
#
# class isGT(Function):
#        nargs = (1,2)
#        @classmethod
#        def eval(cls, x,y):
#            #print("Cross Function" )
#            #print("x = ", x )
#            #print("y = ", y )
#            res =  1 if ( x > y  )  else 0
#            #print("RESULT IS")
#            #print( res )
#            return res
#

#
# class isGE(Function):
#        nargs = (1,2)
#        @classmethod
#        def eval(cls, x,y):
#            #print("Cross Function" )
#            #print("x = ", x )
#            #print("y = ", y )
#            res =  1 if ( x >= y )   else 0
#            #print("RESULT IS")
#            #print( res )
#            return res
#


class isNotEqual(Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        # print("Cross Function" )
        # print("x = ", x )
        # print("y = ", y )
        res = 0 if x.equals(y) else 1
        # print("RESULT IS")
        # print( res )
        return res


class Not(Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, x):
        # print("Cross Function" )
        # print("x = ", x )
        # print("y = ", y )
        if x == 0:
            res = 1
        else:
            res = 0
        return res

        # print("RESULT IS")
        # print( res )
        return res


class Cross(Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        # print("Cross Function" )
        # print("x = ", x )
        # print("y = ", y )
        if isinstance(x, ImmutableMatrix) and isinstance(x, ImmutableMatrix):
            res = x.cross(y)
            # print("RESULT IS")
            # print( res )
            return res
        else:
            print("ILLEGAL TYPES IN CROSS")
            print(type(x))
            print(type(y))


class Dot(Function):
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        # print("Dot Function" )
        # print("x = ", x )
        # print("y = ", y )
        if isinstance(x, ImmutableMatrix) and isinstance(y, ImmutableMatrix):
            res = x.dot(y)
            # print("RESULT IS")
            # print( res )
            return res
        else:
            print("ILLEGAL TYPES IN DOT")
            print(type(x))
            print(type(y))


class Braket(Function):
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            return conjugate(x).T.dot(m)
        else:
            return conjugate(x).T.dot(m * y[0])
        # print("Braket Function" )
        # print("x = ", x )
        # print("y = ", y )
        # if ( isinstance(x, ImmutableMatrix  ) and isinstance(y, ImmutableMatrix )):
        #    res = x.T.dot( m * y)
        #    #print("RESULT IS")
        #    #print( res )
        #    return res
        # else:
        #    print("ILLEGAL TYPES IN DOT")
        #    print( type(x) )
        #    print( type(y) )


class KetBra(Function):
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            return x * conjugate(m).T
        else:
            return x * m * conjugate(y[0].T)
        # print("Braket Function" )
        # print("x = ", x )
        # print("y = ", y )
        # if ( isinstance(x, ImmutableMatrix  ) and isinstance(y, ImmutableMatrix )):
        #    res = x.T.dot( m * y)
        #    #print("RESULT IS")
        #    #print( res )
        #    return res
        # else:
        #    print("ILLEGAL TYPES IN DOT")
        #    print( type(x) )
        #    print( type(y) )


def matrixify(str):  # PUT A MATRIX( ) around outer square brackets
    l = len(str)
    i = 0
    s = ''
    # print("STR1 = ",str)
    depth = 0
    while i < l:
        c = str[i]
        if c == '[':
            if depth == 0:
                s += "Matrix("
            depth -= 1
        if c == ']':
            depth += 1
        # print( i,c, depth, s )
        s += str[i]
        if c == ']' and depth == 0:
            s += ")"
        i += 1
    return s


def absify(str):
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
        return sstr


def braketify(str):
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
    return s


def cloned_compare_numeric_internal(variables, expression1, expression2):  # {{{
    print("FUNCTION cloned_compare_numeric_internal variables" + str(variables))
    print("expression1 = " + str(expression1))
    print("expression2 = " + str(expression2))
    response = {}
    # Do some initial formatting
    # THIS SECTION SHOULD NOT BE NECESSARY  SINCE ILLEGAL CHARACTES SHOULD BE CAUGHT BY cloned_compare_numeric
    invalid_strings = ['_', '.', '[', ']']
    invalid_strings = ['_']
    invalid_strings = ['_', '#', '&', '$']
    for i in invalid_strings:
        if i in expression1:
            raise Exception(_("ILLEGAL CHARACTER " + i))
    #########################################################
    try:
        # Parse variables into substitution dictionary
        # varsubs = parse_variables(variables)
        # print("FUNCTION INTERNAL varsubs = " + str( varsubs) )
        try:
            varsubs = sympyvarsubs(variables)
            varstonumeric = {k: v.subs(uniteval) for k, v in varsubs.items()}
        except Exception as e:
            print("Caught:  " + str(e))
            response['warning'] = str(e)
            return response
        print("FUNCTION INTERNAL varsubs = " + str(varsubs))
        # print("FUNCTION INTERNAL nvarsubs = " + str( nvarsubs) )
        nvars = {}
        # substitution = ""
        for var, value in varsubs.items():
            print("var = ", var)
            print("value = ", value)
            nvars[var] = sympy.sympify(
                (value.subs(uniteval)).evalf()
            )  # XXXX should have a float around it
            # substitution = substitution + str(var) + "=" + str( nvars[var] ) +";"
        print("nvars = ", nvars)
        # print("died")
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.

        print("VARSUBS = ")
        print(varsubs)
        varsubs2 = sympyvarsubs2(variables)
        nscomplete = varsubs2.copy()
        # nscomplete.update(uniteval)
        nscomplete.update(ns)
        nscomplete['Cross'] = Cross
        nscomplete['Dot'] = Dot
        nscomplete['Norm'] = Norm
        nscomplete['isEqual'] = isEqual
        # nscomplete['isGT'] = isGT
        # nscomplete['isLT'] = isLT
        # nscomplete['isGE'] = isGE
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
        print("NSCOMPLETE = ")
        print(nscomplete)
        try:
            lhs = None
            lhsrhs = expression2.split("===")
            if len(lhsrhs) == 2:
                lhs = insertimplicitmultiply(lhsrhs[0])
                expression2 = lhsrhs[1]
                print("lhs = ", lhs)
        except Exception as e:
            print(e)

        try:
            print("SEXPRESSION1")
            sexpression1 = asciiToSympy(expression1, varsubs)
            print(sexpression1)
            print("sympy1")
            sympy1 = sympy.sympify(sexpression1, nscomplete).subs(varsubs)
            print(sympy1)
        except Exception as e:
            print("sympy1 failed: ERROR = ")
            w = sanitize('Q ', str(e))
            print(w)
            logger.error([str(e), expression1, expression2])
            # response['error'] = sanitize('7', _("Error in attempt: "+expression1+"  "+ str(e)) )
            # response['warning'] = "EXPRESSION " + expression1 + " failed "
            response['warning'] = w
            return response

        try:
            print("SEXPRESSION2")
            sexpression2 = asciiToSympy(expression2, varsubs)
            print(sexpression2)  # PUT A MATRIX( ) around outer square brackets
            sympy2 = sympy.sympify(sexpression2, nscomplete).subs(varsubs)
            s2 = sympy.sympify(sexpression2)
            print("sympy2")
            print(sympy2)
        except Exception as e:
            logger.error([str(e), expression2, expression2])
            # print("GOT A PARSING ERROR HERE IN  " + expression2)
            # try:
            #         response['warning'] = sanitize('8', _("Error in facit: "+expression2+"  "+ str(e)) )
            # except Exception as e:
            response['warning'] = (
                "parsing error in \'"
                + expression2
                + "\'  "
                + sanitize('E8', _("Error in facit: " + str(e)))
            )

            return response
        tvars = tuple(varsubs.keys())
        # print("tvars = ");
        # print(tvars)
        try:
            s1sub = sympy1  # .subs(uniteval) #.subs(nvars).evalf()
            if not (lhs is None):
                print("AGAIN: LHS = ", lhs)
                sympy1c = sympy.sympify(sexpression1, nscomplete).subs(varsubs).subs(uniteval)
                print("SYMPY1C = ", sympy1c)
                nscomplete['ans'] = sympy1c
                s1sub = sympy.sympify(lhs, nscomplete).subs(varsubs)
                s1 = sympy.sympify(lhs).subs({'ans': sympy1c})
                s1 = sympy.sympify(sexpression1)
                print("S1SUB = ")
                print(s1sub)
            else:
                s1sub = sympy1  # .subs(uniteval) #.subs(nvars).evalf()
                s1 = sympy.sympify(sexpression1)
            s2sub = sympy2
            unitset = set([kg, meter, second])
            free1 = s1sub.free_symbols
            print("TEST EQUALITY BETWEEN")
            print("SYMBOLICALLY s1 = ", s1)  ### THIS IS THE SYMBOLIC STUDENT ANSWER
            print("SYMBOLICALLY s2 = ", s2)  ### THIS IS THE SYMBOLIC CORRECT ANSWER
            print("S1SUB = ", s1sub)  ### UNITFULL STUDENT WRAPPED ANSWER
            print("S2SUB = ", s2sub)  ### UNITFULL CORRECT ANSWER
            print(
                "NUMERICALLY s1 = ", s1sub.subs(uniteval)
            )  ## THIS IS THE  STUDENT ANSWER WRAPPED BY LHS
            print("NUMERICALLY s2 = ", s2sub.subs(uniteval))  ## THIS IS NUMERICALLY CORRECT ANSWER
            undefs = free1.difference(unitset)
            # print("UNDEFS = ")
            # print(undefs)
            if len(undefs) > 0:
                response['warning'] = 'Undefined symbols: ' + str(list(undefs))
                return response
            m1 = isinstance(s1sub, ImmutableMatrix) or isinstance(s1sub, MutableDenseMatrix)
            m2 = isinstance(s2sub, ImmutableMatrix) or isinstance(s2sub, MutableDenseMatrix)
            iseq = s1sub.subs(uniteval).equals(s2sub.subs(uniteval))
            # iseq = s1sub.equals( s2sub)
            print("ISEQ", iseq)
            if iseq == None:
                response['warning'] = 'unparsable'
                return response
            s1s2 = str(s1sub) + str(s2sub)
            hasunits = 'kg' in s1s2 or 'second' in s1s2 or 'meter' in s1s2
            if hasunits and not iseq:
                # print("TYPES")
                # print(type( s1sub) )
                # print(type( s2sub) )
                if m1 and m2:
                    mag1 = trace(s1sub * s1sub.T)
                    mag2 = trace(s2sub * s2sub.T)
                else:
                    mag1 = s1sub * s1sub
                    mag2 = s2sub * s2sub
                rat = sympy.simplify(mag1 / mag2)
                # print( mag1)
                # print( mag2)
                # print(rat)
                free = rat.free_symbols
                # print( free )
                if len(free) == 0:
                    print("UNITS WORK OUT")
                else:
                    mag1str = str(mag1)
                    pluscount = len(resub.findall(r"[+-]", mag1str))
                    # print("PLUSCOUNT = ", pluscount)
                    # kgcount = len( mag1str.split('kg') )
                    # metercount = len( mag1str.split('meter') )
                    # secondcount = len( mag1str.split('second') )
                    # response['warning'] = "incorrect units"  # + mag1str
                    print("UNITS NOT OK")
                    # print(metercount)
                    # print(kgcount)
                    # print(secondcount)
                    # if metercount > 2 or kgcount > 2 or secondcount > 2 :
                    response['warning'] = 'incorrect units'
                    if pluscount > 0:
                        response['warning'] = "inconsistent units"

        except Exception as e:
            print("UNEXPECTED ERROR IN TEST EQUALITY BETWEEN")
            print(s1sub)
            print(s2sub)
            print(type(s1sub))
            print(type(s2sub))
            response['warning'] = sanitize(
                "E5", "Cannot compare " + str(type(s1sub)) + " and " + str(type(s2sub))
            )
            # response['warning'] = "AB C"
            response['correct'] = False
            return response
        # print("iseq = ")
        # print(iseq)
        # response['correct'] = iseq
        if iseq:
            # response['error'] = 'NUMERICAL DIFFERENCE'
            response['correct'] = True
        else:
            # print( s1sub)
            # print( s2sub)
            response['correct'] = False
        # print("RESPONSE = ")
        # print(response)
        return response
    except Exception as e:
        print("UNCAUGHT ERROR")
        response['warning'] += 'UNCAUGHT ERROR: ' + +sanitize('G', e)
        return response


def cloned_compare_numeric_runner(variables, expression1, expression2, q):
    response = cloned_compare_numeric_internal(variables, expression1, expression2)
    # print("RUNNER RESPONSE = ")
    # rint(response)
    q.put(response)


def cloned_compare_numeric_runner_pool(variables, expression1, expression2):
    return cloned_compare_numeric_internal(variables, expression1, expression2)


def cloned_compare_numeric_pool(variables, expression1, expression2):  # {{{
    """
    Starts a process with cloned_compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Pool. This can be used instead of the implementation with Process with less code but with less control over termination.
    """
    # invalid_strings = ['_', '.', '[', ']']
    # invalid_strings = ['_','#','&','$']
    # for i in invalid_strings:
    #    if i in expression1:
    #        return {'error': _('FROM POOL INVALID CHARACTER') + i }
    with Pool(processes=1) as pool:
        result = pool.apply_async(
            cloned_compare_numeric_runner, (variables, expression1, expression2)
        )
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


def cloned_compare_numeric(variables, expression1, expression2):
    """
    Starts a process with cloned_compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    # print("FUNCTION MAP cloned_compare_numeric variables" + str( variables) );
    # print("FUNCTION cloned_compare_numeric variables" + str( variables) );
    # THIS THROWS AN EXCEPTION WHEN FOR ILLEGAL CHARCTER AND PASSES TO POOL
    invalid_strings = ['_', '[', ']']
    invalid_strings = ['_']
    invalid_strings = ['_', '#', '&', '$']
    for i in invalid_strings:
        if i in expression1:
            raise Exception(_("E2-illegal character " + i))
            return {'error': _('1-Answer contains invalid character ') + i}
    # print(cloned_compare_numeric_internal(variables, expression1, expression2))
    q = Queue()
    p = Process(target=cloned_compare_numeric_runner, args=(variables, expression1, expression2, q))
    p.start()
    try:
        starttime = time.perf_counter()
        response = q.get(True, 6)
        timedelta = time.perf_counter() - starttime
        # logger.info("cloned_compare_numeric took " + str(timedelta) + 's [' + expression1 + ', ' + expression2 + '] \n  and variables \n ' + json.dumps(variables))
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
