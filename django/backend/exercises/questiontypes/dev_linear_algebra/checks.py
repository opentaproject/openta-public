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
        'zoo': numpy.inf,
        'I': numpy.complex(0, 1),
    },
    "numpy",
]


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
        unit_values = list(
            map(
                lambda item: (item[1], item[0]),
                zip(check, [kg, meter, second, ampere, kelvin, mole, candela]),
            )
        )
        # print("unit_values = ", unit_values )
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
    # print("CHECK UNITS results = ", results )
    for res in results:
        if numpy.absolute(res - results[0]) > 10e-5:
            # print("RAISING UNIT ERROR");
            raise LinearAlgebraUnitError(_("Incorrect units"))


def check_for_legal_answer(
    precision, variables, student_answer, expression, check_units=True, blacklist=[]
):
    varsubs, varsubs_sympify, sample_variables = parse_sample_variables(variables)
    # print("varsubs = ", varsubs)
    # print("varsubs_sympify = ", varsubs_sympify)
    # print("sample_variables", sample_variables)
    response = {}
    # print("check for legal answer of ", student_answer)
    student_answer = declash(student_answer)
    # print("check for legal answer of ", student_answer)
    try:
        try:
            unparsedstudentanswer = sympy.sympify(ascii_to_sympy(student_answer), varsubs_sympify)
            sympy1 = unparsedstudentanswer.subs(baseunits)
        except Exception as e:
            # print("DEV ERROR = ", e );
            return {'error': 'Syntax Error: ' + str(e)}
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
            # print("atoms = ", atoms )
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {'error': _('Forbidden token: ') + strrep}
                if funcstr in blacklist:
                    return {'error': _('Forbidden token: ') + funcstr}
            varlist = []
            reclash = {}
            for var in variables:
                name = declash(var['name'])
                varlist.append(name)
            # print('varlist = ', varlist )
            symbolatoms = list(prelhs.atoms(sympy.Symbol))
            # print('symbolatoms = ', type( symbolatoms), symbolatoms)
            for item in symbolatoms:
                # print("check item ", item )
                if str(item) not in varlist:
                    # print("item ", item, "not in ", varlist )
                    response['correct'] = False
                    response['error'] = _('Forbidden token: ') + (str(item)).replace('variable', '')
                    return response
    except:
        response['warning'] = 'warning'
    return None
