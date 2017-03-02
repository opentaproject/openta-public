import sympy
import numpy
from sympy.abc import _clash1, _clash2, _clash
import json
import re
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
from exercises.questiontypes.safe_run import safe_run
import time
import logging

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

uniteval = {meter: 1, second: 1, kg: 1}

lambdifymodules = ["numpy", {'cot': lambda x: 1.0 / numpy.tan(x)}]


class LinearAlgebraUnitError(Exception):
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
    for old, new in dict.items():
        result = result.replace(old, new)
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


def check_units_new(expression, correct, variables):
    nvarsubs = {}
    nvalues = []

    def perturb(value):
        return value + value * random.random() * 0.1 + 0j

    for var, value in variables.items():
        nvarsubs[var] = var * value + 0j
        nvalues.append(1 + random.random() * 0.1 + 0j)
    nexpression = expression.subs(nvarsubs)
    ncorrect = correct.subs(nvarsubs)
    allvars = tuple(variables.keys()) + (kg, meter, second)
    lexpr = sympy.lambdify(allvars, nexpression, modules=lambdifymodules)
    lcorrect = sympy.lambdify(allvars, ncorrect, modules=lambdifymodules)

    checks = [
        [1 + 0j, 1 + 0j, 1 + 0j],
        [perturb(2), 1 + 0j, 1 + 0j],
        [1 + 0j, perturb(2), 1 + 0j],
        [1 + 0j, 1 + 0j, perturb(2)],
    ]
    results = []
    for check in checks:
        args = nvalues + check
        vale = lexpr(*args)
        valc = lcorrect(*args)
        if valc != 0:
            results.append(vale / valc)
        else:
            results.append(vale)
    for res in results:
        if sympy.Abs(res - results[0]) > 10e-5:
            raise LinearAlgebraUnitError(
                _("Seems like the expression does not have the correct units.")
            )


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


def linear_algebra_parse_expression(variables, student_answer, correct_answer):
    return {}


def linear_algebra_parse_condition(variables, condition):
    return {}


def linear_algebra(variables, expression1, expression2):  # {{{
    # Do some initial formatting
    number_of_points = 10
    response = {}
    try:
        sexpression1 = asciiToSympy(expression1)
        sexpression2 = asciiToSympy(expression2)
        # Parse variables into substitution dictionary
        varsubs = parse_variables(variables)
        nvars = {}
        for var, value in varsubs.items():
            nvars[var] = float(value.subs(uniteval)) + 0j
        neighbours = []
        random.seed(1)
        for i in range(0, number_of_points):
            neighbour = []
            for var, value in nvars.items():
                neighbour.append(value + random.random() * value * 0.1 + 0j)
            neighbours.append(neighbour)
            if logger.isEnabledFor(logging.DEBUG):
                varvals = list(
                    map(lambda x: str(x[0]) + ':' + str(x[1]), zip(nvars.keys(), neighbour))
                )
                logger.debug('Neighbour point: ' + str(varvals))

        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        sympy1 = sympy.sympify(sexpression1, ns)
        sympy2 = sympy.sympify(sexpression2, ns)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Expression 1: ' + str(sympy1))
            logger.debug('Expression 2: ' + str(sympy2))
        tvars = tuple(nvars.keys())
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Lambdify order: ' + str(tvars))
        numfunc1 = sympy.lambdify(tvars, sympy1, modules=lambdifymodules)
        numfunc2 = sympy.lambdify(tvars, sympy2, modules=lambdifymodules)

        value1 = sympy1.subs(varsubs).subs(uniteval).evalf()
        value2 = sympy2.subs(varsubs).subs(uniteval).evalf()
        diff = sympy.Abs(value2 - value1)
        if diff.is_constant():
            try:
                check_units_new(sympy1, sympy2, varsubs)
            except CompareNumericUnitError as e:
                response['warning'] = str(e)
            except ZeroDivisionError as e:
                response['zerodivision'] = True
            diffs = []
            for point in neighbours:
                nvalue1 = numfunc1(*point)  # sympy1.subs(point).subs(uniteval).evalf()
                nvalue2 = numfunc2(*point)  # sympy2.subs(point).subs(uniteval).evalf()
                ndiff = numpy.absolute(nvalue2 - nvalue1)
                diffs.append(float(ndiff) < 1e-6)
            if diffs.count(True) >= number_of_points * 0.8:
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


def linear_algebra_expression_runner(variables, expression1, expression2, result_queue):
    response = linear_algebra(variables, expression1, expression2)
    result_queue.put(response)


def linear_algebra_expression(variables, student_answer, correct_answer):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_', '[', ']']
    for i in invalid_strings:
        if i in student_answer:
            return {'error': _('Answer contains invalid character ') + i}
    # print(compare_numeric_internal(variables, expression1, expression2))
    return safe_run(linear_algebra_expression_runner, args=(variables, expression1, expression2))
