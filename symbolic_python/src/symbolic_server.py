import zerorpc
import sympy
import json
import re

meter, second, kg = sympy.symbols('meter,second,kg')
uniteval = {meter: 1, second: 1, kg: 1}


def asciiToSympy(expression):
    dict = {'^': '**'}
    result = expression
    result = re.sub(r'([a-zA-Z0-9]) ([a-zA-Z0-9])', r'\1*\2', result)
    for old, new in dict.iteritems():
        result = result.replace(old, new)
    return result


# def evaluateUnits(expression):
#    return expression.subs(subs)


class SymbolicRPC(object):
    # Expects a JSON object with structure
    # [ {name: name, value: value}, .... ]
    def parseVariables(self, variables):
        sym = {}
        # Decode JSON string into python lists/dictionaries
        vars = json.loads(variables)
        # Declare new sympy symbol for every variable
        for var in vars:
            sym[var['name']] = sympy.symbols(var['name'])
        # Create substituion dictionary
        subs = {}
        for var in vars:
            subs[sym[var['name']]] = sympy.sympify(var['value'])
        return subs

    def evaluate(self, variables, expression):
        subs = self.parseVariables(variables)
        # Parse expression and evaluate with specified values
        value = sympy.sympify(expression).evalf(subs=subs)
        response = {}
        if not value.is_real:
            response['error'] = "Could not parse expression"
        else:
            response['value'] = float(value)
        return json.dumps(response)

    def compareNumeric(self, variables, expression1, expression2):
        # Do some initial formatting
        svariables = asciiToSympy(variables)
        sexpression1 = asciiToSympy(expression1)
        sexpression2 = asciiToSympy(expression2)
        # Parse variables from JSON format into substitution dictionary
        varsubs = self.parseVariables(svariables)
        # Let sympy parse the expressions and substitute the variables together with the units and then evaluate to a sympy float.
        value1 = sympy.sympify(sexpression1).subs(varsubs).subs(uniteval).evalf()
        value2 = sympy.sympify(sexpression2).subs(varsubs).subs(uniteval).evalf()
        diff = sympy.Abs(value2 - value1)
        if float(diff) < 1e-10:
            return True
        else:
            return False

    def toLatex(self, expression):
        latex = sympy.latex(sympy.sympify(asciiToSympy(expression)))
        print latex
        return latex


rpcserver = zerorpc.Server(SymbolicRPC())
rpcserver.bind("tcp://0.0.0.0:4242")
rpcserver.run()
