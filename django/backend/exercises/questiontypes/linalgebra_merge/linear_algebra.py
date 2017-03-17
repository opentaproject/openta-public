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
import traceback
from .string_formatting import (
    absify,
    insert_implicit_multiply,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
)

logger = logging.getLogger(__name__)

meter, second, kg = sympy.symbols('meter,second,kg', real=True, positive=True)

"""
Sympy expressions trees contain special operators for Matrix algebra, for example MatMul instead of Mul. This means
that when substituting matrices into expressions with symbols the operators need to be able to handle matrices for the
 resulting expression to be valid. To generate the correct operators the variables that are matrices or vectors need
 to be specified as MatrixSymbol instead of Symbol.
"""


class Cross(sympy.Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.ImmutableMatrix) and isinstance(y, sympy.ImmutableMatrix):
            res = x.cross(y)
            return res
        else:
            print("ILLEGAL TYPES IN CROSS")
            print(type(x))
            print(type(y))  # }}}


class Dot(sympy.Function):  # {{{
    nargs = (1, 2)

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.ImmutableMatrix) and isinstance(y, sympy.ImmutableMatrix):
            res = x.dot(y)
            return res
        else:
            print("ILLEGAL TYPES IN DOT")
            print(type(x))
            print(type(y))  # }}}


class Sample(sympy.Function):
    @classmethod
    def eval(cls, value):
        return value + 0.1 * value * random.random()


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
        #'sample': Sample
        #'Cross': Cross,
        #'Dot': Dot,
    }
)

uniteval = {meter: 1, second: 1, kg: 1}


def crosslog(x, y):
    print(x)
    print(y)
    return 1


lambdifymodules = [
    {
        'cot': lambda x: 1.0 / numpy.tan(x),
        'norm': numpy.linalg.norm,
        'Norm': numpy.linalg.norm,
        'cross': lambda x, y: numpy.cross(x, y, axis=0),
        #'Dot': lambda x,y : N( numpy.dot(x,y) ),
        #'Cross': lambda x,y : numpy.cross(x,y,axis=0) ,
    },
    "numpy",
]


def sympify_with_custom(expression, varsubs):
    scope = {}
    scope.update(ns)
    scope.update(varsubs)
    # for var, value in varsubs:

    sexpr = sympy.sympify(ascii_to_sympy(expression), scope)
    return sexpr


class LinearAlgebraUnitError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def parse_variables(variables):
    sym = {}
    # Decode JSON string into python lists/dictionaries
    vars = variables
    subs = {}
    sample_variables = []
    next_sample_variable = 0
    for var in vars:
        expr = sympify_with_custom(ascii_to_sympy(var['value']), {})
        if hasattr(expr, 'shape'):
            sym[var['name']] = sympy.MatrixSymbol(
                var['name'], *expr.shape
            )  # sympy.symbols(var['name'])
        else:
            sym[var['name']] = sympy.Symbol(var['name'])
        if expr.has(sympy.Function('sample')):
            sample_around = expr.replace(sympy.Function('sample'), lambda x: x).doit()
            sample_variables.append({'symbol': sym[var['name']], 'around': sample_around})
            next_sample_variable += 1
        else:
            subs[sym[var['name']]] = expr  # _clash)
    return (subs, sample_variables)


def parse_variables_symp(variables):
    sym = {}
    # Decode JSON string into python lists/dictionaries
    vars = variables
    # subs = []
    subs = {}
    for var in vars:
        expr = sympify_with_custom(ascii_to_sympy(var['value']), {})
        if hasattr(expr, 'shape'):
            subs[var['name']] = sympy.MatrixSymbol(
                var['name'], *expr.shape
            )  # sympy.symbols(var['name'])
        else:
            subs[var['name']] = sympy.Symbol(var['name'])
        # subs.append((sympy.Symbol(var['name']), expr))
    return subs


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
        if sympy.Abs(res - results[0]) > 10e-5:
            raise LinearAlgebraUnitError(
                _("Seems like the expression does not have the correct units.")
            )


def evaluate(variables, expression):
    subs = parse_variables(variables)
    # Parse expression and evaluate with specified values
    value = sympify_with_custom(expression).evalf(subs=subs)
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
        sexpression1 = ascii_to_sympy(expression1)
        sexpression2 = ascii_to_sympy(expression2)

        random.seed(1)
        varsubs, sample_variables = parse_variables(variables)
        varsubs_sympify = parse_variables_symp(variables)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        sympy1 = (
            sympify_with_custom(sexpression1, varsubs_sympify).subs(uniteval).subs(varsubs).doit()
        )
        sympy2 = (
            sympify_with_custom(sexpression2, varsubs_sympify).subs(uniteval).subs(varsubs).doit()
        )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Expression 1: ' + str(sympy1))
            logger.debug('Expression 2: ' + str(sympy2))
        sample_variable_symbols = list(map(lambda item: item['symbol'], sample_variables))
        numfunc1 = sympy.lambdify(sample_variable_symbols, sympy1, modules=lambdifymodules)
        numfunc2 = sympy.lambdify(sample_variable_symbols, sympy2, modules=lambdifymodules)

        neighbours = []
        for i in range(0, number_of_points):
            neighbour = []
            for var in sample_variables:
                neighbour.append(var['around'] + random.random() * var['around'] * 0.1 + 0j)
            neighbours.append(neighbour)
            if logger.isEnabledFor(logging.DEBUG):
                varvals = list(
                    map(
                        lambda x: str(x[0]['symbol']) + ':' + str(x[1]),
                        zip(sample_variables, neighbour),
                    )
                )
                logger.debug('Neighbour point: ' + str(varvals))

        diff = numpy.absolute(numfunc1(*neighbours[0]) - numfunc2(*neighbours[0]))
        test_bool = numpy.all(diff < 1e6)
        # unrecognised = ', '.join(list(map(str, diff.free_symbols)))
        # response['error'] = _("Failed to evaluate expression")
        # if len(unrecognised) > 0:
        #    response['error'] = response['error'] + ': ' + unrecognised + _(' are not valid variables.')

        # try:
        #    check_units_new(sympy1, sympy2, varsubs)
        # except LinearAlgebraUnitError as e:
        #    response['warning'] = str(e)
        # except ZeroDivisionError as e:
        #    response['zerodivision'] = True
        diffs = []
        for n in range(0, number_of_points):
            nvalue1 = numfunc1(*neighbours[n])  # sympy1.subs(point).subs(uniteval).evalf()
            nvalue2 = numfunc2(*neighbours[n])  # sympy2.subs(point).subs(uniteval).evalf()
            ndiff = numpy.absolute(nvalue2 - nvalue1)
            correct = numpy.all(ndiff < 1e-06)
            diffs.append(correct)
        if diffs.count(True) >= number_of_points * 0.8:
            response['correct'] = True
        else:
            response['correct'] = False
    except SympifyError as e:
        logger.error([str(e), expression1, expression2])
        response['error'] = _("Failed to evaluate expression.")
    except Exception as e:
        logger.error([str(e), expression1, expression2])
        traceback.print_exc()
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
    return safe_run(
        linear_algebra_expression_runner, args=(variables, student_answer, correct_answer)
    )


def linear_algebra_expression_blocking(variables, student_answer, correct_answer):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    return linear_algebra(variables, student_answer, correct_answer)
