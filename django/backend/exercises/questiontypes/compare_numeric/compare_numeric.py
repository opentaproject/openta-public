import sympy
import numpy
from sympy.abc import _clash1, _clash2, _clash
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


class CompareNumericUnitError(Exception):
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


def check_units(expression, correct, variables):
    """Check units of expression as compared to correct

    Arguments:
    expression -- sympy expression
    correct -- sympy expression
    variables -- dictionary of variables
    """
    evaluated = sympy.simplify(expression.subs(variables))
    if len(evaluated.as_terms()[0]) > 1:
        raise CompareNumericUnitError(_("Terms do not seem to have the same unit."))
    ceval = sympy.simplify(correct.subs(variables))
    quotient = sympy.simplify(ceval / evaluated)
    if len(list(quotient.free_symbols)) > 0:
        raise CompareNumericUnitError(
            _("Seems like the expression does not have the correct units.")
        )


def check_units_new(expression, correct, variables):
    if numpy.absolute(correct) == 0.0:
        return
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
            raise CompareNumericUnitError(
                _("Seems like the expression does not have the correct units.")
            )
    # print(lexpr(*nvalues, 1,1,1))
    # for i in range(0, 3):
    #    for var,value in variables:
    # check_dependence(expression, kg)


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


def compare_numeric_internal(variables, expression1, expression2, blacklist=[]):  # {{{
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
        if isinstance(sympy1, sympy.Basic):
            atoms = sympy1.atoms(sympy.Symbol, sympy.Function)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {'error': _('Forbidden token: ') + strrep}
                if funcstr in blacklist:
                    return {'error': _('Forbidden token: ') + funcstr}
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


def compare_numeric_runner(variables, expression1, expression2, blacklist, result_queue):
    response = compare_numeric_internal(variables, expression1, expression2, blacklist)
    result_queue.put(response)


def compare_numeric(variables, expression1, expression2, blacklist):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_', '[', ']']
    for i in invalid_strings:
        if i in expression1:
            return {'error': _('Answer contains invalid character ') + i}
    return safe_run(compare_numeric_runner, args=(variables, expression1, expression2, blacklist))


def to_latex(expression):
    latex = ""
    try:
        latex = sympy.latex(sympy.sympify(asciiToSympy(expression), ns))  # _clash))
    except SympifyError as e:
        print(e)
        latex = "error"
    return latex
