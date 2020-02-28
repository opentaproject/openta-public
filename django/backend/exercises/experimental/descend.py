from sympy import *
xtest = Function('myadd')(Symbol('ddachfedic'), Symbol('ieeebggdeb'), Symbol('xhat'), Symbol('zhat'), Function('grad')(Pow(Function('myadd')(Pow(Symbol('x'), Integer(2)), Pow(Symbol('y'), Integer(2)), Pow(Symbol('z'), Integer(2))), Rational(-1, 2))))

def newpre(expr, level=0):
    '''
     #
     # TEST WITH 
     from sympy import *
     pre( sympify('1 + tanh(x)')
     #
     '''
    name = 'NONAME' if not hasattr(expr, 'name') else getattr(expr, 'name')
    newargs = None
    if expr.is_Function:
        if str(expr.func) == "myadd":
            print("FOUND MYADD")
            expr = Function('Add')(*expr.args)
        print("FOUND FUNCTION", expr.func)
    elif expr.is_Symbol:
        # if name == "x" :
        #    expr.name = name + 'j'
        # else :
        #    expr = expr
        expr = expr
        print("FOUND SYMBOL ", name)
    elif expr.is_Atom:
        expr = expr
        print("ATOM FOUND", name)
    print("COMPLEX EXPRESSION", expr)
    if not expr.args  == None :
        newargs = [pre(item, level) for item in expr.args]
        expr = expr.__class__(*newargs)
    return expr

def oldpre(expr, level=0):
    '''
     #
     # TEST WITH 
     from sympy import *
     pre( sympify('1 + tanh(x)')
     #
     '''
    name = 'NONAME' if not hasattr(expr, 'name') else getattr(expr, 'name')
    newargs = None
    if expr.is_Function:
        if str(expr.func) == "myadd":
            print("myadd ")
        expr = Function('newadd')(*expr.args)
        newargs = [pre(item, level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
        print( level , " FOUND FUNCTION", expr.func , " IN ", expr )
    elif expr.is_Symbol:
        if name == "x" :
            expr = Symbol('XX') * expr
            #expr.name = name + 'j'
        else :
            expr = expr
        print(level, " FOUND SYMBOL ", name)
    elif expr.is_Atom:
        expr = expr
        print("ATOM FOUND", name)
    else:
        print("COMPLEX EXPRESSION NAME = ", name , expr, "FUNC = ", expr.func, "ARGS = ", expr.args)
        newargs = [pre(item, level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
    print(level , " NEW = ", expr)
    return expr

from sympy.abc import *
matrix_sub =  {'xhat': Matrix([ [1], [0], [0]]), 'yhat': Matrix([ [0], [1], [0]]), 'zhat': Matrix([ [0], [0], [1]]),
               'ddachfedic': Matrix([ [x/(x**2 + y**2 + z**2)**(3/2)], [y/(x**2 + y**2 + z**2)**(3/2)], [z/(x**2 + y**2 + z**2)**(3/2)]]), 
               'ieeebggdeb': Matrix([ [0], [1], [0]])}

def pre(expr, matrix_sub ,func_sub , level=0):
    '''
     #
     # TEST WITH 
     from sympy import *
     pre( sympify('1 + tanh(x)')
     #
     '''
    name = 'NONAME' if not hasattr(expr, 'name') else getattr(expr, 'name')
    newargs = None
    if expr.is_Function:
        if str(expr.func) == "myadd":
            print("myadd ")
            expr = Function('newadd')(*expr.args)
        newargs = [pre(item, matrix_sub, func_sub level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
        print( level , " FOUND FUNCTION", expr.func , " IN ", expr )
    elif expr.is_Symbol:
        if matrix_sub.get(name) :
            expr = matrix_sub[name]
            #expr.name = name + 'j'
        else :
            expr = expr
        print(level, " FOUND SYMBOL ", name)
    elif expr.is_Atom:
        expr = expr
        print("ATOM FOUND", name)
    else:
        print("COMPLEX EXPRESSION NAME = ", name , expr, "FUNC = ", expr.func, "ARGS = ", expr.args)
        newargs = [pre(item, matrix_sub, func_sub,  level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
    print(level , " NEW = ", expr)
    return expr

class mygrad(Function):
    nargs = 1

    @classmethod
    def eval(cls, fun):
        from sympy.abc import x, y, z, t
        res = [diff(fun, x), diff(fun, y), diff(fun, z)]
        res = sympify(Matrix(res))
        res = res.doit()
        return res

myscope = { 'grad': mygrad , }
rep = [ (Function(key), val ) for key,val in myscope.items() ]
new1 = pre(xtest,matrix_sub)
new2 = new1.subs(rep)
new3 = new2.replace(Function('newadd'), Add).doit() 
new4 = simplify( new3 )
print("NEW4 = ", new4 )
funcdefs =  [{'name': 'f', 'args': 'q', 'value': 'cosh(q)', 'tex': 'TeX'}, {'name': 'g', 'args': 'r', 'value': 'r**2 + 25', 'tex': 'TeX'}]
func_sub = {  sub['name'] : {
    'args' :  [  Symbol(arg) for arg  in  sub['args'].lstrip('[').rstrip(']').split(',') ] , 
    'value' : sympify( sub['value']  )  }  for sub in funcdefs }

#for sub in funcsubs :
#        func_def = sympy.Function(sub['name'])
#        args = (sub['args']).lstrip('[').rstrip(']')
#        funcdefstring = sub['name'] + '(' + args + ')'
#        func_def = sympy.sympify(funcdefstring)
#        func_body = sympy.sympify(sub['value'])
#        sexpr = func_sub(sexpr, func_def, func_body, subrule)

name = str( expr.func )
newargs = list( expr.args )
oldargs = func_sub.get(name)['args']
new = func_sub.get(name)['value']
subrule = zip( oldargs, newargs)
old = expr
oldfunc = old.func
newfunc = newvalue.func
arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(oldargs, newargs)}
new = new.subs( arg_sub)





