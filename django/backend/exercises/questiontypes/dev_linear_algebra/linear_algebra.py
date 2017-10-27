import sympy
import numpy
import types
import sys
from sympy import *
from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import itertools
from sympy.core import S

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
from .unithelpers import *
from sympy import DiagonalOf
from .functions import *
from .checks import *
from .parsers import *

logger = logging.getLogger(__name__)

# meter, second, kg , ampere , kelvin, mole, candela = sympy.symbols('meter,second,kg,ampere,kelvin,mole,candela', real=True, positive=True)
# see http://iamit.in/sympy/coverage-report/matrices/sympy_matrices_expressions_diagonal_py.html
# List of special handling in the conversion from sympy to numpy expressions for final evaluation


def linear_algebra_check_if_true(
    precision, variables, correct, expression, check_units=False, blacklist=[]
):
    shouldbetrue = correct + '== 1'
    return linear_algebra_compare_expressions(
        precision, variables, expression, shouldbetrue, check_units=True, blacklist=[]
    )


def linear_algebra_compare_expressions(
    precision, variables, student_answer, correct, check_units=True, blacklist=[]
):
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
        precheck = check_for_legal_answer(
            precision, variables, student_answer, correct, check_units, blacklist
        )
        # print("precheck = ", precheck)
        if precheck is not None:
            return precheck
        varsubs, varsubs_sympify, sample_variables = parse_sample_variables(variables)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate
        # expression (necessary for matrix expressions).
        equality = correct.split('==')
        if len(equality) > 1:
            correct = equality[1]
            student_answer = (equality[0]).replace('$$', '(' + student_answer + ')')
        try:
            unparsedstudentanswer = sympy.sympify(ascii_to_sympy(student_answer), varsubs_sympify)
        except Exception as e:
            # print("DEV ERROR = ", e );
            return {'error': 'Error: ' + str(e)}
        try:
            prelhs = sympify_with_custom(student_answer, varsubs_sympify)
        except Exception as e:
            response = dict(
                error=_(
                    "PROGRAMMING ERROR/ERROR \n "
                    + str(student_answer)
                    + "\n"
                    + str(unparsedstudentanswer)
                    + str(e)
                )
            )
            return response
        lhs = prelhs.doit().subs(varsubs).subs(varsubs).subs(varsubs).doit()
        try:
            prerhs = sympify_with_custom(correct, varsubs_sympify)
            rhs = prerhs.doit().subs(varsubs).subs(varsubs).subs(varsubs).doit()
        except Exception as e:
            response = dict(error=_("ERROR IN AUTHOR EXPRESSION"))
            return response
        ##print("DEV_LINEAR_ALGEGEBRA lhs = ", lhs );
        # print("DEV_LINEAR_ALGEGEBRA rhs = ", rhs );
        if hasattr(lhs, 'shape') and hasattr(rhs, 'shape'):
            if lhs.shape != rhs.shape:
                return {'error': _('incorrect dimensions')}
        if hasattr(lhs, 'shape') and not hasattr(rhs, 'shape'):
            return {'error': _('incorrect dimensions')}
        if hasattr(rhs, 'shape') and not hasattr(lhs, 'shape'):
            return {'error': _('incorrect dimensions')}
        if isinstance(prelhs, sympy.Basic) or isinstance(prelhs, sympy.MatrixBase):
            specials = [
                ('cross', Cross),
                ('dot', Dot),
                ('norm', Norm),
                ('Braket', Braket),
                ('KetBra', KetBra),
                ('KetMBra', KetMBra),
                ('Trace', Trace),
                ('gt', gt),
            ]
            for special in specials:
                # print("___________________________")
                # print("DEV_LINEAR ALGEBRA TEST ", unparsedstudentanswer, "TEST FOR", special[0] )
                # print("DEV_LINEAR ALGEBRA TEST atoms:", unparsedstudentanswer.has( special[1] ) )
                # print("DEV_LINEAR ALGEBRA TEST blacklist ", blacklist )
                # print("___________________________")
                # if special[0] in blacklist and unparsedstudentanswer.has(special[1]):
                # if special[0] in blacklist and unparsedstudentanswer.has(special[1]):
                if special[0] in blacklist and (special[0] in str(unparsedstudentanswer)):
                    return {'error': _('Forbidden token: ') + special[0]}
            atoms = prelhs.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
            # print("atoms = ", atoms)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {'error': _('Forbidden token: ') + strrep}
                if funcstr in blacklist:
                    return {'error': _('Forbidden token: ') + funcstr}
    except SympifyError as e:
        logger.error(traceback.format_exc())
        logger.error([str(e), str(student_answer), str(correct)])
        response = dict(error=_("Failed to evaluate expression."))
        return response
    except ShapeError as e:
        logger.error(traceback.format_exc())
        response = dict(
            error=_("There seems to be a vector or matrix operation with incompatible dimensions.")
        )
        return response
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error([str(e), str(student_answer), str(correct)])
        response = dict(error=_("Unknown error, check your expression."))
        return response

    return linear_algebra_check_equality(
        precision, lhs, rhs, sample_variables, check_units=check_units
    )


