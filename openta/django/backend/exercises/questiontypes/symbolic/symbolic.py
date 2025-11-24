# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import random
import re as resub
import time
import traceback

import sympy
from exercises.questiontypes.dev_linear_algebra.linear_algebra import (
    sigfig,
)
from exercises.questiontypes.safe_run import safe_run
from exercises.util import index_of_matching_right_paren
from exercises.utils.checks import *
from exercises.utils.functions import *
from exercises.utils.parsers import *
from exercises.utils.sympify_with_custom import sympify_with_custom
from exercises.utils.unithelpers import *
from sympy import *
from sympy.core.sympify import SympifyError
from sympy.printing.mathml import *
from sympy import symbols, simplify;
from sympy.physics.quantum.operatorordering import normal_ordered_form as no
from sympy.physics.quantum.boson import BosonOp;
from sympy.physics.quantum import Dagger, Commutator




from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def expr_are_equal(ex1, ex2):
    try:
        diff = 99.0
        zz = sympify("0.0").evalf()
        ex1 = zz if "ZeroMatrix" in srepr(ex1) else ex1
        ex2 = zz if "ZeroMatrix" in srepr(ex2) else ex2
        ex1 = ex1.subs(baseunits).doit()
        ex2 = ex2.subs(baseunits).doit()
        if ex1.is_Matrix and ex2.is_Matrix:
            diff = sympy.simplify(ex1 - ex2).norm()
            adiff = diff
            tval = diff < 1.0e-8
        elif ex1.is_Matrix:
            diff = ex1.norm()
            adiff = diff
            if ex2 == sympy.sympify("0") and diff < 1.0e-8:
                tval = True
            else:
                tval = False
        elif ex2.is_Matrix:
            diff = ex2.norm()
            adiff = diff
            if ex1 == sympy.sympify("0") and diff < 1.0e-8:
                tval = True
            else:
                tval = False
        else:
            diff = sympify(ex1 - ex2).evalf()
            adiff = sympify(abs(abs(ex1) - abs(ex2))).evalf()
            if "Symbol" in srepr(diff):
                # for key in dir( diff1 ):
                #    #print( "KEY  = ", key, "ATT = ", getattr(diff1, key) )
                tval = False
            else:
                tval = (diff == 0) or (abs(N(diff)) < 1.0e-8)
    except Exception:
        # print("ERROR WAS " + str(e))
        tval = False
    diff = 1.0
    adiff = 1.0
    return (tval, "[%s,%s]" % (str(sigfig(abs(diff))), str(sigfig(abs(adiff)))))


def symbolic_check_if_true(
    precision,
    variables,
    correct,
    expression,
    check_units=False,
    blacklist=[],
    used_variables=[],
    funcsubs={},
    extradefs={},
):
    shouldbetrue = correct + "== 1"
    return symbolic_compare_expressions(
        precision,
        variables,
        expression,
        shouldbetrue,
        check_units=True,
        blacklist=[],
        used_variables=[],
        funcsubs=funcsubs,
        extradefs=extradefs,
        validate_definitions=False,
        source="UNKNOWN-2",
    )


