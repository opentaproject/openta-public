import sympy
import numpy
import types
import sys
from sympy import *

# from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import itertools

from exercises.questiontypes.safe_run import safe_run
import logging
import traceback
from exercises.questiontypes.dev_linear_algebra.string_formatting import (
    absify,
    insert_implicit_multiply,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
)
from exercises.questiontypes.dev_linear_algebra.unithelpers import *
from sympy import DiagonalOf
from exercises.questiontypes.dev_linear_algebra.functions import *
from exercises.questiontypes.dev_linear_algebra.checks import *
from exercises.questiontypes.dev_linear_algebra.parsers import *
from exercises.questiontypes.dev_linear_algebra.sympify_with_custom import sympify_with_custom
import re
import inspect
from sympy.printing.mathml import *


logger = logging.getLogger(__name__)

# meter, second, kg , ampere , kelvin, mole, candela = sympy.symbols('meter,second,kg,ampere,kelvin,mole,candela', real=True, positive=True)
# see http://iamit.in/sympy/coverage-report/matrices/sympy_matrices_expressions_diagonal_py.html
# List of special handling in the conversion from sympy to numpy expressions for final evaluation


def symbolic_check_if_true(
    precision,
    variables,
    correct,
    expression,
    check_units=False,
    blacklist=[],
    used_variables=[],
    funcsubs={},
):
    shouldbetrue = correct + '== 1'
    return symbolic_compare_expressions(
        precision,
        variables,
        expression,
        shouldbetrue,
        check_units=True,
        blacklist=[],
        used_variables=[],
        funcsubs=funcsubs,
    )


def symbolic_compare_expressions(
    precision,
    variables,
    student_answer,
    correct,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs={},
):
    s1 = ascii_to_sympy(student_answer)
    s2 = ascii_to_sympy(correct)
    all_variables = [x['name'] for x in variables]
    illegalvars = list(set(list(ns.keys())).intersection(set(all_variables)))
    if len(illegalvars) > 0:
        response = {}
        response['correct'] = False
        response['warning'] = 'Illegal variable ' + ','.join(illegalvars) + '.'
        response['debug'] = str(illegalvars) + " Clashes with sympy predefined variables "
        return response
    # variables = list(
    #    filter(lambda item: (item['name'] in dir( sympy.functions) ), variables)
    # )  # GET RID OF CLASHES WITH FUNCTIONS
    ok = list(set(all_variables) - set(list(dir(sympy.functions))))
    variables = list(
        filter(lambda item: (item['name'] in ok), variables)
    )  # GET RID OF CLASHES WITH FUNCTIONS
    response = {}
    # funcsubs_ = []
    # for sub in funcsubs:
    #    fsub = {}
    #    fsub['name'] = sub['name']
    #    #args = sub['args'].lstrip('[').rstrip(']')
    #    #fsub['args'] = [sympify(item.strip()) for item in args.split(',')]
    #    fsub['args'] = sub['args']
    #    fsub['value'] = sub['value']
    #    funcsubs_ = funcsubs_ + [fsub]
    # funcsubs = funcsubs_
    prelhs = 'PRELHS'
    try:
        correct_is_equality = len(correct.split('==')) > 1
        if '=' in student_answer and not '==' in student_answer:
            response['error'] = 'single equal sign cannot appear in expression'
            response['debug'] = student_answer
            return response
        varsubs, varsubs_sympify, sample_variables = parse_sample_variables(variables, funcsubs)
        student_answer_is_equality = len(student_answer.split('==')) > 1
        if student_answer_is_equality and correct_is_equality:
            [lhs, rhs] = student_answer.split('==')
        elif student_answer_is_equality and not correct_is_equality:
            response['error'] = 'equality is not a valid answer'
            response['debug'] = student_answer
            return response
        elif correct_is_equality and not student_answer_is_equality:
            if len(correct.split('$$')) < 2:
                response['error'] = 'equality expected'
                response['debug'] = student_answer
                return response
            correct = ('(' + student_answer + ')').join(correct.split('$$'))
            [lhs, rhs] = correct.split('==')
        else:
            [lhs, rhs] = [correct, student_answer]
        response['error'] = lhs
        response['warning'] = rhs
        explanation = ''
        try:
            teststring = '(' + ')-('.join(student_answer.split('==')) + ')'
            [tlhs, trhs] = [x.strip() for x in student_answer.split('==')]
            if '0' == tlhs:
                prelhs = sympify_with_custom(
                    trhs, varsubs_sympify, funcsubs, 'symbolic_compare_expressions-1'
                )
            elif '0' == trhs:
                prelhs = sympify_with_custom(
                    tlhs, varsubs_sympify, funcsubs, 'symbolic_compare_expressions-1'
                )
            else:
                prelhs = sympify_with_custom(
                    trhs, varsubs_sympify, funcsubs, 'symbolic_compare_expressions-1'
                ) - sympify_with_custom(
                    tlhs, varsubs_sympify, funcsubs, 'symbolic_compare_expressions-1'
                )
            # for var in used_variables:
            #    diff_ = diff(prelhs, sympify(var))
            #    diff_ = diff_.subs(varubs)
            #    print("DIFF = ", diff_)
            #    #if  Norm(diff_) == 0:
            #    #    return {
            #    #        'error': 'Answer has no mmeaningful dependence on the variable ' + str(var)
            #    #    }

        except SympifyError as e:
            if '@' in str(e):
                explanation = 'The character @ appears in author expression; check for macros with missing semicolon separator or missing :=  in macro definition'
            else:
                explanation = 'Error in expression'
            response = dict(error=_(explanation), debug="SympifyError : " + str(e))
            return response
        except TypeError as e:
            explanation = " Type Error: i.e. for instance adding or comparing matrices and scalars "
            # explanation = explanation + str( student_answer)
            p = re.compile('(x|y|z)hat')
            if p.search(str(student_answer)):
                explanation = (
                    'TypeError:  coordinates xhat,yhat,zhat cannot be mixed with explicit vectors'
                )
            response = dict(
                error=_(explanation),
                debug=(type(e).__name__ + ": " + str(e) + ' : Functions cannot return Matrix type'),
            )
            return response
        except Exception as e:
            response = dict(
                error=_("ERROR IN AUTHOR EXPRESSION. " + explanation),
                debug=(type(e).__name__ + ": " + str(e)),
            )
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
        response['debug'] = str(e)
        return response
    except ShapeError as e:
        logger.error(traceback.format_exc())
        response = dict(
            error=_("There seems to be a vector or matrix operation with incompatible dimensions.")
        )
        response['debug'] = str(e)
        return response
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error([str(e), str(student_answer), str(correct)])
        response = dict(error=_("Unknown error, check your expression."))
        response['debug'] = str(e)
        return response
    try:
        lhs = sympify_with_custom(
            lhs, varsubs_sympify, funcsubs, 'symbolic_compare_expression-2'
        ).doit()
        rhs = sympify_with_custom(
            rhs, varsubs_sympify, funcsubs, 'symbolic_compare_expression-3'
        ).doit()
        res = symbolic_check_equality(
            precision, lhs, rhs, sample_variables, check_units=check_units
        )
        return res
    except Exception as e:
        response = dict(error=str(e), debug=str(e))
        return response


