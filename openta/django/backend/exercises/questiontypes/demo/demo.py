# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

# from sympy.abc import _clash1, _clash2, _clash # dont impport clashes
import logging
import re as resub

from django.utils.translation import gettext as _
from exercises.questiontypes.safe_run import safe_run
from sympy import *
from sympy.core.sympify import SympifyError

logger = logging.getLogger(__name__)

ns = {}
# Taylor clashes
ns.update(
    {
        "zeta": zeta,
        "N": N,
        "Q": Q,
        "O": O,
        "beta": beta,
        "S": S,
        "gamma": gamma,
        "ff": Symbol("ff"),
        "FF": Symbol("FF"),
    }
)


lambdifymodules = ["numpy", {"cot": lambda x: 1.0 / numpy.tan(x)}]


class demoUnitError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def asciiToSympy(expression):
    dict = {
        "^": "**",
        #        '_': '',
        #        '.': '',
        #        '[': '',
        #        ']': ''
    }
    result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", expression)
    result = resub.sub(r"(\W*[0-9]+)([A-Za-z]+)", r"\1 * \2", result)
    result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    for old, new in dict.items():
        result = result.replace(old, new)
    return result


def demo_internal(expression1, expression2):  # {{{
    # Do some initial formatting
    response = {}
    try:
        sexpression1 = asciiToSympy(expression1)
        sexpression2 = asciiToSympy(expression2)
        sympy1 = sympify(sexpression1, ns)
        sympy2 = sympify(sexpression2, ns)
        print("sympy1 = ", simplify(sympy1))
        print("sympy2 = ", simplify(sympy2))
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Expression 1: " + str(sympy1))
            logger.debug("Expression 2: " + str(sympy2))
        diffy = simplify(sympy1 - sympy2)
        if diffy == 0:
            response["correct"] = True
        else:
            response["correct"] = False
            response["warning"] = "reduces to " + str(diffy)
    except SympifyError as e:
        logger.error([str(e), expression1, expression2])
        response["error"] = _("Failed to evaluate expression.")
    except Exception as e:
        logger.error([str(e), expression1, expression2])
        response["error"] = _("Unknown error, check your expression.")
    return response  # }}}


def demo_runner(expression1, expression2, result_queue):
    response = demo_internal(expression1, expression2)
    result_queue.put(response)


def demo(expression1, expression2):
    """
    Starts a process with demo_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ["_", "[", "]"]
    for i in invalid_strings:
        if i in expression1:
            return {"error": _("Answer contains invalid character ") + i}
    return safe_run(demo_runner, args=(expression1, expression2))


def to_latex(expression):
    latex = ""
    try:
        latex = latex(sympify(asciiToSympy(expression), ns))  # _clash))
    except SympifyError as e:
        print(e)
        latex = "error"
    return latex