def symbolic_compare_expressions(
    precision,
    variables,
    student_answer,
    correct,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs=[],
    extradefs={},
    validate_definitions=False,
    source="UNKNOWN-3",
):
    logger.debug(
        f"SYMBOLIC_COMPARE_EXPRESSIONS ARGS: precision={precision}\n \
                variables={variables}\n \
                student_answer={student_answer}\n \
                correct={correct}\n  \
                check_units={check_units}\n  \
                blacklist={blacklist}\n  \
                used_variables={used_variables}\n  \
                funcsubs={funcsubs}\n  \
                extradefs\n \
                validate_definitions={validate_definitions}\n"
    )

    #    if settings.OPTIMIZE_COMPARE:
    #        calculus_expressions = [
    #            "curl",
    #            "div",
    #            "grad",
    #            "partial",
    #            "Partial",
    #            "Prime",
    #            "del2",
    #            "dot",
    #            "iden",
    #        ]
    #        # if validate_definitions :
    #        #    [student_answer, correct] = student_answer.split('==')
    #        #    print(f"STUDENT = {student_answer} correct = {correct}")
    #        if len(funcsubs) == 0 and not "'" in correct and not "'" in student_answer:
    #            skip_calculus = True
    #            varstring = " ".join([t["value"] for t in variables])
    #            for s in calculus_expressions:
    #                if s in correct or s in student_answer or s in varstring:
    #                    skip_calculus = False
    #            if skip_calculus:
    #                ret = linear_algebra_compare_expressions(
    #                    precision,
    #                    variables,
    #                    student_answer,
    #                    correct,
    #                    check_units,
    #                    blacklist,
    #                    used_variables,
    #                    funcsubs=[],
    #                    extradefs={},

    #                    validate_definitions=validate_definitions,
    #                )
    #                ret["correct"] = ret.get("correct", False)
    #                # print(f"RET = {ret}")
    #                return ret
    should_be_end = index_of_matching_right_paren(0, "(" + student_answer + ")")
    assert should_be_end == len(student_answer) + 2, "MATCHING PAREN ERROR IN STUDENT_ANSWER " + student_answer
    should_be_end = index_of_matching_right_paren(0, "(" + correct + ")")
    assert should_be_end == len(correct) + 2, "MATCHING PAREN ERROR IN CORRECT " + correct
    # print("CORRECT = ", correct )
    correct_is_equality = "==" in correct
    student_answer_is_equality = "==" in student_answer
    response = {}

    if "=" in student_answer and not "==" in student_answer:
        response["error"] = "single equal sign cannot appear in expression"
        response["debug"] = student_answer
        response["correct"] = False
        return response

    if not correct_is_equality and student_answer_is_equality:
        response["error"] = "equality not permitted in response"
        response["correct"] = False
        response["debug"] = student_answer
        return response

    # s1 = ascii_to_sympy(student_answer)
    # s2 = ascii_to_sympy(correct)
    # student_answer = s1
    # correct = s2
    # #print("SPLITA = " , ( time.time() - tbeg  )  * 1000 )
    all_variables = [x["name"] for x in variables]
    illegalvars = set(list(ns.keys())).intersection(set(all_variables))
    illegalvars = list(illegalvars - set(sympy_units))
    if len(illegalvars) > 0:
        response = {}
        response["correct"] = False
        response["warning"] = "Illegal variable " + ",".join(illegalvars) + "."
        response["debug"] = str(illegalvars) + " Clashes with sympy predefined variables "
        return response
    ok = list(set(all_variables) - set(list(dir(sympy.functions))))
    variables = list(filter(lambda item: (item["name"] in ok), variables))  # GET RID OF CLASHES WITH FUNCTIONS
    # for v in ['x','y','z','t' ] :
    #    if not v in all_variables :
    #        variables = variables + [{'name':v }]
    extra_tokens = ["x", "y", "z", "t", "xhat", "yhat", "zhat"] + [item["name"] for item in funcsubs]
    precheck = check_for_legal_answer(precision, variables, student_answer, correct, False, blacklist, extra_tokens)
    if precheck is not None:
        # print("PRECHECK = ", precheck)
        response["correct"] = False
        return precheck
    response = {}
    response["correct"] = False
    prelhs = "PRELHS"
    try:
        varsubs, varsubs_sympify, sample_variables = parse_sample_variables(
            variables, funcsubs, extradefs, source="symbolic"
        )
        print(f"VARSUBS_SYMPIFY = {varsubs_sympify}")
        varsubs = [(key, val.subs(baseunits).doit()) for key, val in varsubs]
        student_answer_is_equality = len(student_answer.split("==")) > 1
        if student_answer_is_equality and correct_is_equality:
            [lhs, rhs] = student_answer.split("==")
        elif correct_is_equality and not student_answer_is_equality:
            if len(correct.split("$$")) < 2:
                response["error"] = "equality expected"
                response["debug"] = student_answer
                return response
            correct = ("(" + student_answer + ")").join(correct.split("$$"))
            [lhs, rhs] = correct.split("==")
        else:
            [lhs, rhs] = [correct, student_answer]
        response["error"] = lhs
        response["debug"] = "ERROR IN symbolic_compare_expressions"
        explanation = ""
        # print("VARSUBS_SYMPIFY = %s " % varsubs_sympify)
        [tlhs, trhs] = [lhs, rhs]
        print("SYMBOLIC tlhs %s varsubs_sympify %s funcsubs %s " % ( tlhs, varsubs_sympify, funcsubs) )
        if "0" == tlhs:
            prelhs = sympify_with_custom(trhs, varsubs_sympify, funcsubs, extradefs, "symbolic_compare_expressions-1")
        elif "0" == trhs:
            prelhs = sympify_with_custom(tlhs, varsubs_sympify, funcsubs, extradefs, "symbolic_compare_expressions-1")
        else:
            prerhs = sympify_with_custom(trhs, varsubs_sympify, funcsubs, extradefs, "symbolic_compare_expressions-1")
            # print("SYMBOLIC tlhs %s varsubs_sympify %s funcsubs %s " % ( tlhs, varsubs_sympify, funcsubs) )
            prelhs = sympify_with_custom(tlhs, varsubs_sympify, funcsubs, extradefs, "symbolic_compare_expressions-2")
        if hasattr(lhs, "shape") and hasattr(rhs, "shape"):
            if lhs.shape != rhs.shape:
                return {
                    "error": _("incorrect dimensions")
                    + ": your answer has the dimensions "
                    + str(lhs.shape)
                    + " whereas  the answer requires the dimensions "
                    + str(rhs.shape)
                }
        if hasattr(lhs, "shape") and not hasattr(rhs, "shape"):
            return {
                "error": _("incorrect dimensions")
                + ": your expression is a matrix or vector; a scalar answer is required."
            }
        if hasattr(rhs, "shape") and not hasattr(lhs, "shape"):
            return {
                "error": _("incorrect dimensions")
                + ": your expression is a scalar; a vector or matrix answer is required."
            }
        if isinstance(prelhs, sympy.Basic) or isinstance(prelhs, sympy.MatrixBase):
            specials = [
                ("cross", Cross),
                ("dot", Dot),
                ("norm", Norm),
                ("Braket", Braket),
                ("KetBra", KetBra),
                ("KetMBra", KetMBra),
                ("Trace", Trace),
                ("gt", gt),
            ]
            for special in specials:
                if special[0] in blacklist and (special[0] in str(unparsedstudentanswer)):
                    return {"error": _("(E) Forbidden token: ") + special[0]}
            atoms = prelhs.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {"error": _("(F) Forbidden token: ") + strrep}
                if funcstr in blacklist:
                    return {"error": _("(G) Forbidden token: ") + funcstr}

        # #print("SPLIT2 = " , ( time.time() - tbeg  )  * 1000 )
        lhs = sympify_with_custom(lhs, varsubs_sympify, funcsubs, extradefs, "symbolic_compare_expression-2")
        lhs = lhs.doit()
        # #print("SPLIT2a = " , ( time.time() - tbeg  )  * 1000 )
        # THE NEXT  BIT LINE IS 1/2 THE BOTTLENECK
        # IT PROPAGEATES TO TIME SPENT IN pre
        rhs = sympify_with_custom(rhs, varsubs_sympify, funcsubs, extradefs, "symbolic_compare_expression-3").doit()
        # print("LHS = ", lhs )
        # print("RHS = ", rhs )
        ##################
        # #print("SPLIT2b = " , ( time.time() - tbeg  )  * 1000 )
        res = symbolic_check_equality(precision, lhs, rhs, sample_variables, check_units=check_units)
        time.time()
        # #print("TOTAL TIME IN COMPARE EXPRESSIONS", ( tend - tbeg ) * 1000  , " MILLISECONDS" )
        return res

    except SympifyError as e:
        if "@" in str(e):
            explanation = "The character @ appears in author expression; check for macros with missing semicolon separator or missing :=  in macro definition"
        else:
            explanation = str(e)
        response = dict(error=_(explanation), debug="Error 91 : " + str(e))
        response["correct"] = False
    # except TypeError as e:
    #    explanation = " Type Error: i.e. for instance adding or comparing matrices and scalars "
    #    # explanation = explanation + str( student_answer)
    #    p = re.compile('(x|y|z)hat')
    #    if p.search(str(student_answer)):
    #        explanation = (
    #            'TypeError:  coordinates xhat,yhat,zhat cannot be mixed with explicit vectors'
    #        )
    #    response = dict(
    #        error=_(explanation),
    #        debug=(type(e).__name__ + ": " + str(e) + ' : Functions cannot return Matrix type'),
    #    )
    #    response['correct'] = False
    except NameError as e:
        logger.error(traceback.format_exc())
        logger.error([str(e), str(student_answer), str(correct)])
        response["correct"] = False
        response["debug"] = "NAME ERROR in symbolic_compare_expressions" + str(e) + str(student_answer)
        response["error"] = str(e)
    except ShapeError as e:
        logger.error(traceback.format_exc())
        response = dict(error=_("There seems to be a vector or matrix operation with incompatible dimensions."))
        response["correct"] = False
        response["debug"] = str(e)
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error([str(e), str(student_answer), str(correct)])
        response = dict(error=_("Unknown error, check your expression."))
        response["correct"] = False
        response["debug"] = (
            "Error1 in symbolic_compare_expressions: " + type(e).__name__ + ": " + str(e) + str(student_answer)
        )

    return response


