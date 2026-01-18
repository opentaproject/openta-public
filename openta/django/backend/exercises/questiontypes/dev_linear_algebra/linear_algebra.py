# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import random
import time
from sympy import ShapeError
import traceback

import numpy
import sympy
from exercises.questiontypes.safe_run import safe_run
from exercises.utils.print_utils import dprint
from exercises.utils.checks import (
    LinearAlgebraUnitError,
    check_answer_structure,
    check_consistency,
    check_for_legal_answer,
    check_for_undefined_variables_and_functions,
    check_units_new,
)
from exercises.utils.parsers import parse_sample_variables
from exercises.utils.string_formatting import absify  # replace_sample_funcs
from exercises.utils.string_formatting import (
    declash,
    insert_implicit_multiply,
    replace_sample_funcs,
)
from exercises.utils.sympify_with_custom import sympify_with_custom
from sympy import *
from sympy.core.sympify import SympifyError

from django.conf import settings
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def linear_algebra_check_if_true(
    precision, variables, correct, expression, check_units=False, blacklist=[], funcsubs={}, extradefs={}
):
    shouldbetrue = correct + "== 1"
    return linear_algebra_compare_expressions(
        precision,
        variables,
        expression,
        shouldbetrue,
        check_units=True,
        blacklist=[],
        funcsubs={},
        extradefs=extradefs,
    )


def equality_remap(student_answer, correct, varsubs_sympify):
    time.time()
    is_equality = False
    equality = correct.split("==")
    if len(equality) > 1 and "$$" in correct:
        is_equality = True
        correct = equality[1]
        student_answer = (equality[0]).replace("$$", "(" + student_answer + ")")
    if "==" in student_answer:
        is_equality = True
        equality = correct.split("==")
        if not len(equality) == 2:
            raise NameError("Error in equality syntax in student answer %s " % str(student_answer))
        correct = "abs( (" + equality[0] + ") - ( " + equality[1] + "))"
        correct = "0"
        equality = student_answer.split("==")
        student_answer = "abs( (" + equality[0] + ") - ( " + equality[1] + "))"
    if is_equality:  # DON'T DO SAMPLING IN EQUALITY
        student_answer = replace_sample_funcs(student_answer)
        correct = replace_sample_funcs(correct)
        for key in varsubs_sympify.keys():
            varsubs_sympify[key] = sympy.sympify(replace_sample_funcs(str(varsubs_sympify[key])))
    return (student_answer, correct, varsubs_sympify)


def linear_algebra_compare_expressions(
    precision,
    variables,
    student_answer,
    correct,
    check_units=False,
    blacklist=[],
    used_variables=[],
    funcsubs=[],
    extradefs={},
    validate_definitions=False,
    source="UNDEFINED1",
):
    student_answer_unparsed = student_answer
    student_answer = declash(student_answer)
    correct = declash(correct)
    tnow = time.time()
    i = 0

    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    _, varsubs_sympify, sample_variables = parse_sample_variables(variables, {}, extradefs, source=source + "- SOURCE1")
    #print(f"COMPARE_EXPRESSIONS SAMPLE_VARIABLES {sample_variables}")
    #print(f"COMPARE_EXPRESSIONS SAMPLE_VARIABLES {varsubs_sympify}")
    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    for unitname in ["kg", "meter", "second", "ampere", "kelvin", "mole", "candela"]:
        if unitname in str(correct):
            check_units = True

    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    if not validate_definitions and not settings.RUNTESTS:
        response = check_for_undefined_variables_and_functions(student_answer, used_variables)
        if response:
            return response
    try:
        (student_answer, correct, varsubs_sympify) = equality_remap(student_answer, correct, varsubs_sympify)
    except Exception as e:
        response = {"error": "Equality syntax incorrect in student expression [%s] " % student_answer_unparsed}
        logger.error(
            f"LINEAR_ALGEBRA_ERROR 901 student_answer={student_answer} correct={correct} error={type(e).__name__}"
        )
        return response
    # logger.error("A")
    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    insert_implicit_multiply(correct)
    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    precheck = check_for_legal_answer(precision, variables, student_answer, correct, check_units, blacklist)
    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    # logger.error("B")
    if precheck is not None:
        return precheck
    student_answer = insert_implicit_multiply(student_answer)
    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    response = check_answer_structure(student_answer, correct, varsubs_sympify, extradefs)
    # logger.error("C")
    if response:
        return response

    # logger.error("D")
    dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
    tnow = time.time()
    i = i + 1
    try:
        prelhs = sympify_with_custom(
            student_answer, varsubs_sympify, {}, extradefs, "linear_algebra_compare_expressions-2"
        )
        if isinstance(prelhs, str):
            response = dict(
                correct=False,
                debug=f" Unknown error in {student_answer} ",
            )
            return response
        dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
        tnow = time.time()
        i = i + 1
        if prelhs.has(oo, -oo, zoo, nan):
            response = dict(correct=False, warning=f" Your answer {student_answer} is infinite or undefined. ")
            return response
        lhs = prelhs.doit()
        dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
        tnow = time.time()
        i = i + 1
    except Exception as e:
        logger.error(f" UNCAUGHT ERROR {type(e).__name__} student_answer = {student_answer}")
        response = dict(correct=False, warning=f" Unknown error in {student_answer}")
        return response
    try:
        dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
        tnow = time.time()
        i = i + 1
        prerhs = sympify_with_custom(correct, varsubs_sympify, {}, extradefs, "linear_algebra_compare_expressions-3")
        if isinstance(prerhs, str):
            response = dict(correct=False, warning=f"Error in author expression needs to be fixed.")
            logger.error(f" ERROR   {str(prerhs)}")
            return response
        rhs = prerhs.doit()
        dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
        tnow = time.time()
        i = i + 1
    except Exception as e:
        if "@" in str(e):
            explanation = "The character @ appears in author expression; check for macros with missing semicolon separator or missing :=  in macro definition"
        else:
            explanation = ""
        response = dict(
            correct=False,
            error=(f"Error in author expression. {explanation}"),
            warning=("%s %s" % (type(e), str(e))),
        )
        dprint(f"        COMPARE {i}  { int( ( tnow - time.time() ) * 1000 ) } ")
        tnow = time.time()
        i = i + 1
        return response
    # logger.error("E")

    ret = linear_algebra_check_equality(
        precision,
        lhs,
        rhs,
        sample_variables,
        check_units=check_units,
        blacklist=blacklist,
        extradefs=extradefs,
    )
    # logger.error("F")
    ret["maxerror"] = str(ret.get("maxerror", "X"))
    # logger.error(f" RET = {ret}")
    return ret


