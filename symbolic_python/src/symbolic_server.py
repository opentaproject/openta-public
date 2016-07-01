import zerorpc
import sympy
import json


class SymbolicRPC(object):
    # Expects a JSON object with structure
    # [ {name: name, value: value}, .... ]
    def parseVariables(self, variables):
        sym = {}
        # Decode JSON string into python lists/dictionaries
        vars = json.loads(variables)
        # Declare new sympy symbol for every variable
        for var in vars:
            print var['name']
            sym[var['name']] = sympy.symbols(var['name'])
        # Create substituion dictionary
        subs = {}
        for var in vars:
            subs[sym[var['name']]] = var['value']
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
        subs = self.parseVariables(variables)
        value1 = sympy.sympify(expression1).evalf(subs=subs)
        value2 = sympy.sympify(expression2).evalf(subs=subs)
        diff = Sympy.Abs(value2 - value1)
        if diff < 1e-10:
            return True
        else:
            return False


rpcserver = zerorpc.Server(SymbolicRPC())
rpcserver.bind("tcp://0.0.0.0:4242")
rpcserver.run()
