from sympy import *
from sympy.abc import *

xtest = Function('myadd')(Symbol('ddachfedic'), Symbol('ieeebggdeb'), Symbol('xhat'), Symbol('zhat'), Function('grad')(Pow(Function('myadd')(Pow(Symbol('x'), Integer(2)), Pow(Symbol('y'), Integer(2)), Pow(Symbol('z'), Integer(2))), Rational(-1, 2))))

matrix_sub =  {'xhat': Matrix([ [1], [0], [0]]), 'yhat': Matrix([ [0], [1], [0]]), 'zhat': Matrix([ [0], [0], [1]]),
               'ddachfedic': Matrix([ [x/(x**2 + y**2 + z**2)**(3/2)], [y/(x**2 + y**2 + z**2)**(3/2)], [z/(x**2 + y**2 + z**2)**(3/2)]]), 
               'ieeebggdeb': Matrix([ [0], [1], [0]])}
expr = xtest 

def func_replace(expr,func_subs):
    name = str( expr.func )
    if func_subs.get(name) :
        newargs = list( expr.args )
        oldargs = func_subs.get(name)['args']
        new = func_subs.get(name)['value']
        subrule = zip( oldargs, newargs)
        old = expr
        oldfunc = old.func
        arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(oldargs, newargs)}
        new = new.subs( arg_sub)
        return new 
    else :
        return expr


def pre(expr, newvarsubs, matrix_sub ,func_subs , myscope , level=0):
    '''
     #
     # TEST WITH 
     from sympy import *
     pre( sympify('1 + tanh(x)')
     #
     '''
    rep = [ (Function(key), val ) for key,val in myscope.items() ]
    if level == 0 :
        expr = expr.replace(Add, Function('add') )
    name = 'NONAME' if not hasattr(expr, 'name') else getattr(expr, 'name')
    newargs = None
    if expr.is_Function:
        #if str(expr.func) == "myadd":
        #    print("myadd ")
        #    expr = Function('newadd')(*expr.args)
        expr = func_replace(expr,func_subs)
        newargs = [pre(item, newvarsubs,  matrix_sub, func_subs , myscope,level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
        print( level , " FOUND FUNCTION", expr.func , " IN ", expr )
    elif expr.is_Symbol:
        expr = expr.subs(newvarsubs)
        if matrix_sub.get(name) :
            expr = matrix_sub[name]
        else :
            expr = expr
        print(level, " FOUND SYMBOL ", name)
    elif expr.is_Atom:
        expr = expr
        print("ATOM FOUND", name)
    else:
        print("COMPLEX EXPRESSION NAME = ", name , expr, "FUNC = ", expr.func, "ARGS = ", expr.args)
        newargs = [pre(item, newvarsubs, matrix_sub, func_subs, myscope,  level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
    if level == 0 :
        expr = expr.replace( Function('add') , Add).doit()
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


funcdefs =  [{'name': 'f', 'args': 'q', 'value': 'F(q)', 'tex': 'TeX'}, {'name': 'g', 'args': 'r', 'value': 'G(r)', 'tex': 'TeX'}]
func_subs = {  sub['name'] : {
    'args' :  [  Symbol(arg) for arg  in  sub['args'].lstrip('[').rstrip(']').split(',') ] , 
    'value' : sympify( sub['value']  )  }  for sub in funcdefs }

myscope = { 'grad': mygrad , }
rep = [ (Function(key), val ) for key,val in myscope.items() ]
new1 = pre(xtest,matrix_sub,func_subs)
new2 = new1.subs(rep)
new3 = new2.replace(Function('newadd'), Add).doit() 
new4 = simplify( new3 )
print("NEW4 = ", new4 )

expr = sympify( 'g( y**2 )' )

def func_replace(expr,func_subs):
    name = str( expr.func )
    if func_subs.get(name) :
        newargs = list( expr.args )
        oldargs = func_subs.get(name)['args']
        new = func_subs.get(name)['value']
        subrule = zip( oldargs, newargs)
        old = expr
        oldfunc = old.func
        arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(oldargs, newargs)}
        new = new.subs( arg_sub)
        return new 
    else :
        return expr

new = func_replace(expr, func_subs)