def symbolic_internal(expression1, expression2):  # {{{
    # Do some initial formatting
    response = {}
    time.time()
    #
    # SWITCH BETWEEN SYMBOLIC AND NOT
    # NUMERIC IS PROBABLY THE WAY TO GO
    #
    # print(f"EXPRESSION1 = {expression1} EXPRESSION2={expression2}")
    doNumeric = True
    try:
        sympy1 = expression1
        sympy2 = expression2

        ns.update(unitbaseunits)
        # print("NS = ", ns )
        sympy1 = expression1.subs(ns).doit()
        sympy2 = expression2.subs(ns).doit()
        # print("SYMPY1 A = ", sympy1 )
        # print("SYMPY2 B = ", sympy2 )
        # print("SYMPY1 = ", sympy1 )
        # print("SYMPY2 = ", sympy2 )
        if not doNumeric:
            sympy1 = simplify(powdenest(powsimp(sympy1, force=True)))
            sympy2 = simplify(powdenest(powsimp(sympy2, force=True)))
        if sympy1 == 0:
            zero = sympy2
        elif sympy2 == 0:
            zero = sympy1
        else:
            zero = sympy1 - sympy2
        # THE NEXT LINE IS BOTTLENET 1/2 OF TIME SPENT
        # USING simplify ONLY DOES NOT DO MUCH  ; IT IS STILL SLOW
        # #print("ZER0 = ", simplify( zero ) )
        # print(f"doNumeric={doNumeric} sympy1={sympy1} sympy2={sympy2}")
        if doNumeric:
            symbs = zero.free_symbols
            # symbs.update( {sympy.Symbol('x') ,} )
            # #print("SYMBS = ", symbs)
            symsub = [(sym, random.random()) for sym in symbs]
            ex1 = sympy1.subs(symsub).doit()
            ex2 = sympy2.subs(symsub).doit()
        else:
            ex1 = sympy1
            ex2 = sympy2
            # shouldbezero = simplify(powdenest(factor(simplify(zero)), force=True))
            # diffy = Norm(shouldbezero)
        # print(" NOW ex1 = ", ex1 )
        # print(" NOW ex2 = ", ex2 )
        (are_same, maxerror) = expr_are_equal(ex1, ex2)
        response["correct"] = are_same
        if not are_same:
            # print("ZERO = ", zero )
            response["correct"] = False
            response["debug"] = "diff reduces to $" + latex(zero) + "$" + str(zero)
            response["correct"] = False
            response["debug"] = "diff reduces" + str(zero)
            response["maxerror"] = maxerror
        else:
            response["correct"] = True
            response["maxerror"] = maxerror
        return response
    except SympifyError as e:
        logger.error([str(e), expression1, expression2])
        response["debug"] = str(e)
        response["correct"] = False
        response["error"] = _("Failed to evaluate expression.")
    except TypeError as e:
        logger.error([str(e), expression1, expression2])
        response["debug"] = "Type Error in symbolic_internal :" + str(e)
        if "cannot add " in str(e):
            cls = resub.sub(r"<class \'([^>]*\')>", "\\1", str(e))
            cls = resub.sub(r"'", "", cls)
            cls = " ".join([item.split(".")[-1] for item in cls.split(" ")])
            cls = resub.sub(r"matrix", "matrix or vector", cls)
            cls = resub.sub(r".*Matrix", "matrix or vector", cls)
            cls = resub.sub(r"(Mul|Add)", "something else ", cls)
            cls = resub.sub(r"(NegativeOne)", "integer ", cls)
            response["error"] = "Incompatible types: " + cls
        response["correct"] = False
    except Exception as e:
        logger.error([str(e), expression1, expression2])
        response["error"] = _("Unknown error2, check your expression.")
        response["debug"] = debug = type(e).__name__ + ": " + str(e)
        response["correct"] = False
    # #print("TOTAL TIME IN INTERNAL", (time.time() - tbeg) * 1000)
    return response  # }}}


