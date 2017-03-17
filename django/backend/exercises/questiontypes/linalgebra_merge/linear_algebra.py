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
        'abs': numpy.linalg.norm,
        'cross': lambda x, y: numpy.cross(x, y, axis=0),
        'dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
        #'Cross': lambda x,y : numpy.cross(x,y,axis=0) ,
    },
    "numpy",
]


def sympify_with_custom(expression, varsubs):
    scope = {'abs': sympy.Function('norm')}
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
    subs_rules = {}
    sympify_rules = {}
    sample_variables = []
    for var in vars:
        expr = sympify_with_custom(ascii_to_sympy(var['value']), {})
        if hasattr(expr, 'shape'):
            sym[var['name']] = sympy.MatrixSymbol(
                var['name'], *expr.shape
            )  # sympy.symbols(var['name'])
        else:
            sym[var['name']] = sympy.Symbol(var['name'])
        sympify_rules[var['name']] = sym[var['name']]
        if expr.has(sympy.Function('sample')):
            sample_around = expr.replace(sympy.Function('sample'), lambda x: x).doit()
            sample_variables.append({'symbol': sym[var['name']], 'around': sample_around})
        else:
            subs_rules[sym[var['name']]] = expr  # _clash)
    return (subs_rules, sympify_rules, sample_variables)


def check_units_new(expression, correct, sample_variables):
    nvarsubs = {}
    nvalues = []

    def perturb(value):
        return value + value * random.random() * 0.1

    for item in sample_variables:
        nvarsubs[item['symbol']] = item['symbol'] * item['around']
        value = float(item['around'].subs(uniteval))
        nvalues.append(value + random.random() * value * 0.1 + 0j)
    nexpression = expression.subs(nvarsubs)
    ncorrect = correct.subs(nvarsubs)
    allvars = tuple(map(lambda item: item['symbol'], sample_variables)) + (kg, meter, second)
    lexpr = sympy.lambdify(allvars, nexpression, modules=lambdifymodules)
    lcorrect = sympy.lambdify(allvars, ncorrect, modules=lambdifymodules)

    checks = [[1, 1, 1], [perturb(2), 1, 1], [1, perturb(2), 1], [1, 1, perturb(2)]]
    results = []
    for check in checks:
        args = nvalues + check
        vale = numpy.linalg.norm(lexpr(*args))
        valc = numpy.linalg.norm(lcorrect(*args))
        if valc != 0:
            results.append(vale / valc)
        else:
            results.append(vale)
    for res in results:
        if numpy.absolute(res - results[0]) > 10e-5:
            raise LinearAlgebraUnitError(
                _("Seems like the expression does not have the correct units.")
            )


def linear_algebra_parse_expression(variables, student_answer, correct_answer):
    return {}


def linear_algebra_parse_condition(variables, condition):
    return {}


def linear_algebra(variables, student_answer, correct):  # {{{
    # Do some initial formatting
    expression1 = student_answer
    expression2 = correct
    number_of_points = 10
    response = {}
    try:
        sexpression1 = ascii_to_sympy(expression1)
        sexpression2 = ascii_to_sympy(expression2)

        random.seed(1)
        varsubs, varsubs_sympify, sample_variables = parse_variables(variables)
        # varsubs_sympify = parse_variables_symp(variables)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        sympy1_units = sympify_with_custom(sexpression1, varsubs_sympify).subs(varsubs).doit()
        sympy2_units = sympify_with_custom(sexpression2, varsubs_sympify).subs(varsubs).doit()
        sympy1 = sympy1_units.subs(uniteval)
        sympy2 = sympy2_units.subs(uniteval)
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
                var_value = float(var['around'].subs(uniteval))
                neighbour.append(var_value + random.random() * var_value * 0.1 + 0j)
            neighbours.append(neighbour)
            if logger.isEnabledFor(logging.DEBUG):
                varvals = list(
                    map(
                        lambda x: str(x[0]['symbol']) + ':' + str(x[1]),
                        zip(sample_variables, neighbour),
                    )
                )
                logger.debug('Neighbour point: ' + str(varvals))

        one_point = list(
            map(lambda item: (item['symbol'], item['around'].subs(uniteval)), sample_variables)
        )
        undefined_variables = sympy1.subs(one_point).free_symbols - set([kg, second, meter])
        if len(undefined_variables) > 0:
            unrecognised = ', '.join(list(map(str, undefined_variables)))
            response['error'] = unrecognised + _(' are not valid variables.')
            return response

        test_evaluation = numpy.linalg.norm(
            sympy.lambdify(
                [], (sympy1.subs(one_point) - sympy2.subs(one_point)), modules=lambdifymodules
            )()
        )
        try:
            check_units_new(sympy1_units, sympy2_units, sample_variables)
        except LinearAlgebraUnitError as e:
            response['warning'] = str(e)

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
        # traceback.print_exc()
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