def symbolic_internal(expression1, expression2):  # {{{
    # Do some initial formatting
    number_of_points = 10
    response = {}
    try:
        sexpression1 = expression1
        sexpression2 = expression2
        nvars = {}
        sympy1 = powdenest(factor(sympify(sexpression1, ns)), force=True)
        sympy2 = powdenest(factor(sympify(sexpression2, ns)), force=True)
        # print("SYMPY1 = ", sympy1 )
        # print("SYMPY2 = ", sympy2 )
        # if logger.isEnabledFor(logging.DEBUG):
        #    logger.debug('Expression 1: ' + str(sympy1))
        #    logger.debug('Expression 2: ' + str(sympy2))
        if sympy1 == 0:
            zero = sympy2
        elif sympy2 == 0:
            zero = sympy1
        else:
            zero = sympy1 - sympy2
        shouldbezero = simplify(powdenest(factor(simplify(zero)), force=True))
        diffy = Norm(shouldbezero)
        if diffy == 0:
            response['correct'] = True
        else:
            response['correct'] = False
            response['debug'] = "diff reduces to $" + latex(shouldbezero) + '$'
    except SympifyError as e:
        logger.error([str(e), expression1, expression2])
        response['debug'] = str(e)
        response['error'] = _("Failed to evaluate expression.")
    except TypeError as e:
        logger.error([str(e), expression1, expression2])
        response['debug'] = "Type Error in symbolic_internal :" + str(e)
        if "cannot add " in str(e):
            cls = re.sub(r"<class \'sympy\.core\.[^\.]*\.*([^\\']+).*", "\\1", str(e))
            cls = re.sub(r"matrix", "matrix or vector", cls)
            cls = re.sub(r"(Mul|Add)", 'something else ', cls)
            cls = re.sub(r"(NegativeOne)", 'integer ', cls)
            response['error'] = "Incompatible types: " + cls
    except Exception as e:
        logger.error([str(e), expression1, expression2])
        response['error'] = _("Unknown error2, check your expression.")
        response['debug'] = debug = type(e).__name__ + ": " + str(e)
    return response  # }}}


def symbolic_check_equality(precision, lhs, rhs, sample_variables, check_units=False):  # {{{
    try:
        response = symbolic_internal(lhs, rhs)
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
        inner = ''
        logger.error([str(e), str(lhs), str(rhs)])
        logger.error(traceback.format_exc())
        response['error'] = _("Unknown error 1, check your expression." + inner)
        response['debug'] = str(e)
    return response  # }}}


def symbolic_expression_runner(
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
    response = symbolic_compare_expressions(
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


def symbolic_expression(
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
    return safe_run(
        symbolic_expression_runner,
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


def symbolic_expression_blocking(
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
    return symbolic_compare_expressions(
        precision,
        variables,
        student_answer,
        correct_answer,
        check_units,
        blacklist,
        used_variables,
        funcsubs,
    )
