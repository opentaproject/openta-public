import sympy
import numpy
from sympy import *
from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import itertools
from exercises.questiontypes.safe_run import safe_run
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


class Norm(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.ImmutableMatrix):
            return x.norm()
        else:
            return None


class Cross(sympy.MatrixExpr):
    """
    This reimplementation of the cross product is necessary for sympify to generate a correct expression tree with
    the correct matrix operators instead of the standard scalar ones. For example sympify('5*cross(a,b)'),
     without any special handling, generates an expression tree with Mul instead of MatMul. Because of how sympy handles
     matrices this will result in a runtime error when eventually the cross products gets replaced with an actual matrix.
    """

    def __new__(cls, arg1, arg2):
        return sympy.Basic.__new__(cls, arg1, arg2)

    @property
    def shape(self):
        return self.args[0].shape

    def doit(self, **hints):
        x = self.args[0].doit() if isinstance(self.args[0], sympy.Basic) else self.args[0]
        y = self.args[1].doit() if isinstance(self.args[1], sympy.Basic) else self.args[1]
        if isinstance(x, sympy.ImmutableMatrix) and isinstance(y, sympy.ImmutableMatrix):
            return x.cross(y)
        else:
            return self


class Dot(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.ImmutableMatrix) and isinstance(y, sympy.ImmutableMatrix):
            return x.dot(y)
        else:
            return None


# Dictionary specifying behaviour of sympify conversion of asciimath to sympy. _clash is a special sympy list that
# removes, among other things, conversion of greek letter to special functions.
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

# Sympy substitution rule for removing units from an expression
uniteval = {meter: 1, second: 1, kg: 1}

# List of special handling in the conversion from sympy to numpy expressions for final evaluation
lambdifymodules = [
    {
        'cot': lambda x: 1.0 / numpy.tan(x),
        'norm': numpy.linalg.norm,
        'Norm': numpy.linalg.norm,
        'abs': numpy.linalg.norm,
        'cross': lambda x, y: numpy.cross(x, y, axis=0),
        'dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
    },
    "numpy",
]


def sympify_with_custom(expression, varsubs):
    """
    Convert asciimath expression into sympy using extra context
    Args:
        expression: asciimath
        varsubs: { string(name): substitution, ... }

    Returns:
        Sympy expression
    """
    scope = {'abs': Norm, 'cross': Cross, 'dot': Dot, 'norm': Norm}  # sympy.Function('norm')
    scope.update(ns)
    scope.update(varsubs)

    sexpr = sympy.sympify(ascii_to_sympy(expression), scope)
    return sexpr


