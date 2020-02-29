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
from .variableparser import getallvariables, get_used_variable_list
from .sympify_with_custom import sympify_with_custom


logger = logging.getLogger(__name__)

# meter, second, kg , ampere , kelvin, mole, candela = sympy.symbols('meter,second,kg,ampere,kelvin,mole,candela', real=True, positive=True)
# see http://iamit.in/sympy/coverage-report/matrices/sympy_matrices_expressions_diagonal_py.html
# List of special handling in the conversion from sympy to numpy expressions for final evaluation


def linear_algebra_check_if_true(
    precision, variables, correct, expression, check_units=False, blacklist=[], funcsubs={}
):
    shouldbetrue = correct + '== 1'
    return linear_algebra_compare_expressions(
        precision, variables, expression, shouldbetrue, check_units=True, blacklist=[], funcsubs={}
    )


def linear_algebra_compare_expressions(
    precision,
    variables,
    student_answer,
    correct,
    check_units=True,
    blacklist=[],
    used_varialbes=[],
    funcsubs={},
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
    student_answer_orig = student_answer
    try:
        precheck = check_for_legal_answer(
            precision, variables, student_answer, correct, check_units, blacklist
        )
        if precheck is not None:
            return precheck
        varsubs, varsubs_sympify, sample_variables = parse_sample_variables(variables)
        equality = correct.split('==')
        if len(equality) > 1 and '$$' in correct:
            correct = equality[1]
            # student_answer_orig = student_answer
            student_answer = (equality[0]).replace('$$', '(' + student_answer + ')')
        if '==' in student_answer:
            equality = correct.split('==')
            if len(equality) != 2:
                return {'error': 'Response is not an equality'}
            correct = 'abs( (' + equality[0] + ') - ( ' + equality[1] + '))'
            correct = '0'
            equality = student_answer.split('==')
            student_answer = 'abs( (' + equality[0] + ') - ( ' + equality[1] + '))'
        try:
            unparsedstudentanswer = sympify_with_custom(
                ascii_to_sympy(student_answer), varsubs_sympify
            )
        except Exception as e:
            test = sympify_with_custom(ascii_to_sympy(student_answer_orig), varsubs_sympify).doit()
            testatoms = list(test.atoms(sympy.Function))
            testsymbols = list(test.atoms(sympy.Symbol))
            return {'error': '(G) Error : ' + str(testatoms) + str(testsymbols)}
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
            if '@' in str(e):
                explanation = 'The character @ appears in author expression; check for macros with missing semicolon separator or missing :=  in macro definition'
            else:
                explanation = ''
            response = dict(error=_("ERROR IN AUTHOR EXPRESSION. " + explanation))
            return response
        if hasattr(lhs, 'shape') and hasattr(rhs, 'shape'):
            if lhs.shape != rhs.shape:
                return {
                    'error': _('incorrect dimensions')
                    + ': your answer has the dimensions '
                    + str(lhs.shape)
                    + ' whereas  the answer requires the dimensions '
                    + str(rhs.shape)
                }
        if hasattr(lhs, 'shape') and not hasattr(rhs, 'shape'):
            return {
                'error': _('incorrect dimensions')
                + ': your expression is a matrix or vector; a scalar answer is required.'
            }
        if hasattr(rhs, 'shape') and not hasattr(lhs, 'shape'):
            return {
                'error': _('incorrect dimensions')
                + ': your expression is a scalar; a vector or matrix answer is required.'
            }
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
                if special[0] in blacklist and (special[0] in str(unparsedstudentanswer)):
                    return {'error': _('(E) Forbidden token: ') + special[0]}
            atoms = prelhs.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {'error': _('(F) Forbidden token: ') + strrep}
                if funcstr in blacklist:
                    return {'error': _('(G) Forbidden token: ') + funcstr}
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
    # response['ABC'] = 'ABC';
    try:
        random.seed(1)
        sympy1_units = lhs
        sympy2_units = rhs
        sympy1 = sympy1_units.subs(baseunits)
        sympy2 = sympy2_units.subs(baseunits)
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
                # if logger.isEnabledFor(logging.DEBUG):
                #    varvals = list(map(lambda x: str(x[0]) + ':' + str(x[1]), combination))
                #    logger.debug('Neighbour point: ' + str(varvals))

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
        if len(subs_neighbours) <= 1:
            inside = sympy1.subs(eval_point).doit() - sympy2.subs(eval_point).doit()
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

        nsympy1 = sympy1.subs(eval_point).doit()
        nsympy2 = sympy2.subs(eval_point).doit()
        nnsympy2 = numpy.linalg.norm(sympy.lambdify([], nsympy2, modules=lambdifymodules)())
        if check_units:
            if nsympy2 == 0 or nnsympy2 < 1e-12:
                check_units = False
        test_evaluation = numpy.linalg.norm(
            sympy.lambdify([], nsympy1 - nsympy2, modules=lambdifymodules)()
        )
        inner = "A"
        if check_units:
            try:
                inner = inner + '1'
                # print("call check_units_new")
                check_units_new(sympy1_units, sympy2_units, sample_variables)
                # print("returned from check_units_new")
                inner = inner + 'B'
            except LinearAlgebraUnitError as e:
                response['warning'] = str(e)
                return response

        diffs = []
        for sample_point in subs_neighbours:
            inner = inner + 'C'
            nsympy1 = sympy1.subs(sample_point).doit()
            nsympy2 = sympy2.subs(sample_point).doit()
            inner = inner + 'D'
            inner = inner + 'E'
            try:
                ndiff = numpy.linalg.norm(
                    sympy.lambdify(
                        [],
                        (sympy1.subs(sample_point).doit() - sympy2.subs(sample_point).doit()),
                        modules=lambdifymodules,
                    )()
                )
            except Exception as e:
                response['error'] = str(e)
                response['correct'] = False
                return response
                break
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
    except AttributeError as e:
        parts = str(e).split('attribute')
        response['error'] = str(parts[1]) + ' is undefined '
    except NameError as e:
        response['error'] = str(e)
    except Exception as e:
        # print("error caught = ", str(e) )
        inner = ''
        logger.error([str(e), str(lhs), str(rhs)])
        logger.error(traceback.format_exc())
        response['error'] = _("Unknown error, check your expression." + inner)
    return response  # }}}


def linear_algebra_expression_runner(
    precision,
    variables,
    expression1,
    expression2,
    check_units,
    blacklist,
    used_variables,
    funcsubs,
    result_queue,
):
    response = linear_algebra_compare_expressions(
        precision,
        variables,
        expression1,
        expression2,
        check_units,
        blacklist,
        used_variables,
        funcsubs,
    )
    result_queue.put(response)


def linear_algebra_expression(
    precision,
    variables,
    student_answer,
    correct_answer,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs={},
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
        args=(
            precision,
            variables,
            student_answer,
            correct_answer,
            check_units,
            blacklist,
            used_variables,
            funcsubs,
        ),
    )


def linear_algebra_expression_blocking(
    precision,
    variables,
    student_answer,
    correct_answer,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs={},
):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    return linear_algebra_compare_expressions(
        precision,
        variables,
        student_answer,
        correct_answer,
        check_units,
        blacklist,
        used_variables,
        funcsubs,
    )
