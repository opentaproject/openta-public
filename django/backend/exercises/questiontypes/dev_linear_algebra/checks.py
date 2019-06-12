from sympy import *
from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import itertools
from sympy.core import S
from .unithelpers import units, sympy_units


from .variableparser import getallvariables, get_used_variable_list
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
from .parsers import *
from .functions import *


lambdifymodules = [
    {
        'cot': lambda x: 1.0 / numpy.tan(x),
        'norm': numpy.linalg.norm,
        'Norm': numpy.linalg.norm,
        'abs': numpy.linalg.norm,
        'cross': lambda x, y: numpy.cross(x, y, axis=0),
        'dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
        'Dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
        'zoo': numpy.inf,
        'I': numpy.complex(0, 1),
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
    # print("check_units_new expression ", expression )
    # print("check_units_new correct ", correct )
    # print("sample_variables = ", sample_variables)
    nvarsubs = {}
    nsubs_values = []

    def perturb(value):
        return value + value * random.random() * 0.1

    for item in sample_variables:
        nvarsubs[item['symbol']] = item['symbol'] * item['around'][0]
        value = float(item['around'][0].subs(baseunits))
        sampled_value = value + random.random() * value * 0.1
        nsubs_values.append((item['symbol'], sampled_value))
    nexpression = expression.subs(nvarsubs).doit()
    ncorrect = correct.subs(nvarsubs).doit()

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
            raise LinearAlgebraUnitError(_("Incorrect units"))


def check_for_legal_answer(
    precision, variables, student_answer, expression, check_units=True, blacklist=[]
):
    response = {}
    atoms = get_used_variable_list(student_answer)
    # print("ATOMS = ", atoms )
    for atom in atoms:
        strrep = str(atom)
        # funcstr = str(atom.func)
        if strrep in blacklist:
            return {'error': _('(A) Forbidden token: ') + strrep}
    student_answer = declash(student_answer)
    # if funcstr in blacklist:
    #    return {'error': _('(C) Forbidden token: ') + funcstr}

    # print("LEGAL: expression = ", expression)
    # print("LEGAL: student_answer = ", student_answer)
    if '==' in expression and not '$$' in expression:
        if not '==' in student_answer:
            return {'error': _('answer in terms of an equality using == ')}
    if '==' in student_answer:
        if not '==' in expression or '$$' in expression:
            return {'error': _('an equality is not permitted as answer')}
        else:
            equality = student_answer.split('==')
            student_answer = equality[0] + '-' + equality[1]
    varsubs, varsubs_sympify, sample_variables = parse_sample_variables(variables)
    m = re.search(r'(atan|arctan|acos|arccos|acos|arcos|asin|arcsin)', student_answer)
    if m:
        return {'error': _('inverse trig function') + m.group(1) + _(' is forbidden')}
    m = re.search(r'(print|sum)', student_answer)
    if m:
        return {'error': _('forbidden function') + m.group(1)}
    try:
        try:
            sympyex = ascii_to_sympy(student_answer)
            unparsedstudentanswer = sympify_with_custom(
                ascii_to_sympy(student_answer), varsubs_sympify
            )
            sympy1 = unparsedstudentanswer.subs(baseunits)
        except SympifyError as e:
            return {'error': 'error in: ' + student_answer}
        except TypeError as e:
            if 'required positional argument' in str(e):
                return {'error': _('Syntax Error: a function is missing an argument')}
            if 'callable' in str(e):
                return {
                    'error': _(
                        'Syntax Error: You probably have a variable followed by a parenthesis without a space between. This is interpreted as a function call rather than implicit multiply and therefore  therefore fails.'
                    )
                }
        except Exception as e:
            return {
                'error': 'Unidentified error unidentified : >'
                + e.__class__.__name__
                + '< '
                + str(e)
            }
            # return {'error': 'Unidentified error: ' };
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
                ('lt', lt),
            ]
            for special in specials:
                if special[0] in blacklist and (special[0] in str(unparsedstudentanswer)):
                    return {'error': _('(A) Forbidden token: ') + special[0]}

            sa = sympy.sympify(student_answer)
            atoms = sa.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {'error': _('(B) Forbidden token: ') + strrep}
                if funcstr in blacklist:
                    return {'error': _('(C) Forbidden token: ') + funcstr}

            varlist = []
            reclash = {}
            for var in variables:
                name = declash(var['name'])
                varlist.append(name)
            symbolatoms = list(prelhs.atoms(sympy.Symbol))
            varlist = varlist + units
            for item in symbolatoms:
                if str(item) not in varlist:
                    response['correct'] = False
                    response['error'] = _('(D) Forbidden token: ') + (str(item)).replace(
                        'variable', ''
                    )
                    return response
    except:
        response['warning'] = 'warning'
    return None