class LinearAlgebraUnitError(Exception):
    """
    Can be raised from check_units_new
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def parse_variables(variables):
    """
    Parses a list of asciimath defined variables into correct sympy representations.

    Args:
        variables: [ { name: string, value: asciimath } , ... ]

    Returns:
        tuple ( subs_rules, sympify_rules, sample_variables )
        subs_rules: list of 2-tuples [ (sympy symbol, sympy expression), ... ] used in .subs(...)
        sympify_rules: { string(name): sympy symbol } used in sympify(...)
        sample_variables: [ { symbol: sympy Symbol/MatrixSymbol,
                              around: sympy expression ( a point around which to sample (might contain units))
                              }, ... ]

    """
    sym = {}
    vars = variables
    subs_rules = []
    sympify_rules = {}
    sample_variables = []
    for var in vars:
        expr = sympify_with_custom(ascii_to_sympy(var['value']), {})
        if hasattr(expr, 'shape'):
            sym[var['name']] = sympy.MatrixSymbol(var['name'], *expr.shape)
        else:
            sym[var['name']] = sympy.Symbol(var['name'])
        sympify_rules[var['name']] = sym[var['name']]
        if expr.has(sympy.Function('sample')):
            [sample] = expr.find(sympy.Function('sample'))
            sample_points = list(sample.args)
            sample_around = [
                expr.replace(sympy.Function('sample'), lambda *args: point).doit()
                for point in sample_points
            ]
            sample_variables.append({'symbol': sym[var['name']], 'around': sample_around})
        else:
            subs_rules.append((sym[var['name']], expr))
    return (list(reversed(subs_rules)), sympify_rules, sample_variables)


def check_units_new(expression, correct, sample_variables):
    """
    Checks if expression has the same SI units as correct by confirming that the quotient is independent of variations
    in each unit separately (by random sampling).

    Args:
        expression: sympy expression
        correct: sympy expression
        sample_variables: [ { symbol: sympy Symbol/MatrixSymbol,
                              around: sympy expression ( a point around which to sample (might contain units))
                              }, ... ]

    Returns:
        Nothing
    Raises:
        LinearAlgebraUnitError if the units do not match
    """
    nvarsubs = {}
    nsubs_values = []

    def perturb(value):
        return value + value * random.random() * 0.1

    for item in sample_variables:
        nvarsubs[item['symbol']] = item['symbol'] * item['around'][0]
        value = float(item['around'][0].subs(uniteval))
        sampled_value = value + random.random() * value * 0.1
        nsubs_values.append((item['symbol'], sampled_value))
    nexpression = expression.subs(nvarsubs).doit()
    ncorrect = correct.subs(nvarsubs).doit()

    checks = [[1, 1, 1], [perturb(2), 1, 1], [1, perturb(2), 1], [1, 1, perturb(2)]]
    results = []
    for check in checks:
        unit_values = list(map(lambda item: (item[1], item[0]), zip(check, [kg, meter, second])))
        allvalues = nsubs_values + unit_values
        vale = numpy.linalg.norm(
            sympy.lambdify([], nexpression.subs(allvalues).doit(), modules=lambdifymodules)()
        )
        valc = numpy.linalg.norm(
            sympy.lambdify([], ncorrect.subs(allvalues).doit(), modules=lambdifymodules)()
        )
        if valc != 0:
            results.append(vale / valc)
        else:
            results.append(vale)
    for res in results:
        if numpy.absolute(res - results[0]) > 10e-5:
            raise LinearAlgebraUnitError(
                _("Seems like the expression does not have the correct units.")
            )


def linear_algebra_compare_expressions(variables, student_answer, correct, blacklist=[]):
    """
    Compare two asciimath expressions for equality.

    Args:
        variables: [ { name: string, value: asciimath }, ... ]
        student_answer: asciimath
        correct: asciimath
        blacklist: [ string ] blacklisted tokens

    Returns:
        {
            correct: boolean
            error: string
        }
    """
    try:
        varsubs, varsubs_sympify, sample_variables = parse_variables(variables)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate
        # expression (necessary for matrix expressions).
        prelhs = sympify_with_custom(student_answer, varsubs_sympify)
        lhs = prelhs.subs(varsubs).subs(varsubs).subs(varsubs).doit()
        prerhs = sympify_with_custom(correct, varsubs_sympify)
        rhs = prerhs.subs(varsubs).subs(varsubs).subs(varsubs).doit()
        if hasattr(lhs, 'shape') and hasattr(rhs, 'shape'):
            if lhs.shape != rhs.shape:
                return {'error': _('The answer does not have the correct dimensions.')}
        if hasattr(lhs, 'shape') and not hasattr(rhs, 'shape'):
            return {'error': _('The answer does not have the correct dimensions.')}
        if hasattr(rhs, 'shape') and not hasattr(lhs, 'shape'):
            return {'error': _('The answer does not have the correct dimensions.')}
        if isinstance(prelhs, sympy.Basic):
            atoms = prelhs.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {'error': _('Forbidden token: ') + strrep}
                if funcstr in blacklist:
                    return {'error': _('Forbidden token: ') + funcstr}
    except SympifyError as e:
        logger.error([str(e), str(student_answer), str(correct)])
        response = dict(error=_("Failed to evaluate expression."))
        return response
    except ShapeError as e:
        response = dict(
            error=_("There seems to be a vector or matrix operation with incompatible dimensions.")
        )
        return response
    except Exception as e:
        logger.error([str(e), str(student_answer), str(correct)])
        response = dict(error=_("Unknown error, check your expression."))
        return response

    return linear_algebra_check_equality(lhs, rhs, sample_variables)


def linear_algebra_check_equality(lhs, rhs, sample_variables):  # {{{
    """
    Compares two sympy expressions for equality using random sampling around a point specified in variables.

    Args:
        variables: [ { name: string, value: asciimath }, ... ]
        lhs: sympy expression
        rhs: sympy expression

    Returns:
        {
            correct: boolean
            error: string
        }
    """

    number_of_points = 5
    response = {}
    try:
        random.seed(1)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate
        # expression (necessary for matrix expressions).
        sympy1_units = lhs
        sympy2_units = rhs
        sympy1 = sympy1_units.subs(uniteval)
        sympy2 = sympy2_units.subs(uniteval)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Expression 1: ' + str(sympy1))
            logger.debug('Expression 2: ' + str(sympy2))

        subs_neighbours = []
        for i in range(0, number_of_points):
            subs_neighbour = []
            for var in sample_variables:
                sample_point_values = []
                for sample_point in var['around']:
                    var_value = float(sample_point.subs(uniteval))
                    sample_point_values.append(
                        (var['symbol'], var_value + random.random() * var_value * 0.1 + 0j)
                    )
                subs_neighbour.append(sample_point_values)
            for combination in itertools.product(*subs_neighbour):
                subs_neighbours.append(combination)
                if logger.isEnabledFor(logging.DEBUG):
                    varvals = list(map(lambda x: str(x[0]) + ':' + str(x[1]), combination))
                    logger.debug('Neighbour point: ' + str(varvals))

        one_point = list(
            map(lambda item: (item['symbol'], item['around'][0].subs(uniteval)), sample_variables)
        )
        undefined_variables = sympy1.subs(one_point).free_symbols - set([kg, second, meter])
        if len(undefined_variables) > 0:
            unrecognised = ', '.join(list(map(str, undefined_variables)))
            response['error'] = unrecognised + _(' are not valid variables.')
            return response

        test_evaluation = numpy.linalg.norm(
            sympy.lambdify(
                [],
                (sympy1.subs(one_point).doit() - sympy2.subs(one_point).doit()),
                modules=lambdifymodules,
            )()
        )
        try:
            check_units_new(sympy1_units, sympy2_units, sample_variables)
        except LinearAlgebraUnitError as e:
            response['warning'] = str(e)

        diffs = []
        for sample_point in subs_neighbours:
            nvalue1 = sympy.lambdify(
                [], sympy1.subs(sample_point).doit(), modules=lambdifymodules
            )()
            nvalue2 = sympy.lambdify(
                [], sympy2.subs(sample_point).doit(), modules=lambdifymodules
            )()
            ndiff = numpy.absolute(nvalue2 - nvalue1)
            correct = numpy.all(ndiff < 1e-06)
            diffs.append(correct)
        if diffs.count(True) >= len(subs_neighbours) * 0.9:
            response['correct'] = True
        else:
            response['correct'] = False
    except SympifyError as e:
        logger.error([str(e), str(lhs), str(rhs)])
        response['error'] = _("Failed to evaluate expression.")
    except Exception as e:
        logger.error([str(e), str(lhs), str(rhs)])
        # traceback.print_exc()
        response['error'] = _("Unknown error, check your expression.")
    return response  # }}}


def linear_algebra_expression_runner(variables, expression1, expression2, blacklist, result_queue):
    response = linear_algebra_compare_expressions(variables, expression1, expression2, blacklist)
    result_queue.put(response)


def linear_algebra_expression(variables, student_answer, correct_answer, blacklist=[]):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_']
    for i in invalid_strings:
        if i in student_answer:
            return {'error': _('Answer contains invalid character ') + i}
    # print(compare_numeric_internal(variables, expression1, expression2))
    return safe_run(
        linear_algebra_expression_runner,
        args=(variables, student_answer, correct_answer, blacklist),
    )


def linear_algebra_expression_blocking(variables, student_answer, correct_answer, blacklist=[]):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    return linear_algebra_compare_expressions(variables, student_answer, correct_answer, blacklist)