def symbolic_check_equality(precision, lhs, rhs, sample_variables, check_units=False):  # {{{
    response = {}
    response["correct"] = False
    try:
        response = symbolic_internal(lhs, rhs)
    except SympifyError as e:
        inner = ""
        logger.error([str(e), str(lhs), str(rhs)])
        response["error"] = _("Failed to evaluate expression." + inner)
        response["correct"] = False
    except AttributeError as e:
        parts = str(e).split("attribute")
        response["correct"] = False
        response["error"] = str(parts[1]) + " is undefined "
    except NameError as e:
        response["error"] = str(e)
        response["correct"] = False
    except Exception as e:
        inner = ""
        response["correct"] = False
        logger.error([str(e), str(lhs), str(rhs)])
        logger.error(traceback.format_exc())
        response["error"] = _("Unknown error 1, check your expression." + inner)
        response["debug"] = str(e)
    return response  # }}}


def go_expression(symbolic_compare_expressions, result_queue, *args):
    response = symbolic_compare_expressions(*args)
    result_queue.put(response)


def symbolic_expression_runner(*args, result_queue):
    go_expression(symbolic_compare_expressions, result_queue, *args)


def symbolic_expression(
    precision,
    variables,
    student_answer,
    correct_answer,
    check_units,
    blacklist=[],
    used_variables=[],
    funcsubs={},
    extradefs={},
    source="UNKNOWN-SYMBOLIC",
):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ["_", "#", "@", "&", "?", '"']
    for i in invalid_strings:
        if i in student_answer:
            return {"error": _("Answer contains invalid character ") + i}
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
            extradefs,
        ),
    )
