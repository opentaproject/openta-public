# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import os
import random
import re as reg
import traceback

import numpy.linalg
from exercises.parsing import exercise_xml
from exercises.utils.print_utils import dprint
from sympy import *

from django.utils.translation import gettext as _

from .functions import *
from .parsers import *
from .string_formatting import declash, replace_sample_funcs
from .sympify_with_custom import sympify_with_custom
from .unithelpers import *
from .unithelpers import baseunits, sympy_units
from .variableparser import get_used_variable_list # , getallvariables

# from sympy.abc import _clash1, _clash2, _clash


logger = logging.getLogger(__name__)


def mysqrt(x):
    x = x + complex(0, 0)
    if numpy.isscalar(x):
        return numpy.sqrt(x)
    else:
        # print("Trying to take sqrt( %s ) type= %s " % ( str(x), type(x)  ) )
        return 0
        # raise ValueError("Trying to take sqrt( %s ) type= %s " % ( str(x), type(x)  ) )


lambdifymodules = [
    {
        "cot": lambda x: 1.0 / numpy.tan(x),
        "exp": lambda x: numpy.exp(x),
        "sqrt": lambda x: mysqrt(x),
        "real": lambda x: numpy.real(x),
        "norm": lambda x: numpy.linalg.norm(x),
        "logicaland": numpy.logical_and,
        "logicalor": numpy.logical_or,
        "eq": numpy.equal,
        "Norm": lambda x: numpy.linalg.norm(x),
        "abs": lambda x: numpy.linalg.norm(x),
        "cross": lambda x, y: numpy.cross(x, y, axis=0),
        "crossfunc": lambda x, y: numpy.cross(x, y, axis=0),
        "dot": lambda x, y: numpy.dot(numpy.transpose(x), y),
        "Dot": lambda x, y: numpy.dot(numpy.transpose(x), y),
        "zoo": numpy.inf,
        "I": complex(0, 1),
    },
    "numpy",
]

import re