def linear_algebra_check_equality(precision, lhs, rhs, sample_variables, check_units=True):  # {{{

    number_of_points = 5
    response = {}
    # print("CHECK_EQUALITY lhs ", str( lhs ));
    # print("CHECK_EQULITY  rhs ", str( rhs ));
    response['ABC'] = 'ABC'
    try:
        random.seed(1)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate
        # expression (necessary for matrix expressions).
        sympy1_units = lhs
        sympy2_units = rhs
        sympy1 = sympy1_units.subs(baseunits)
        sympy2 = sympy2_units.subs(baseunits)
        if isinstance(sympy1, Number):
            number_of_points = 5
        else:
            check_units = False
            # print("NO CAUGHT FLOAT", sympy1, type( sympy1 ) )
            number_of_points = 1

        # if logger.isEnabledFor(logging.DEBUG):
        #    logger.debug('Expression 1: ' + str(sympy1))
        #    logger.debug('Expression 2: ' + str(sympy2))
        # print("UNITS ARE ", str(sympy1));
        # print("UNITS ARE ", str(sympy2));
        subs_neighbours = []
        for i in range(0, number_of_points):
            subs_neighbour = []
            for var in sample_variables:
                sample_point_values = []
                for sample_point in var['around']:
                    var_value = float(sample_point.subs(baseunits))
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
            map(lambda item: (item['symbol'], item['around'][0].subs(baseunits)), sample_variables)
        )
        undefined_variables = sympy1.subs(one_point).free_symbols - set(
            [kg, second, meter, ampere, kelvin, mole, candela, sympy.I, sympy.E]
        )
        if len(undefined_variables) > 0:
            unrecognised = ', '.join(list(map(str, undefined_variables)))
            response['error'] = unrecognised + _(' are not valid variables.')
            return response

        eval_point = subs_neighbours[0] if subs_neighbours else []

        # print("TYPE1 = ", type( sympy1 ) )
        # print("TYPE2 = ", type( sympy2 ) )
        # print("EVAL_POINT ", eval_point)
        # print("LENGTH SUBS_NEIGHBORS", len( subs_neighbours ) )
        if len(subs_neighbours) <= 1:
            test_evaluation = numpy.linalg.norm(
                sympy.lambdify(
                    [],
                    (sympy1.subs(eval_point).doit() - sympy2.subs(eval_point).doit()),
                    modules=lambdifymodules,
                )()
            )
            if numpy.absolute(test_evaluation) < precision:
                response['correct'] = True
            else:
                response['correct'] = False
                # response['warning'] = "NO SAMPLING"
            return response
        test_evaluation = numpy.linalg.norm(
            sympy.lambdify(
                [],
                (sympy1.subs(eval_point).doit() - sympy2.subs(eval_point).doit()),
                modules=lambdifymodules,
            )()
        )
        # print("TEST EVALUATION = ", test_evaluation)
        inner = "A"
        if check_units:
            try:
                inner = inner + '1'
                # print("sympy1_units = ", sympy1_units)
                # print("sympy2_units = ", sympy2_units)
                # print("sample_variables = ", sample_variables )
                check_units_new(sympy1_units, sympy2_units, sample_variables)
                inner = inner + 'B'
            except LinearAlgebraUnitError as e:
                response['warning'] = str(e)
                return response

        diffs = []
        for sample_point in subs_neighbours:
            inner = inner + 'C'
            nvalue1 = sympy.lambdify(
                [], sympy1.subs(sample_point).doit(), modules=lambdifymodules
            )()
            inner = inner + 'D'
            nvalue2 = sympy.lambdify(
                [], sympy2.subs(sample_point).doit(), modules=lambdifymodules
            )()
            inner = inner + 'E'
            ndiff = numpy.absolute(nvalue2 - nvalue1)
            inner = inner + 'F'
            correct = numpy.all(ndiff < precision)
            inner = inner + 'G'
            diffs.append(correct)
            inner = inner + 'H'
        if diffs.count(True) >= len(subs_neighbours) * 0.9:
            response['correct'] = True
        else:
            inner = inner + 'J'
            # response['warning'] = inner
            response['correct'] = False
    except SympifyError as e:
        inner = ''
        logger.error([str(e), str(lhs), str(rhs)])
        response['error'] = _("Failed to evaluate expression." + inner)
    except Exception as e:
        inner = ''
        logger.error([str(e), str(lhs), str(rhs)])
        logger.error(traceback.format_exc())
        response['error'] = _("Unknown error, check your expression." + inner)
    return response  # }}}


def linear_algebra_expression_runner(
    precision, variables, expression1, expression2, check_units, blacklist, result_queue
):
    response = linear_algebra_compare_expressions(
        precision, variables, expression1, expression2, check_units, blacklist
    )
    result_queue.put(response)


def linear_algebra_expression(
    precision, variables, student_answer, correct_answer, check_units=True, blacklist=[]
):
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
        args=(precision, variables, student_answer, correct_answer, check_units, blacklist),
    )


def linear_algebra_expression_blocking(
    precision, variables, student_answer, correct_answer, check_units=True, blacklist=[]
):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    return linear_algebra_compare_expressions(
        precision, variables, student_answer, correct_answer, check_units, blacklist
    )
