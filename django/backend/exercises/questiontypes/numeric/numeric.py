import sympy
import numpy
from sympy.abc import _clash1, _clash2, _clash

# from sympy.physics.units import *
from math import log10, floor
import json
import re
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
from multiprocessing import Queue, Process, Pool, TimeoutError
from exercises.questiontypes.safe_run import safe_run
from queue import Empty
import time
import logging

logger = logging.getLogger(__name__)

meter, second, kg, ampere, kelvin, mole, candela = sympy.symbols(
    'meter,second,kg,ampere,kelvin,mole,candela ', real=True, positive=True
)
ns = {}
ns.update(_clash)
ns.update(
    {
        'meter': meter,
        'second': second,
        'kg': kg,
        'ampere': ampere,
        'kelvin': kelvin,
        'mole': mole,
        'candela': candela,
        'pi': sympy.pi,
        'ff': sympy.Symbol('ff'),
        'FF': sympy.Symbol('FF'),
    }
)

derivedunits = {
    'joule': kg * meter ** 2 / second ** 2,
    'N': kg * meter ** 2 / second ** 2,
    'coulomb': ampere * second,
    'volt': kg * meter ** 2 / second ** 3 / ampere,
}

baseunits = {meter: 1, second: 1, kg: 1, ampere: 1, kelvin: 1, mole: 1, candela: 1}

lambdifymodules = ["numpy", {'cot': lambda x: 1.0 / numpy.tan(x)}]


class NumericUnitError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def asciiToSympy(expression):
    dict = {
        '^': '**',
        #        '_': '',
        #        '.': '',
        #        '[': '',
        #        ']': ''
    }
    result = re.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression)
    result = re.sub(r"(\W*[0-9]+)([A-Za-z]+)", r"\1 * \2", result)
    result = re.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    result = re.sub(
        r"([0-9])\.([^0-9])", r"\1.0 \2", result
    )  # strip trailing decimal to force integer
    # print("result = ", result )
    for old, new in dict.items():
        result = result.replace(old, new)
    result = result.strip(' \t\n\r')
    return result


def parse_variables(variables):
    sym = {}
    # Decode JSON string into python lists/dictionaries
    vars = variables
    # Declare new sympy symbol for every variable
    for var in vars:
        sym[var['name']] = sympy.symbols(var['name'])
    # Create substituion dictionary
    subs = {}
    for var in vars:
        subs[sym[var['name']]] = sympy.sympify(asciiToSympy(var['value']), ns)  # _clash)
    return subs


def check_units(expression, correct, variables):
    """Check units of expression as compared to correct

    Arguments:
    expression -- sympy expression
    correct -- sympy expression
    variables -- dictionary of variables
    """
    # all_units = {bar:foo for bar,foo in u.__dict__.items() if isinstance(foo, type(u.m))}
    # print("allunits = ", all_units)
    # print("CHECK UNITS" )
    print("CHECK UNITS variables = ", variables)
    evaluated = sympy.simplify(expression.subs(variables))
    print("evaluated ", evaluated)
    evaluatedn = sympy.simplify(expression.subs(variables))
    print("evaluatedn ", evaluatedn)
    print("correct", correct)
    print("correct", sympy.simplify(correct.subs(variables)))
    # evaluatedp = convert_to( sympy.simplify(expression.subs(variables)), [kg,m,s] )
    # print("evaluatedp ", evaluatedp)
    unitsok = False
    if len(evaluated.as_terms()[0]) > 1:
        raise NumericUnitError(_("Terms do not seem to have the same unit."))
    ceval = sympy.simplify(correct.subs(variables))
    quotient = sympy.simplify(ceval / evaluated)
    # print("u.__dict__")
    # print(u.__dict__)
    # print("u.__dict__",u.__dict__.items())
    # print("quotient", quotient )
    # print("quotient", quotient.subs(u.__dict__) )
    print("quotient = ", quotient)
    print("NUMERIC len = ", len(list(quotient.free_symbols)))
    unitsok = int(len(list(quotient.free_symbols))) == 0
    print("NUMERIC unitsok = ", unitsok)
    if not (unitsok):
        raise NumericUnitError(_("Seems like the expression does not have the correct units."))
    print("NUMERIC unitsok = ", unitsok)
    return unitsok


