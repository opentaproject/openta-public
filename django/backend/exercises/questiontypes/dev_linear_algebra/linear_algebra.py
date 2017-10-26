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

logger = logging.getLogger(__name__)

# meter, second, kg , ampere , kelvin, mole, candela = sympy.symbols('meter,second,kg,ampere,kelvin,mole,candela', real=True, positive=True)

# see http://iamit.in/sympy/coverage-report/matrices/sympy_matrices_expressions_diagonal_py.html
# see https://pypkg.com/pypi/sympy/f/sympy/matrices/expressions/diagonal.py/


class Dot(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return conjugate(x).dot(y)
        else:
            return None


class Norm(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return x.norm()
        else:
            return None


class diagonalof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return Matrix(DiagonalOf(x))
        else:
            return None


class Trace(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return x.trace()
        else:
            return None


class eigenvaluesof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            evdict = x.eigenvals()
            evt = list(map(lambda key: [key] * evdict[key], evdict.keys()))
            evlist = [val for sublist in evt for val in sublist]
            ev = sorted(evlist, key=default_sort_key)
            # print("EV = ", ev )
            return sympy.Matrix(ev)
        else:
            return None


class AreEigenvaluesOf(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, y, x):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            evdict = y.eigenvals()
            evt = list(map(lambda key: [key] * evdict[key], evdict.keys()))
            evlist = [val for sublist in evt for val in sublist]
            ev = Matrix(sorted(evlist, key=default_sort_key))
            # print("ev = ", ev )
            # print("x = ", x )
            diff = ev - Sort(x)
            # print("diff = ", diff )
            mag = conjugate(diff).dot(diff)
            # print("mag = ", mag )
            if mag <= 1e-6:
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class IsDiagonalizationOf(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, m, u):
        if isinstance(u, sympy.MatrixBase) and isinstance(m, sympy.MatrixBase):
            ut = transpose(u)
            diag = ut.inv() * m * ut
            if diag.is_diagonal():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')

        else:
            return None


class Transpose(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            return x.T
        else:
            return None


class rankof(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            sp = x.shape
            rank = sp[1]
            return sympy.sympify(rank)
        else:
            return None


class isunitary(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            sp = x.shape
            target = eye(sp[1])
            # print("target = ", target )
            if ((x * conjugate(x.T)) - target).is_zero:
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class IsHermitian(sympy.Function):
    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            if (x - conjugate(x.T)).is_zero:
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class Cross(sympy.MatrixExpr):
    def __new__(cls, arg1, arg2):
        return sympy.Basic.__new__(cls, arg1, arg2)

    @property
    def shape(self):
        return self.args[0].shape

    def doit(self, **hints):
        x = self.args[0].doit() if isinstance(self.args[0], sympy.Basic) else self.args[0]
        y = self.args[1].doit() if isinstance(self.args[1], sympy.Basic) else self.args[1]
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return x.cross(y)
        else:
            return self


class Sort(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            xs = x.tolist()
            xs = sorted(xs, key=default_sort_key)
            # print("xs = ",  xs )
            return sympy.Matrix(xs)
        else:
            return None


class gt(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            if Gt(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class lt(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            if Lt(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class ge(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            if Ge(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class le(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.Basic) and isinstance(y, sympy.Basic):
            if Le(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class eq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            if Eq(x, y):
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (
            isinstance(x, Integer) or isinstance(x, Float)
        ):
            if x.n() == y.n():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')
        else:
            return None


class neq(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            if Eq(x, y):
                return sympy.sympify('0')
            else:
                return sympy.sympify('1')
        elif (isinstance(x, Integer) or isinstance(x, Float)) and (
            isinstance(x, Integer) or isinstance(x, Float)
        ):
            if x.n() == y.n():
                return sympy.sympify('0')
            else:
                return sympy.sympify('1')
        else:
            return None


class logicaland(sympy.Function):
    @classmethod
    def eval(cls, *x):
        tot = 1
        for tval in x:
            if Not(isinstance(tval, sympy.Integer)):
                return None
            tot = And(tot, tval)
        if tot:
            return sympy.sympify('1')
        else:
            return sympy.sympify('0')


class logicalor(sympy.Function):
    @classmethod
    def eval(cls, *x):
        tot = 0
        for tval in x:
            if Not(isinstance(tval, sympy.Integer)):
                return None
            tot = Or(tot, tval)
        if tot:
            return sympy.sympify('1')
        else:
            return sympy.sympify('0')


class logicalnot(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.Integer):
            if x > 0:
                return sympy.sympify('0')
            else:
                return sympy.sympify('1')
        else:
            return None


#            'gt' : lambda x,y: Gt( x , y ),
#            'ge' : lambda x,y: Ge( x , y ),
#            'lt' : lambda x,y: Lt( x , y ),
#            'le' : lambda x,y: Le( x , y ),
#            'eq' : lambda x,y: Equality( x,y ),
#            'neq' : lambda x,y: ( x != y ),
#            'aeq' : lambda x,y: ( abs( x - y ) < 1e-6 ),
#            'naeq' : lambda x,y: ( abs( x - y ) > 1e-6 ),
#            'and' : lambda x,y:  sympy.And( x, y ),
#            'not' : lambda x: ( Not(x) ),
#            'or'  : lambda x,y: ( x | y ),
#            'norm': numpy.linalg.norm,


class Dot(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return conjugate(x).dot(y)
        else:
            return None


class Times(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return sympy.matrix_multiply_elementwise(x, y)
        else:
            return None


class IsDiagonal(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            if x.is_diagonal():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')


class IsDiagonalizable(sympy.Function):
    nargs = 1

    @classmethod
    def eval(cls, x):
        if isinstance(x, sympy.MatrixBase):
            if x.is_diagonalizable():
                return sympy.sympify('1')
            else:
                return sympy.sympify('0')


class Braket(sympy.Function):
    nargs = 2

    @classmethod
    def eval(cls, x, y):
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return conjugate(x).dot(y)
        else:
            return None


class KetBraBroken(sympy.Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):
        if len(y) == 0:
            if isinstance(x, sympy.MatrixBase) and isinstance(m, sympy.MatrixBase):
                # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
                # print("LINEAR_ALGEBRA m = ", m );
                return x * m.adjoint()
            else:
                return None
        else:
            if (
                isinstance(x, sympy.MatrixBase)
                and isinstance(m, sympy.MatrixBase)
                and isinstance(y[0], sympy.MatrixBase)
            ):
                # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
                # print("LINEAR_ALGEBRA m = ", m );
                # print("LINEAR_ALBEBRA y = ", y[0] );
                return x * m * y[0].adjoint()  # }}}
            else:
                return None


class KetBra(sympy.Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
            # print("LINEAR_ALGEBRA m = ", m );
            return MatMul(x, conjugate(m).T)
        else:
            # print("MULTIPLYING LINEAR_ALGEBRA x = ", x );
            # print("LINEAR_ALGEBRA m = ", m );
            # print("LINEAR_ALBEBRA y = ", y[0] );
            return x * (m * conjugate(y[0])).T  # }}}


class NewKetBra(sympy.MatrixExpr):
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
        if isinstance(x, sympy.MatrixBase) and isinstance(y, sympy.MatrixBase):
            return x * conjugate(y).T
        else:
            return self


class KetMBra(sympy.MatrixExpr):
    """
    This reimplementation of the cross product is necessary for sympify to generate a correct expression tree with
    the correct matrix operators instead of the standard scalar ones. For example sympify('5*cross(a,b)'),
     without any special handling, generates an expression tree with Mul instead of MatMul. Because of how sympy handles
     matrices this will result in a runtime error when eventually the cross products gets replaced with an actual matrix.
    """

    def __new__(cls, arg1, arg2, arg3):
        return sympy.Basic.__new__(cls, arg1, arg2, arg3)

    @property
    def shape(self):
        return self.args[0].shape

    def doit(self, **hints):
        x = self.args[0].doit() if isinstance(self.args[0], sympy.Basic) else self.args[0]
        m = self.args[1].doit() if isinstance(self.args[1], sympy.Basic) else self.args[1]
        y = self.args[2].doit() if isinstance(self.args[1], sympy.Basic) else self.args[2]
        # print("XMY = ", x, m, y )
        if (
            isinstance(x, sympy.MatrixBase)
            and isinstance(m, sympy.MatrixBase)
            and isinstance(y, sympy.MatrixBase)
        ):
            return MatMul(x, (m * conjugate(y)).T)
        else:
            return self


class BraketBroken(Function):  # {{{
    nargs = (2, 3)

    @classmethod
    def eval(cls, x, m, *y):

        if len(y) == 0:
            return conjugate(x).T.dot(m)
        else:
            return x.adjoint().dot(m * y[0])  # }}}


class nullrank(Function):  # {{{
    nargs = 2

    @classmethod
    def eval(cls, zmat, mvars):
        global varstonumeric  # MAKE THIS CLASS OBJECT INSTEAD
        try:
            subs = varstonumeric
            variables = list(mvars)
            # print( "norm = ", zmat.subs(subs).norm() )
            free1 = list(zmat.subs(subs).free_symbols)
            # print( "free1 = ", free1 )
            if len(free1) > 0:
                return sympify('NONFREE')
            if not (zmat.subs(subs).norm()).equals(0):
                # print("DOES IS NOT EQUAL ZERO")
                return sympy.sympify('NONZERO')
            zlist = list(zmat)
            jac = []
            for zrow in zlist:
                row = []
                for var in variables:
                    row.append(diff(zrow, var))
                jac.append(row)
            jacobian = Matrix(jac).subs(subs)
            null = jacobian.nullspace()
            # print("FREE = ", free1)
            nullrank = len(null)
            # print("NULLRANK RETURNS", nullrank)
            return sympy.sympify(nullrank)
        except Exception as e:
            # print("RETURNING 99")
            return sympy.sympify('UKNOWNERROR')  # }}}


# List of special handling in the conversion from sympy to numpy expressions for final evaluation
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


def sympify_with_custom(expression, varsubs):
    """
    Convert asciimath expression into sympy using extra context
    Args:
        expression: asciimath
        varsubs: { string(name): substitution, ... }

    Returns:
        Sympy expression
    """
    # print("SYMPIFY WITH CUSTOM", expression)
    scope = {
        'abs': Norm,  # sympy.Function('norm')
        'Abs': Norm,  # sympy.Function('norm')
        'Trace': Trace,
        'Transpose': Transpose,
        'AreEigenvaluesOf': eigenvaluesof,
        'AreEigenvaluesOf': AreEigenvaluesOf,
        'IsDiagonalizationOf': IsDiagonalizationOf,
        'IsHermitian': IsHermitian,
        'RankOf': rankof,
        'IsUnitary': isunitary,
        'cross': Cross,
        'Gt': gt,
        'Ge': ge,
        'Lt': lt,
        'Le': le,
        'Or': logicalor,
        'And': logicaland,
        'Not': logicalnot,
        'IsEqual': eq,
        'IsNotEqual': neq,
        'diagonalpart': diagonalof,
        'IsDiagonal': IsDiagonal,
        'IsDiagonalizable': IsDiagonalizable,
        'true': sympy.sympify('1'),
        'false': sympy.sympify('0'),
        'True': sympy.sympify('1'),
        'False': sympy.sympify('0'),
        'times': Times,
        'dot': Dot,
        'sort': Sort,
        'Sort': Sort,
        'norm': Norm,
        'KetBra': KetBra,
        'KetMBra': KetMBra,
        'Braket': Braket,
        'NullRank': nullrank,
    }
    scope.update(ns)
    scope.update(varsubs)
    # print("LINEAR_ALGEBRA expression= ", expression)
    # print("LINEAR_ALGEBRA ascii_to_sympy = ", ascii_to_sympy(expression) )
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


def parse_sample_variables(variables):
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
    matrix_symbols = {}
    for var in vars:
        expr = sympify_with_custom(ascii_to_sympy(var['value']), matrix_symbols)
        if hasattr(expr, 'shape'):
            sym[var['name']] = sympy.MatrixSymbol(var['name'], *expr.shape)
            matrix_symbols[var['name']] = sym[var['name']]
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
