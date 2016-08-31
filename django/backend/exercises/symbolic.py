import sympy
import json
import re
from sympy.core.sympify import SympifyError
import traceback

meter, second, kg = sympy.symbols('meter,second,kg')
uniteval = {meter: 1, second: 1, kg: 1}


def asciiToSympy(expression):
    dict = {'^': '**'}
    result = re.sub(r"([a-zA-Z0-9]) ([a-zA-Z0-9])", r"\1*\2", expression)
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
        subs[sym[var['name']]] = sympy.sympify(var['value'])
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
        value1 = sympy.sympify(sexpression1).subs(varsubs).subs(uniteval).evalf()
        value2 = sympy.sympify(sexpression2).subs(varsubs).subs(uniteval).evalf()
        diff = sympy.Abs(value2 - value1)
        if diff.is_constant():
            value = float(diff)
            if value < 1e-10:
                response['correct'] = True
            else:
                response['correct'] = False
        else:
            print(type(diff.free_symbols))
            unrecognised = ', '.join(list(map(sympy.latex, diff.free_symbols)))
            # for sym in diff.free_symbols:
            #    print(sym)
            #    print(type(sym))
            response['error'] = "Failed to evaluate expression"
            if len(unrecognised) > 0:
                response['error'] = (
                    response['error'] + ': ' + unrecognised + ' are not valid variables.'
                )
    except SympifyError:
        print("SympifyError")
        print(traceback.format_exc())
        response['error'] = "Failed to evaluate expression"
        pass
    return response


def to_latex(expression):
    latex = ""
    try:
        latex = sympy.latex(sympy.sympify(asciiToSympy(expression)))
        print(latex)
    except Exception:
        print("toLatex exception")
        pass
    return latex