class LinearAlgebraUnitError(Exception):
    """
    Can be raised from check_units_new
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def check_units_new(expression, correct, sample_variables):
    nvarsubs = {}
    nsubs_values = []

    def perturb(value):
        return value + value * float(random.random() * 0.1)

    # print("a")
    for item in sample_variables:
        # print("b")
        nvarsubs[item["symbol"]] = item["symbol"] * item["around"][0]
        value = float(item["around"][0].subs(baseunits))
        sampled_value = value + random.random() * value * 0.1
        nsubs_values.append((item["symbol"], sampled_value))
    # print("c")
    nexpression = expression.subs(nvarsubs).doit()
    # print("NEXPRESSION = ", nexpression)
    # print("d")
    ncorrect = correct.subs(nvarsubs).doit()
    # print("e")

    checks = [
        [1, 1, 1, 1, 1, 1, 1],
        [perturb(2), 1, 1, 1, 1, 1, 1],
        [1, perturb(2), 1, 1, 1, 1, 1],
        [1, 1, perturb(2), 1, 1, 1, 1],
        [1, 1, 1, perturb(2), 1, 1, 1],
        [1, 1, 1, 1, perturb(2), 1, 1],
        [1, 1, 1, 1, 1, perturb(2), 1],
        [1, 1, 1, 1, 1, 1, perturb(2)],
    ]
    results = []
    for check in checks:
        unit_values = list(map(lambda item: (item[1], item[0]), zip(check, sympy_units)))
        allvalues = nsubs_values + unit_values
        tres = sympy.lambdify([], nexpression.subs(allvalues), modules=lambdifymodules)()
        nexpression = sympy.sympify(str(nexpression))  # THIS MUST BE A BUG IN SYMPY THIS EXPRESSION SHOULD BE A NOOP
        allval = [
            ("meter", float(1)),
            ("second", float(1)),
            ("kg", float(1)),
            ("ampere", float(1)),
            ("kelvin", float(1)),
            ("mole", float(1)),
            ("candela", float(1)),
        ]
        nexpression.subs(allval)
        vale = 99
        valc = 99
        try:
            ve = sympy.lambdify([], nexpression.subs(allvalues).doit(), modules=lambdifymodules)()
            vc = sympy.lambdify([], ncorrect.subs(allvalues).doit(), modules=lambdifymodules)()
            if isinstance(vc, numpy.ndarray):
                ve = ve[vc != 0]
                vc = vc[vc != 0]
                vale = numpy.prod(ve)
                valc = numpy.prod(vc)
            else:
                vale = ve
                valc = vc
            ncorrect = sympy.sympify(str(ncorrect))
            if valc != 0:
                results.append(vale / valc)
            else:
                results.append(vale)
        except Exception as e:
            results.append(1.0)
            logger.error(
                f"UTILS.CHECKS ERROR 761 {type(e).__name__} error checking {nexpression}   or {ncorrect}, vale={vale} valc={valc}"
            )
    for res in results:
        if numpy.absolute(res - results[0]) > 10e-5:
            # print("g")
            raise LinearAlgebraUnitError(("Incorrect units::"))


def parens_are_balanced(expression):
    level = 1
    ind = 0
    while level > 0 and ind < len(expression):
        if expression[ind] == ")":
            level = level - 1
        elif expression[ind] == "(":
            level = level + 1
        ind = ind + 1
    return (level == 1) and (ind == len(expression))


def brackets_are_balanced(expression):
    level = 1
    ind = 0
    while level > 0 and ind < len(expression):
        if expression[ind] == "]":
            level = level - 1
        elif expression[ind] == "[":
            level = level + 1
        ind = ind + 1
    return (level == 1) and (ind == len(expression))


def check_for_legal_answer(
    precision,
    variables,
    student_answer,
    expression,
    check_units=True,
    blacklist=[],
    extra_tokens=[],
):
    #### INVALID STRINGS
    expression = declash(expression)
    student_answer = declash(student_answer)
    invalid_strings = ["_", "#", "@", "&", "?", '"', ":", "..", ";", "^*", "*^"]
    for i in invalid_strings:
        if i in student_answer:
            return {"error": _("Answer contains invalid character or string ") + i}

    illegal = reg.findall(r"(\^|\.)([0-9]+[a-zA-Z]+)(\^|\.)", student_answer)
    if len(illegal) > 0:
        s = ",".join(["".join(item) for item in illegal])
        return dict(error=_("Illegal pattern %s in %s " % (s, student_answer)))

    ##### INVALID PATTERNS
    invalid_patterns = {
        r"\)[\w]": "implicit multiply needs a space; right parenthesis cannot be followed by letter or number",
        r"\.[A-z\(\)]": "strange placement of a decimal",
        r"[\( \^\* ][0-9\.]+\(": "left implicit multiply with a number needs a space",
        r"^[0-9\.]+\(": "right implicit multiply with a number needs a space",
        r"[^A-z][0-9\.]+\(": "right implicit multiply with a number needs a space",
        r"[^=]=[^=]": "single equal sign is illegal",
        r"(\^|\s|\(|\+|\/|\*|-)[0-9\.]+[A-Za-z]": "illegal implicit multiply",
        r"(^|\s|\+|-|\*|\/)[0-9]+[A-Za-z]+": "illegal implicit multiply with a number",
        r"\^\s": "exponential cannot be followed by space",
        r"\^$": "exponential cannot end a line",
        r"\s\^": "exponential cannot be preceded by space",
        r"[A-z]\.": "period cannot follow letters",
    }
    for i in invalid_patterns.keys():
        if not None == re.search(r"%s" % i, student_answer):
            dprint(f" INVALIDATED {student_answer} with pattern {i}")
            return {"error": _("%s" % invalid_patterns[i])}

    ########## UNBALANCED PARENS
    if not parens_are_balanced(student_answer):
        return {"error": _("Unbalanced parenthesis")}

    if not brackets_are_balanced(student_answer):
        return {"error": _("Unbalanced brackets")}

    # print("VARIABLES1 = ", variables)
    variables = [replace_sample_funcs(item) for item in variables]
    # print("VARIABLES2 = ", variables)
    student_answer = replace_sample_funcs(declash(student_answer))
    # print("STUDENT ANSWER CHECK", student_answer, flush=True)

    ######### CHECK THAT VARIABLES ARE NOT USED AS FUNCTIONS ######
    for variable in variables:
        if re.search(r"(^|\W)%s\(" % variable["name"], student_answer):
            # MAKE EXCEPTION FOR FUNCTION
            if not "(" in variable["value"]:
                return dict(
                    error="Variable %s cannot be used as a function; check implicit multiply." % variable["name"]
                )

    ###########  MAKE SURE NO BLACKLISTED VARIABLES ARE USED
    studentatoms = get_used_variable_list(student_answer)
    okatoms = [item["name"] for item in variables] + [
        "kg",
        "meter",
        "second",
        "t",
        "x",
        "y",
        "z",
        "xhat",
        "yhat",
        "zhat",
    ]
    # print("okatoms = ", okatoms )
    # print("STUDENTATOMS = ", studentatoms)
    for atom in studentatoms:
        strrep = str(atom)
        # funcstr = str(atom.func)
        if strrep in blacklist or (strrep not in okatoms):
            if strrep not in extra_tokens:
                return {"error": _("(A) Forbidden token: ") + reg.sub(r"variable", "", strrep)}

    # student_answer = insert_implicit_multiply( student_answer )
    # student_answer = declash(student_answer)

    expression = replace_sample_funcs(expression)
    if "==" in expression and not "$$" in expression:
        if not "==" in student_answer:
            return {"error": _("answer in terms of an equality using == ")}
    if "==" in student_answer:
        if not "==" in expression or "$$" in expression:
            return {"error": _("an equality is not permitted as answer")}
        # else:
        #    equality = student_answer.split('==')
        #    student_answer = equality[0] + '-' + equality[1]

    m = re.search(r"(atan|arctan|acos|arccos|acos|arcos|asin|arcsin)", student_answer)
    if m:
        return {"error": _("The inverse trig function ") + m.group(1) + _(" is forbidden ")}
    m = re.search(r"(print|sum)", student_answer)
    if m:
        return {"error": _("forbidden function") + m.group(1)}
    return None


def check_answer_structure(student_answer, correct, varsubs_sympify, extradefs={}):
    response = None
    prelhs = None
    time.time()
    if student_answer.strip() == "":
        response = dict(error="Your answer is blank!")
        return response
    try:
        # REPLACE SAMPLES WITH SINGLE SHOT TO CHECK STRUCTURE OF ANSWER
        tstudent_answer = replace_sample_funcs(student_answer)
        # print("      TSTUDENTANSWER = ", tstudent_answer)
        # print("      TYPE VARSUBS_SUMPFIY = ", type( varsubs_sympify) )
        tvarsubs_sympify = {}
        for key in varsubs_sympify.keys():
            # print("     KEY = ", key )
            tvarsubs_sympify[key] = sympy.sympify(replace_sample_funcs(str(varsubs_sympify[key])))
        # dprint("      TVARSUBS_SYMPIFY = ", tvarsubs_sympify)
        prelhs = sympify_with_custom(
            tstudent_answer,
            tvarsubs_sympify,
            {},
            extradefs,
            "check-answer-structure-linear_algebra_compare_expressions",
        )

    except AttributeError as e:
        if "uple" in str(e):
            response = dict(
                    error=_("Look for misplaced comma. Use square brackets if you are using vectors or matrices::")
            )
        else:
            response = dict(
                error=_(
                    "Unknown error 279: Look for missing square brackets for vectors, stray or incorrectly placed commas::"
                ),
                debug="Error 279: " + str(e) + traceback.format_exc(),
            )

    except TypeError as e:
        if "required positional" in str(e):
            response = dict(error=_("function is missing an argument"))
        elif "callable" in str(e):
            response = dict(
                error=(
                    "Unrecognized function call. Remember that letters and numbers, including a lone integer that precedes a left parenthesis is interpreted as a function even if the javascript frontend interprets it the way you do. It is much better to use space or * to specify you mean multiplication. Don't depend on OpenTA to always interpret implicit multiplication."
                )
            )
        else:
            response = dict(error=_(str(e)), debug="Error 187: " + str(e) + traceback.format_exc())
        # return response

    except NameError as e:
        response = dict(error=_(str(e)), debug="Error 193: " + str(e))
        # return response

    except ShapeError as e:
        response = dict(
            error=_(
                "Matrix dimensions inconsistent with each other or with the result. Possible reasons: You must mul(A,B) for multiplying a matrix or matrix times vector. The matrices must have proper dimenions for that. You also can't divide by a matrix or vector. "
            ),
            debug="Error 202: " + str(e),
        )
        # return response
    except ValueError as e:
        illegalchars = ["$", "%"]
        explain = ""
        if False and settings.DEBUG:
            msg = str(e)
        else:
            msg = "Error 158"
        illegalpresent = list(filter(lambda x: x in student_answer, illegalchars))
        if "EOF" in str(e):
            msg = "Unclosed expression"
        elif "mismatched" in str(e):
            msg = ""
            explain = "Probably missing mul(A,B) in matrix x matrix or matrix x vector"
        elif "EOL" in str(e):
            msg = ""
            explain = "Probably a quote character in the expression"

        elif len(illegalpresent) > 0:
            msg = ""
            explain = "illegal character: " + ",".join(illegalpresent)

        response = dict(error=_("%s \n %s %s" % ("Error 158", explain, msg)))
    except AssertionError as e :
        response = dict(error=f"{str(e)}")
    except IndexError as e:
        response = dict(
            error=f'Index error in your answer "{student_answer}" ',
            debug=_("%s answer=>%s< %s %s" % (type(e).__name__, str(student_answer), str(e), traceback.format_exc())),
        )
    except Exception as e:
        response = dict(
            error=_(str(type(e)) + " Error 213: Unidentified Error\n " + str(student_answer) + "\n" + str(e)),
            debug=_("%s %s %s" % (type(e), str(e), traceback.format_exc())),
        )
    dprint("     RESSPONSE = ", response)
    dprint("     PRELHS = ", prelhs)
    # print("TIME CHECK_ANSWER_STRUCTURE " , int( 1000 * (  time.time() - tbeg ) ) )
    return response


def check_consistency(lhs, rhs, blacklist):
    time.time()
    if hasattr(lhs, "shape") and hasattr(rhs, "shape"):
        if lhs.shape != rhs.shape:
            return {
                    "error": _("Incorrect dimensions::")
                + ": your answer has the dimensions "
                + str(lhs.shape)
                + " whereas  the answer requires the dimensions "
                + str(rhs.shape)
            }
    # print("A6")
    if hasattr(lhs, "shape") and not hasattr(rhs, "shape") and (not rhs == 0):
        return {
                "error": _("Error 182 incorrect dimensions::")
            + ": your expression  is a matrix or vector; a scalar answer is required."
        }
    if hasattr(rhs, "shape") and not hasattr(lhs, "shape") and (not lhs == 0):
        return {
                "error": _("Error 188 incorrect dimensions::") + ": your expression is is not a proper  vector or matrix "
        }
    # print("A7")
    if isinstance(lhs, sympy.Basic) or isinstance(lhs, sympy.MatrixBase):
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
            if special[0] in blacklist and (special[0] in str(lhs)):
                return {"error": _("(E) Forbidden token: ") + special[0]}
        atoms = lhs.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
        for atom in atoms:
            strrep = str(atom)
            funcstr = str(atom.func)
            if strrep in blacklist:
                return {"error": _("(F) Forbidden token: ") + strrep}
            if funcstr in blacklist:
                return {"error": _("(G) Forbidden token: ") + funcstr}
        # print("POSITION 5", 1000 * ( time.time() - time_start ) );
    # print("TIME CHECK_CONSISTENCY " , int( 1000 * (  time.time() - tbeg ) ) )
    return None


def check_for_undefined_variables_and_functions(student_answer, used_variables):
    response = []
    student_answer = declash(student_answer)
    used_variables = [declash(item) for item in used_variables]
    # print(f"STUDENT_ANSWER = {student_answer}")
    # print(f"used_variables = {used_variables}")
    student_answer_unparsed = student_answer
    studentatoms = get_used_variable_list(student_answer)
    okatoms = used_variables + ["kg", "meter", "second", "t", "x", "y", "z", "xhat", "yhat", "zhat"]
    diff = list(set(studentatoms).difference(set(okatoms)))
    if len(diff) > 0:
        # print( " DIFF = ", diff, "LEN ", len(diff) )
        return {"error": "(H) Forbidden token: %s " % ",".join(diff)}  # , "correct": False}
    okatoms = used_variables + ["kg", "meter", "second"]
    funcs = reg.findall(r"([A-Za-z][A-Za-z0-9]*)\(", student_answer_unparsed)
    badfuncs = list(filter(lambda fname: not hasattr(sympy, fname), funcs))
    if len(badfuncs) > 0:
        opentafuncs = list(openta_scope.keys()) + ["sample"]
        badfuncs = list(set(badfuncs).difference(set(opentafuncs)))
        if len(badfuncs) > 0:
            response = {
                "error": "(H) Forbidden function : %s " % ",".join(badfuncs),
                # "correct": False,
            }
            # print("RESPONSE TO BADFUNCS = ", response)
            return response
    return []


def get_extradefs(exerciseassetpath):
    extradefs = {"exerciseassetpath": exerciseassetpath}
    if os.path.exists(os.path.join(exerciseassetpath, "customfunctions.py")):
        extradefs["customfunctions"] = "customfunctions.py"
    xml = exercise_xml(os.path.join(exerciseassetpath, "exercise.xml"))
    # extradefs['xmlhash'] =  (hashlib.md5(xml.encode()).hexdigest())[0:7]
    extradefs["mtime"] = os.path.getmtime(os.path.join(exerciseassetpath, "exercise.xml"))

    return extradefs


#def oldutil_question_check(question_json, question_xmltree, answer_data, global_xmltree, symex):
#    tbeg = time.time()
#    tnow = time.time()
#    result = {}
#    # if hints is not None:
#    #    if hints.get('correct', None) is not None:
#    #        return hints
#    exerciseassetpath = question_xmltree.attrib["exerciseassetpath"]
#    # extradefs = {"exerciseassetpath": exerciseassetpath}
#    # if os.path.exists(os.path.join(exerciseassetpath, "customfunctions.py")):
#    #    extradefs["customfunctions"] = "customfunctions.py"
#    extradefs = get_extradefs(exerciseassetpath)
#    check_units = True
#    ret = getallvariables(global_xmltree, question_xmltree, assign_all_numerical=False)
#    used_variables = list(ret["used_variables"])
#    variables = ret["variables"]
#    funcsubs = ret["functions"]
#    authorvariables = ret["authorvariables"]
#    # exposeglobals = (question_json.get("@attr").get("exposeglobals", "false")).lower() == "true"
#    # if exposeglobals :
#    #   okvariables = set( [item['name'] for item in authorvariables] + used_variables   )
#    # else :
#    #   okvariables = set(  used_variables   )
#    blacklist = ret["blacklist"]
#    # okvariables = okvariables.difference( set( blacklist) )
#    correct_answer = ret["correct_answer"]
#    equality = question_xmltree.find("equality")
#    negate = False
#    if equality is not None:
#        correct_answer = equality.text
#    istrue = question_xmltree.find("istrue")
#    if istrue is not None:
#        correct_answer = istrue.text
#        if "==" not in istrue.text:
#            correct_answer = istrue.text + "== 1 "
#        check_units = False
#
#    isfalse = question_xmltree.find("isfalse")
#    if isfalse is not None:
#        negate = True
#        correct_answer = isfalse.text
#        if "==" not in isfalse.text:
#            correct_answer = isfalse.text + "== 1 "
#        check_units = False
#    precision = question_json.get("@attr").get("precision", 1.0e-6)
#    # SYMEX CALLS LINEAR_ALGEBRA_EXPRESSION
#    deltat = -int((tnow - time.time()) * 1000)
#    tnow = time.time()
#    dprint(f"DELTA1 = {deltat}")
#    dprint(f"EXTRADEFS ={extradefs}")
#    result = symex(
#        precision,
#        authorvariables,
#        answer_data,
#        correct_answer,
#        check_units=check_units,
#        blacklist=list(blacklist),
#        used_variables=used_variables,
#        funcsubs=funcsubs,
#        source="util_question_check",
#        extradefs=extradefs,
#    )
#
#    deltat = -int((tnow - time.time()) * 1000)
#    tnow = time.time()
#    dprint(f"DELTA2 = {deltat}")
#    if negate:
#        if "correct" in list(result.keys()):
#            if result["correct"]:
#                result["status"] = "incorrect"
#            else:
#                result["status"] = "correct"
#            # result['status'] = 'incorrect' if result['correct'] else 'correct'
#        elif "error" in list(result.keys()):
#            result["status"] = "error"
#    else:
#        if "correct" in list(result.keys()):
#            if result["correct"]:
#                result["status"] = "correct"
#            else:
#                result["status"] = "incorrect"
#        # result['status'] = 'incorrect' if result['correct'] else 'correct'
#        # if 'correct' in result.keys() :
#        #    result['status'] = 'correct' if result['correct'] else 'incorrect'
#        elif "error" in list(result.keys()):
#            result["status"] = "error"
#    # if hints is not None:
#    #    result.update(hints)
#    # okvariables = [ reg.sub(r"variable",'',item) for item in list( okvariables) ]
#    # result['used_variable_list'] = list( set( okvariables ) )
#    # THIS IS WHERE IN TERMS OF GETS POPULATED
#    funcatoms = [item["name"] for item in funcsubs]
#    result["used_variable_list"] = used_variables + funcatoms
#    if settings.IGNORE_NOFEEDBACK:
#        result["maxerror"] = result.get("maxerror", "nomaxerror from questioncheck")
#    else:
#        result["maxerror"] = None
#    tend = time.time()
#    deltat = int((tend - tbeg) * 1000)
#    # result['deltat'] = deltat
#    # deltat = int( ( tnow - time.time() ) * 1000 )
#    # tnow  = time.time()
#    dprint(f"DELTA2 = {deltat}")
#    result["deltat"] = deltat
#    # result.update(hints)
#    return result