def evaluate(variables, expression):
    subs = parse_variables(variables)
    # Parse expression and evaluate with specified values
    value = sympy.sympify(expression).evalf(subs=subs)
    response = {}
    if not value.is_real:
        response['error'] = "Could not parse expression"
    else:
        response['value'] = float(value)
    return json.dumps(response)


def getprecision(e2):
    expression2 = re.sub(
        r"([0-9])\.([^0-9])", r"\1.0 \2", e2
    )  # strip trailing decimal to force integer
    intpart2 = re.search(r"([0-9]*\.[0-9]*)", expression2)
    floatpart = float(1)
    if intpart2 != None:
        floatpart = float(intpart2.group(0))
        # print("GETPRECISION: intpart2", intpart2.group(0) )
        # print("GETPRECISION: floatpart", floatpart )
        digits = re.sub(r"\.", '', intpart2.group(0))
        # print("GETPRECISION digits", digits )
        precision = 2.0 / float(digits)
        precision = round(precision, -int(floor(log10(abs(precision)))))
    else:
        precision = 0
        # print("GETPRECISION: old precision = ", precision )
    # print("GETPRECISION: new precision = ", precision )
    return precision


def numeric_internal(variables, e1, e2, precision):  # {{{
    # Do some initial formatting
    expression1 = re.sub(
        r"([0-9])\.([^0-9])", r"\1.0 \2", e1
    )  # strip trailing decimal to force integer
    expression2 = re.sub(
        r"([0-9])\.([^0-9])", r"\1.0 \2", e2
    )  # strip trailing decimal to force integer
    number_of_points = 10
    response = {}
    print("NUMERIC_INTERRNA variables = ", variables)
    # print("INTERNAL: precision = ", precision )
    try:
        sexpression1 = asciiToSympy(expression1)
        # print("sexpression1 = ", sexpression1 )
        sexpression2 = asciiToSympy(expression2)
        # print("sexpression2 = ", sexpression2 )
        # Parse variables into substitution dictionary
        varsubs = parse_variables(variables)
        nvars = {}
        for var, value in varsubs.items():
            # print("var = ", var )
            # print("value = ", value )
            nvars[var] = value
        neighbours = []
        random.seed(1)
        # print("nvars=", nvars )
        # for i in range(0,number_of_points):
        #    neighbour = []
        #    for var, value in nvars.items():
        #        neighbour.append(value + random.random() * value * 0.1 + 0j)
        #    neighbours.append(neighbour)
        #    if logger.isEnabledFor(logging.DEBUG):
        #        varvals = list(map(lambda x: str(x[0]) + ':' + str(x[1]), zip(nvars.keys(), neighbour)))
        #        logger.debug('Neighbour point: ' + str(varvals))

        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        sympy1 = sympy.sympify(sexpression1, ns).subs(derivedunits)
        sympy2 = sympy.sympify(sexpression2, ns).subs(derivedunits)
        print("sympy1=", sympy1)
        print("sympy2=", sympy2)
        print("variables =", variables)
        # intpart = re.sub(r"([0-9])*\.([0-9]*).*",r"BEGIN#\1\2#END",expression2)
        # intpart = re.sub(r"^[^#]*#",r"",intpart)
        # intpart = re.sub(r"#.*$",r"",intpart)
        # print("inpart = ", intpart )
        # print("expression2 = ", expression2 )
        if float(precision) == float(0):
            precision = getprecision(expression2)
        # floatpart = prec[1];
        # print("new precision = ", precision )
        if isinstance(sympy1, sympy.Basic):
            atoms = sympy1.atoms(sympy.Symbol, sympy.Function)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                # if strrep in blacklist:
                #    return {'error': _('Forbidden token: ') + strrep}
                # if funcstr in blacklist:
                #    return {'error': _('Forbidden token: ') + funcstr}
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Expression 1: ' + str(sympy1))
            logger.debug('Expression 2: ' + str(sympy2))
        tvars = tuple(nvars.keys())
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Lambdify order: ' + str(tvars))
        # numfunc1 = sympy.lambdify(tvars, sympy1, modules=lambdifymodules)
        # numfunc2 = sympy.lambdify(tvars, sympy2, modules=lambdifymodules)
        value1 = sympy1.subs(varsubs).subs(baseunits).evalf()
        value2 = sympy2.subs(varsubs).subs(baseunits).evalf()
        # print("sympy1, value1 = ", sympy1, value1)
        # print("sympy2, value2 = ", sympy2, value2.subs(baseunits) )
        # diff = sympy.Abs( ( value1/value2 - 1.0 ) * floatpart * .999)
        diff = sympy.Abs((value1 / value2 - 1.0))
        print("diff = ", diff)
        print("precision = ", precision)
        # print("baseunits = ", baseunits)
        # print("value1 = ", value1)
        # print("value2 = ", value2)
        print("varsubs = ", varsubs)
        unitsok = False
        if diff.is_constant():
            print("NUMERIC2 unitsok ", unitsok)
            try:
                unitsok = check_units(sympy1, sympy2, varsubs)
                print("NUMERIC5 unitsok ", unitsok)
            except NumericUnitError as e:
                print("NUMERIC6 unitsok ", unitsok)
                unitsok = False
                response['warning'] = str(e)
            except ZeroDivisionError as e:
                unitsok = False
                print("NUMERIC7 unitsok ", unitsok)
                response['zerodivision'] = True
            print("NUMERIC3 unitsok ", unitsok)
            # diffs = []
            # for point in neighbours:
            #    nvalue1 = numfunc1(*point)#sympy1.subs(point).subs(baseunits).evalf()
            #    nvalue2 = numfunc2(*point)#sympy2.subs(point).subs(baseunits).evalf()
            #    ndiff = numpy.absolute(nvalue2 - nvalue1)
            #    diffs.append(float(ndiff) < 1e-6)
            # if diffs.count(True) >= number_of_points*0.8:
            if float(precision) != 0:
                response['precision'] = " [ precision " + str(precision) + " erfodras ]"
            else:
                response['precision'] = " [ exakt svar erfodras ]  "
            if diff <= float(precision) and unitsok:
                response['correct'] = True
            else:
                response['correct'] = False
        else:
            unrecognised = ', '.join(list(map(str, diff.free_symbols)))
            response['error'] = _("Failed to evaluate expression")
            if len(unrecognised) > 0:
                response['error'] = (
                    response['error'] + ': ' + unrecognised + _(' are not valid variables.')
                )
    except SympifyError as e:
        logger.error([str(e), expression1, expression2])
        response['error'] = _("Failed to evaluate expression.")
    except Exception as e:
        logger.error([str(e), expression1, expression2])
        response['error'] = _("Unknown error, check your expression.")
    return response  # }}}


def numeric_runner(variables, expression1, expression2, precision, result_queue):
    # print("RUNNER - precision ", precision )
    response = numeric_internal(variables, expression1, expression2, precision)
    result_queue.put(response)


def numeric(variables, expression1, expression2, precision):
    """
    Starts a process with numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    # print("CLONED_COMPARE_NUMERIC precision = ", precision)
    invalid_strings = ['_', '[', ']']
    for i in invalid_strings:
        if i in expression1:
            return {'error': _('Answer contains invalid character ') + i}
    return safe_run(numeric_runner, args=(variables, expression1, expression2, precision))


def to_latex(expression):
    latex = ""
    try:
        latex = sympy.latex(sympy.sympify(asciiToSympy(expression), ns))  # _clash))
    except SympifyError as e:
        print(e)
        latex = "error"
    return latex