def localsqrt(x):
    return numpy.sqrt(x)


local_defs = {
    "cot": lambda x: 1.0 / numpy.tan(x),
    "exp": lambda x: numpy.exp(x),
    "log": lambda x: numpy.log(x),
    "sqrt": lambda x: numpy.sqrt(x),
    "real": lambda x: numpy.real(x),
    "norm": lambda x: numpy.linalg.norm(x),
    "eq": lambda x, y: 1.0 if numpy.equal(x, y) else 0.0,
    "logicaland": numpy.logical_and,
    "logicalor": numpy.logical_or,
    "Norm": lambda x: numpy.linalg.norm(x),
    "abs": lambda x: numpy.linalg.norm(x),
    "cross": lambda x, y: numpy.cross(x, y, axis=0),
    "crossfunc": lambda x, y: numpy.cross(x, y, axis=0),
    "dot": lambda x, y: numpy.vdot(x, y),
    "Dot": lambda x, y: numpy.vdot(x, y),
    "zoo": numpy.inf,
    "I": complex(0, 1),
    "sample": lambda *x: dorand(x),
    "pi": numpy.pi,
}

sample_defs = dict(local_defs)
# sample_defs.update({"sample": lambda *x: dorand(x)})
sample_module = [
    sample_defs,
    "numpy",
]


base_module = [
    local_defs,
    "numpy",
]

kit = 0 
def dorand(xt):
    global kseed, kit
    #print(f"XT = {xt}, {type(xt)}")
    try:
        x = list(xt)
    except TypeError:
        x = [xt]
    #print(f"X = {x} kit={kit} ")
    if len(x) > 1 :
        ret = float( x[kit % len(x) ] )
        return ret
    s = 0
    random.seed(kseed)
    i = 0.1
    for value in list(x):
        if abs(value) > 1.0e-6:
            scale = 10.0 ** (round(log(abs(value), 10)))
        else:
            scale = 1.0
        s = s + value * (1.0 + 0.05 * random.random()) + 0.1 * scale * random.random()
        i = i + 1.0
    s = s / i
    return float(s)


sample_project = [
    {
        "sample": lambda *x: x[0],
    },
    "sympy",
]


kseed = 5


def sigfig(x):
    if x == 0:
        return "0"
    else:
        return str(10.0 ** (round(log(x, 10))))


