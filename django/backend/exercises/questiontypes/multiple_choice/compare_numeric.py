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
    result = re.sub(
        r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression
    )  # re.sub(r"([a-zA-Z0-9]) ([a-zA-Z0-9])", r"\1*\2", expression)
    result = re.sub(r"([0-9])([a-zA-Z])", r"\1*\2*", result)
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
    nvarsubs = {}
    nvalues = []

    def perturb(value):
        return value + value * random.random() * 0.1

    for var, value in variables.items():
        nvarsubs[var] = var * value
        nvalues.append(1 + random.random() * 0.1)
    nexpression = expression.subs(nvarsubs)
    ncorrect = correct.subs(nvarsubs)
    allvars = tuple(variables.keys()) + (kg, meter, second)
    lexpr = sympy.lambdify(allvars, nexpression, modules=lambdifymodules)
    lcorrect = sympy.lambdify(allvars, ncorrect, modules=lambdifymodules)

    checks = [[1, 1, 1], [perturb(2), 1, 1], [1, perturb(2), 1], [1, 1, perturb(2)]]
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
        if abs(res - results[0]) > 10e-5:
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


def compare_numeric_internal(variables, expression1, expression2):  # {{{
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
            nvars[var] = float(value.subs(uniteval))
        neighbours = []
        random.seed(1)
        for i in range(0, number_of_points):
            neighbour = []
            for var, value in nvars.items():
                neighbour.append(value + random.random() * value * 0.1)
                # neighbour[var] = value + random.random() * value * 0.1
            neighbours.append(neighbour)

        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        sympy1 = sympy.sympify(sexpression1, ns)
        sympy2 = sympy.sympify(sexpression2, ns)
        tvars = tuple(varsubs.keys())

        numfunc1 = sympy.lambdify(tvars, sympy1, modules=lambdifymodules)
        numfunc2 = sympy.lambdify(tvars, sympy2, modules=lambdifymodules)
        # value1 = numfunc1(*nvars.values())#sympy1.subs(varsubs).subs(uniteval).evalf()
        # value2 = numfunc2(*nvars.values())#sympy2.subs(varsubs).subs(uniteval).evalf()
        value1 = sympy1.subs(varsubs).subs(uniteval).evalf()
        value2 = sympy2.subs(varsubs).subs(uniteval).evalf()
        diff = sympy.Abs(value2 - value1)
        # symbolic = sympy.simplify(sympy1-sympy2)
        # response['symbolic_difference'] = str(symbolic)
        if diff.is_constant():
            try:
                # pass
                # start = time.perf_counter()
                check_units_new(sympy1, sympy2, varsubs)
                # new = time.perf_counter()
                # check_units(sympy1, sympy2, varsubs)
                # old = time.perf_counter()
                # print("Old: " + str(old-new) + " New: " + str(new-start))
                # print("Stats")
            except CompareNumericUnitError as e:
                response['warning'] = str(e)
            except ZeroDivisionError as e:
                response['zerodivision'] = True
            diffs = []
            for point in neighbours:
                nvalue1 = numfunc1(*point)  # sympy1.subs(point).subs(uniteval).evalf()
                nvalue2 = numfunc2(*point)  # sympy2.subs(point).subs(uniteval).evalf()
                ndiff = numpy.fabs(nvalue2 - nvalue1)
                diffs.append(float(ndiff) < 1e-10)
            if diffs.count(True) >= number_of_points * 0.8:
                response['correct'] = True
            else:
                response['correct'] = False
        else:
            # print(type(diff.free_symbols))
            unrecognised = ', '.join(list(map(str, diff.free_symbols)))
            # for sym in diff.free_symbols:
            #    print(sym)
            #    print(type(sym))
            response['error'] = _("Failed to evaluate expression")
            if len(unrecognised) > 0:
                response['error'] = (
                    response['error'] + ': ' + unrecognised + _(' are not valid variables.')
                )
    except SympifyError as e:
        # print("SympifyError")
        # print(e)
        # print(traceback.format_exc())
        logger.error([str(e), expression1, expression2])
        response['error'] = _("Failed to evaluate expression.")
        # pass
    except Exception as e:
        logger.error([str(e), expression1, expression2])
        response['error'] = _("Unknown error, check your expression.")
        # print("SympifyError")
        # print(e)
        # print(traceback.format_exc())
    return response  # }}}


def compare_numeric_runner(variables, expression1, expression2, q):
    response = compare_numeric_internal(variables, expression1, expression2)
    q.put(response)


def compare_numeric_runner_pool(variables, expression1, expression2):
    return compare_numeric_internal(variables, expression1, expression2)


def compare_numeric_pool(variables, expression1, expression2):  # {{{
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Pool. This can be used instead of the implementation with Process with less code but with less control over termination.
    """
    invalid_strings = ['_', '.', '[', ']']
    for i in invalid_strings:
        if i in expression1:
            return {'error': _('Answer contains invalid character ') + i}
    with Pool(processes=1) as pool:
        result = pool.apply_async(compare_numeric_runner, (variables, expression1, expression2))
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


def compare_numeric(variables, expression1, expression2):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_', '[', ']']
    for i in invalid_strings:
        if i in expression1:
            return {'error': _('Answer contains invalid character ') + i}
    # print(compare_numeric_internal(variables, expression1, expression2))
    q = Queue()
    p = Process(target=compare_numeric_runner, args=(variables, expression1, expression2, q))
    p.start()
    try:
        starttime = time.perf_counter()
        response = q.get(True, 6)
        timedelta = time.perf_counter() - starttime
        logger.info(
            "compare_numeric took "
            + str(timedelta)
            + 's ['
            + expression1
            + ', '
            + expression2
            + '] and variables '
            + json.dumps(variables)
        )
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


def to_latex(expression):
    latex = ""
    try:
        latex = sympy.latex(sympy.sympify(asciiToSympy(expression), ns))  # _clash))
    except SympifyError as e:
        print(e)
        latex = "error"
    return latex
