import sympy
from sympy.abc import _clash1, _clash2, _clash
import json
import re
from sympy.core.sympify import SympifyError
import traceback

meter, second, kg = sympy.symbols('meter,second,kg')
uniteval = {meter: 1, second: 1, kg: 1}

_newclash = _clash.update({'pi': sympy.pi, 'ff': sympy.Symbol('ff'), 'FF': sympy.Symbol('FF')})


def asciiToSympy(expression):
    dict = {'^': '**'}
    result = re.sub(r"([a-zA-Z0-9]) ([a-zA-Z0-9])", r"\1*\2", expression)
    result = re.sub(r"([0-9])([a-zA-Z])", r"\1*\2*", result)
    result = re.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
    for old, new in dict.items():
        result = result.replace(old, new)
    print([result, expression])
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
        subs[sym[var['name']]] = sympy.sympify(asciiToSympy(var['value']), _clash)
    return subs


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
    response = {}
    try:
        sexpression1 = asciiToSympy(expression1)
        sexpression2 = asciiToSympy(expression2)
        # Parse variables into substitution dictionary
        varsubs = parse_variables(variables)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        sympy1 = sympy.sympify(sexpression1, _clash)
        sympy2 = sympy.sympify(sexpression2, _clash)
        value1 = sympy1.subs(varsubs).subs(uniteval).evalf()
        value2 = sympy2.subs(varsubs).subs(uniteval).evalf()
        diff = sympy.Abs(value2 - value1)
        symbolic = sympy.simplify(sympy1 - sympy2)
        response['symbolic_difference'] = str(symbolic)
        if diff.is_constant():
            value = float(diff)
            if value < 1e-10:
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
    latex = sympy.latex(sympy.sympify(asciiToSympy(expression), _clash))
    return latex