def linear_algebra_check_equality(
    precision, lhs, rhs, sample_variables, check_units=True, blacklist=None, extradefs={}
):  # {{{
    global kseed, kit
    precision = numpy.float64(precision)
    check_units_here = False
    for u in ["kg", "meter", "second", "ampere", "kelvin", "mole", "candela"]:
        if u in str(lhs) or u in str(rhs):
            check_units_here = True
    check_units = check_units_here and check_units
    response = check_consistency(lhs, rhs, blacklist)
    if response:
        return response
    lhsorig = lhs
    time.time()
    # dprint("LINEAR_ALGEBRA_CHECK_EQUALITY check_units", check_units)
    if rhs == 0.0:
        rhs = 0.0 * lhs
        check_units = False
    if lhs == 0.0:
        lhs = 0.0 * rhs
        check_units = False
    response = {}
    time.time()
    inner = "BEGIN: "
    # print("ZERO = ", Zero)
    #print(f"SAMPLE_VARIABLES_IN_LINEAR_ALGEBRA {sample_variables}")
    #print(f"LHS = {lhs} RHS={rhs}")
    try:
        #print("DO SAMPLE")
        miss = 0
        bigmiss = 0
        nsamples = 5
        if not "sample" in str(lhsorig):
             nsamples = 1
        maxerror = 0
        maxaerror = 0
        random.seed(10)
        for k in range(0, nsamples):
            kit = k 
            #print(f"SAMPLE k={k}")
            kseed = k
            baseunits = [
                ("meter", float(random.random() + 1.0)),
                ("second", float(random.random() + 1.0)),
                ("kg", float(random.random() + 1.0)),
                ("ampere", float(random.random() + 1.0)),
                ("kelvin", float(random.random() + 1.0)),
                ("mole", float(random.random() + 1.0)),
                ("candela", float(random.random() + 1.0)),
            ]
            # (lhs,rhs) = ("Matrix([ [10*kg*meter/second**2], [ 2*kg*meter/second**2], [ 4*kg*meter/second**2]])",
            #            "Matrix([ [10*kg*meter/second**2], [ 2*kg*meter/second**2], [ 4*kg*meter/second**2]])")
            sympy_wo_units1 = sympy.sympify(str(lhs)).subs(baseunits)
            sympy_wo_units2 = sympy.sympify(str(rhs)).subs(baseunits)
            pair = (sympy_wo_units1, sympy_wo_units2)
            oldpair = pair
            # dprint("A1")
            # dprint(f"SAMPLE_MODULE = { sample_module}")
            # dprint(f"PAIR = {pair}")
            try:
                pair = sympy.lambdify(
                    [],
                    pair,
                    modules=sample_module,
                )()
            except NameError as e:
                response["error"] = str(e)
                return response
            except Exception as e:
                errorstring = str(e)
                if "kg" in errorstring or "meter" in errorstring or "second" in errorstring:
                    response["error"] = "Units are not consistent"
                    return response
                logger.error(
                    f"LINEAR_ALGEBRA_ERROR 910 lhs={lhs} rhs={rhs} error=LINEAR_ALGEBRA_EXPRESSION{ type(e).__name__} "
                )
                logger.error(f"{traceback.format_exc()}")
                logger.error(f"SHOULD BE UNIT_FREE pair  = {oldpair}")
                miss = miss + 1
            dprint("A2")
            (sympy_wo_units1, sympy_wo_units2) = pair
            cond = 0
            #print(f"PAIR = {pair}")
            try:
                diff = numpy.absolute(((sympy_wo_units1) - (sympy_wo_units2)))
                adiff = numpy.absolute((numpy.absolute(sympy_wo_units1) - numpy.absolute((sympy_wo_units2))))
                answer_scale = numpy.absolute((sympy_wo_units2))
                scale = answer_scale
                # dprint(f"DIFF {diff} type(diff) = {type(diff)}")
                # dprint(f"ADIFF {adiff} type(adiff) = {type(adiff)}")
                # if  diff == 0 or adiff == 0 :
                #    cond = 1
                #    maxadiff = diff
                #    maxdiff = diff
                cond = 1
                tdiff = numpy.sum(diff)
                if numpy.isscalar(tdiff):
                    assert not numpy.isnan(tdiff), "Incorrect"
                else:
                    assert not (numpy.isnan(tdiff)).any(), "Incorrect"
                if not numpy.isscalar(scale):
                    cond = 2
                    maxadiff = numpy.amax(adiff)
                    maxdiff = numpy.amax(diff)
                    scale = numpy.amax(scale)
                    # maxdiff = maxdiff.item()
                    # maxadiff = maxadiff.item()LINEAR_ALGEBRA_EXPRESSION
                else:
                    cond = 3
                    maxdiff = diff
                    maxadiff = adiff
                if hasattr(maxdiff, "item"):
                    maxdiff = maxdiff.item()
                if hasattr(maxadiff, "item"):
                    maxadiff = maxadiff.item()
                if hasattr(scale, "item"):
                    scale = max(scale.item(), 1.0)
                else:
                    scale = max(scale, 1.0)
                # dprint(f" OK SO FAR")
            except AssertionError as e:
                if "sqrt" in str(lhs):
                    return {"error": str(e) + " probably illegal sqrt"}
                elif "log" in str(lhs):
                    return {"error": str(e) + " probably illegal log"}
                else:
                    return {"error": str(e)}
            except Exception as e:
                maxdiff = 99.0
                maxadiff = 99.0
                diff = 99.0
                if "shape" in str(e):
                    return {"error": " matrix shape incompatibility "}
                logger.error(
                    "LINEAR_ALGEBRA_ERROR 912 %s: %s %s %s %s %s"
                    % (cond, lhs, rhs, type(e).__name__, str(e), traceback.format_exc())
                )
                scale = 1.0
            if not precision:
                accuracy = scale * 1.0e-5
            else:
                response["precision"] = precision
                accuracy = numpy.float64(precision) * answer_scale
            # print(f"ACCURACYH = {accuracy}  { type( accuracy) } precision = {precision} { type(precision)}")
            accuracy = numpy.maximum(accuracy, precision)  # ADDED THIS TO AVOID ERROR WITH 0 ==  0
            # print(f" ACCURACY = {scale} {answer_scale} {accuracy} { type(accuracy) } ")
            # accuracy = numpy.max( accuracy, numpy.float64( 1.e-8) )
            # accuracy = numpy.max(numpy.float64(accuracy))
            # accuracy = numpy.max(accuracy, 1.0e-9)
            # logger.error(f" ACCURACY = {accuracy}")
            try:
                if numpy.any(numpy.abs(diff) > accuracy) and numpy.any(accuracy > 0):
                    miss = miss + 1
                if numpy.any(numpy.abs(diff) > 10000 * accuracy) and numpy.any( 10000 *  accuracy > 0):
                    bigmiss = bigmiss + 1;


            except TypeError as e:
                logger.error(
                    "MISS WITH Type ERROR %s %s %s %s %s" % (lhs, rhs, type(e), str(e), traceback.format_exc())
                )
            except Exception as e:
                logger.error("MISS WITH ERROR %s %s %s %s %s" % (lhs, rhs, type(e), str(e), traceback.format_exc()))

                miss = miss + 1
            maxerror = max(maxerror, maxdiff)
            maxaerror = max(maxaerror, maxadiff)
        if settings.DEBUG_PLUS:
            response["debug"] = " Sampling: %s of %s are ok; maxerror = %s " % (
                str(nsamples - miss),
                str(nsamples),
                str(maxerror),
            )
            response["maxerror"] = "err = [%s : %s]" % (sigfig(maxerror), sigfig(maxaerror))
        if miss <= nsamples * 0.3:
            response["correct"] = True
            check_units = False
        else:
            response["correct"] = False
        response["debug"] = "maxerror  = %s and maxadiff = %s " % (
            sigfig(maxerror),
            sigfig(maxaerror),
        )
        if bigmiss > 0 :
            response["correct"] = False;
        # dprint(f" CHECK_UNITS = {check_units} MISS={miss} ")
        if check_units:
            try:
                s1 = sympy.sympify(replace_sample_funcs(str(lhs)))
                s2 = sympy.sympify(replace_sample_funcs(str(rhs)))
                check_units_new(s1, s2, sample_variables)
                inner = inner + "B"
            except LinearAlgebraUnitError as e:
                response["error"] = " " + str(e) + " "
            except KeyError as e:
                response["error"] = " " + str(e) + " "
            except NameError as e:
                response["error"] = " " + str(e) + " "
            except Exception as e:
                logger.error(
                    "LINEAR_ALGEBRA_ERROR 913: %s %s %s %s %s"
                    % (lhs, rhs, type(e).__name__, str(e), traceback.format_exc())
                )
    except ShapeError:
        response["error"] = _("Illegal matrix operation")
    except SympifyError as e:
        inner = ""
        logger.error([str(e), str(lhs), str(rhs)])
        response["error"] = _("Error 533 Failed to evaluate expression. {inner} ")
    except AttributeError as e:
        parts = str(e).split("attribute")
        response["error"] = str(parts[1]) + " is undefined  ( Error 347 ) inner = " + inner
        response["debug"] = str(e) + inner
    except NameError as e:
        response["error"] = "(Error 483: ) " + str(e)
    except TypeError as e:
        msg = str(e)
        if "cannot add" in msg:
            if "mutable" in msg and "core" in msg:
                response["error"] = f"incompatible type. You may be trying to add scalar to nonscalar "
            else:
                response["error"] = f"incompatible types in addtion "
        else:
            response["error"] = f"incompatible types in your expression"
    except Exception as e:
        inner = ""
        logger.error(f"ERROR 914  {type(e).__name__} {str(e)} lhs={ lhs } rhs={rhs}")
        response["error"] = f"Unknown parsing error:  check your expression"
    # dprint(f"RESPONSE = {response}")
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
    extradefs,
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
        extradefs,
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
    extradefs={},
    source="UNDEF4",
):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
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
            extradefs,
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
    extradefs={},
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
        extradefs,
    )
