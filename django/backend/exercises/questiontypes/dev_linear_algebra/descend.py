from sympy import *
from sympy.abc import *
from sympy.matrices import *
from copy import deepcopy
import time

# from sympy.abc import _clash1, _clash2, _clash
import re as resub
from exercises.util import get_hash_from_string

from .string_formatting import (
    absify,
    insert_implicit_multiply,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
)
from .functions import *



#xtest = Function('myadd')(Symbol('ddachfedic'), Symbol('ieeebggdeb'), Symbol('xhat'), Symbol('zhat'), Function('grad')(Pow(Function('myadd')(Pow(Symbol('x'), Integer(2)), Pow(Symbol('y'), Integer(2)), Pow(Symbol('z'), Integer(2))), Rational(-1, 2))))
#
#matrix_sub =  {'xhat': Matrix([ [1], [0], [0]]), 'yhat': Matrix([ [0], [1], [0]]), 'zhat': Matrix([ [0], [0], [1]]),
#               'ddachfedic': Matrix([ [x/(x**2 + y**2 + z**2)**(3/2)], [y/(x**2 + y**2 + z**2)**(3/2)], [z/(x**2 + y**2 + z**2)**(3/2)]]), 
#               'ieeebggdeb': Matrix([ [0], [1], [0]])}
#expr = xtest 

def dematrixify( sexpr,varsubs) :
    matrix_subs = {}
    matrix_subs['xhat'] = Matrix([1,0,0])
    matrix_subs['yhat'] = Matrix([0,1,0])
    matrix_subs['zhat'] = Matrix([0,0,1])
    newvarsubs = {}
    vsubs = []
    for key,val in varsubs.items() :
        (newval,vsub) = tokenify(str(val) )
        newvarsubs[key] = sympify( newval )
        for item in vsub:
            (n,m) = item['value'].shape
            matrix_subs[ item['name']] =  item['value']  
    (xtest, vsubs) = tokenify(sexpr)
    for item in vsubs:
        (n,m) = item['value'].shape
        matrix_subs[ item['name'] ] =  item['value']  
    return (xtest, newvarsubs, matrix_subs)


def tokenify(xtest,vsubs=[]):
    try:
        nit = 0
        vsubs = []
        while True:
            vsub = {}
            previous = xtest
            p = resub.compile(r'Matrix')
            allm = list(p.finditer(xtest))
            if len(allm) == 0:
                break
            m = allm[0]
            (ibeg, ileft) = m.span()
            iright = index_of_matching_right_paren(ileft, xtest)
            head = xtest[0:ibeg]
            body = xtest[ibeg:iright]
            tail = xtest[iright:]
            bodyhash = get_hash_from_string(body)
            vsub['name'] = bodyhash ;
            vsub['value'] = sympify(body);
            xtest = head + '(' + bodyhash + ')' + tail
            vsubs = vsubs + [vsub]
            nit = nit + 1
    except:
        print("FAILED WITH ", xtest)
        raise TypeError("FAILED WITH " + xtest)
    return (xtest, vsubs)



def new_func_replace(expr,func_subs):
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


def pre(expr, newvarsubs, matrix_sub ,func_subs , rep , level=0):
    '''
     #
     # TEST WITH 
     from sympy import *
     pre( sympify('1 + tanh(x)')
     #
     '''
    #tbegin  = datetime.datetime.now()
    if level == 0 :
        expr = expr.replace(Add, Function('myadd') )
    name = 'NONAME' if not hasattr(expr, 'name') else getattr(expr, 'name')
    newargs = None
    print("PARSING ", expr )
    if expr.is_Function:
        print("FOUND THE  FUNCTION", str(expr.func))
        #if str(expr.func) == "myadd":
        #    print("myadd ")
        #    expr = Function('newadd')(*expr.args)
        if len( func_subs) > 0 :
            expr = new_func_replace(expr,func_subs)
        newargs = [pre(item, newvarsubs,  matrix_sub, func_subs , rep,level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
        print( level , " FOUND FUNCTION", expr.func , " IN ", expr )
    elif expr.is_Symbol:
        print("FOUND SYMBOL", expr.name )
        while True :
            prev = expr 
            expr = expr.subs(newvarsubs).doit()
            expr = expr.subs(matrix_sub).doit()
            if expr == prev:
                break
        print(level, " FOUND SYMBOL ", name)
    elif expr.is_Atom:
        expr = expr
        print("FOUND ATOM", name)
    else:
        print("COMPLEX EXPRESSION NAME = ", name , expr, "FUNC = ", expr.func, "ARGS = ", expr.args)
        newargs = [pre(item, newvarsubs, matrix_sub, func_subs, rep,  level + 1) for item in expr.args]
        expr = expr.__class__(*newargs)
    #tend = datetime.datetime.now()
    #print("TIMEING = " ( tend - tbegin).milliseconds )
    return expr

'''
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

rep = { 'grad': mygrad , }
newvarsubs = {} 
rep = [ (Function(key), val ) for key,val in rep.items() ]
new1 = pre(xtest,newvarsubs, matrix_sub,func_subs,rep)
new2 = new1.subs(rep)
new3 = new2.replace(Function('myadd'), Add).doit() 
new4 = simplify( new3 )
print("NEW4 = ", new4 )

expr = sympify( 'g( y**2 )' )
new5 = new_func_replace(expr, func_subs)
'''
