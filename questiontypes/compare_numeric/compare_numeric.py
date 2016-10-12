import sympy
from sympy.abc import _clash1, _clash2, _clash
import json
import re
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random

meter, second, kg = sympy.symbols('meter,second,kg', real=True, positive=True)
ns = {
    'meter': meter,
    'second': second,
    'kg': kg,
    'pi': sympy.pi,
    'ff': sympy.Symbol('ff'),
    'FF': sympy.Symbol('FF'),
}
ns.update(_clash)

uniteval = {meter: 1, second: 1, kg: 1}


class CompareNumericUnitError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def asciiToSympy(expression):
    dict = {'^': '**'}
    result = re.sub(r"([a-zA-Z0-9]) ([a-zA-Z0-9])", r"\1*\2", expression)
    result = re.sub(r"([0-9])([a-zA-Z])", r"\1*\2*", result)
    result = re.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    for old, new in dict.items():
        result = result.replace(old, new)
    return result


def parse_variables(variables):
    sym = {}
    # Decode JSON string into python lists/dictionaries
    vars = variables
    # Declare new sympy symbol for every variable
    for var in vars:
        sym[var['name']] = sympy.symbols(var['name'])
    # Create substituion dictionary
    subs = {}
    for var in vars:
        subs[sym[var['name']]] = sympy.sympify(asciiToSympy(var['value']), ns)  # _clash)
    return subs


def check_units(expression, correct, variables):
    """Check units of expression as compared to correct

    Arguments:
    expression -- sympy expression
    correct -- sympy expression
    variables -- dictionary of variables
    """
    evaluated = sympy.simplify(expression.subs(variables))
    if len(evaluated.as_terms()[0]) > 1:
        raise CompareNumericUnitError(_("Terms do not seem to have the same unit."))
    ceval = sympy.simplify(correct.subs(variables))
    quotient = sympy.simplify(ceval / evaluated)
    if len(list(quotient.free_symbols)) > 0:
        raise CompareNumericUnitError("Seems like the expression does not have the correct units.")


def evaluate(variables, expression):
    subs = parse_variables(variables)
    # Parse expression and evaluate with specified values
    value = sympy.sympify(expression).evalf(subs=subs)
    response = {}
    if not value.is_real:
        response['error'] = "Could not parse expression"
    else:
        response['value'] = float(value)
    return json.dumps(response)


def compare_numeric(variables, expression1, expression2):
    # Do some initial formatting
    number_of_points = 10
    response = {}
    try:
        sexpression1 = asciiToSympy(expression1)
        sexpression2 = asciiToSympy(expression2)
        # Parse variables into substitution dictionary
        varsubs = parse_variables(variables)
        neighbours = []
        random.seed(1)
        for i in range(0, number_of_points):
            neighbour = {}
            for var, value in varsubs.items():
                neighbour[var] = value + random.random() * value * 0.1
            neighbours.append(neighbour)

        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        sympy1 = sympy.sympify(sexpression1, ns)
        sympy2 = sympy.sympify(sexpression2, ns)
        value1 = sympy1.subs(varsubs).subs(uniteval).evalf()
        value2 = sympy2.subs(varsubs).subs(uniteval).evalf()
        diff = sympy.Abs(value2 - value1)
        symbolic = sympy.simplify(sympy1 - sympy2)
        response['symbolic_difference'] = str(symbolic)
        if diff.is_constant():
            try:
                check_units(sympy1, sympy2, varsubs)
            except CompareNumericUnitError as e:
                response['warning'] = str(e)
            diffs = []
            for point in neighbours:
                nvalue1 = sympy1.subs(point).subs(uniteval).evalf()
                nvalue2 = sympy2.subs(point).subs(uniteval).evalf()
                ndiff = sympy.Abs(nvalue2 - nvalue1)
                diffs.append(float(ndiff) < 1e-10)
            if diffs.count(True) >= number_of_points * 0.8:
                response['correct'] = True
            else:
                response['correct'] = False
        else:
            # print(type(diff.free_symbols))
            unrecognised = ', '.join(list(map(sympy.latex, diff.free_symbols)))
            # for sym in diff.free_symbols:
            #    print(sym)
            #    print(type(sym))
            response['error'] = "Failed to evaluate expression"
            if len(unrecognised) > 0:
                response['error'] = (
                    response['error'] + ': ' + unrecognised + ' are not valid variables.'
                )
    except SympifyError as e:
        # print("SympifyError")
        print(e)
        print(traceback.format_exc())
        response['error'] = "Failed to evaluate expression"
        # pass
    return response


def to_latex(expression):
    latex = ""
    try:
        latex = sympy.latex(sympy.sympify(asciiToSympy(expression), ns))  # _clash))
    except SympifyError as e:
        print(e)
        latex = "error"
    return latex
