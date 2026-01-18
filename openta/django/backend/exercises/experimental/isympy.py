# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from sympy import *
from sympy.utilities.lambdify import lambdify, implemented_function, lambdastr, flatten
d4 = Function('d4')
from sympy.abc import x,y,z,t
A = sympify('x^2 + cos(x)')
sexpr = d4(A)
#res = lambdastr((x,y), x + y )
argstring = '[a,b,c,d]'
valuestring = 'a + b + c  + d '
targs = argstring.lstrip('[').rstrip(']').split(',') 
scope = {arg : Symbol(arg)  for arg in targs }
value = sympify( valuestring,scope)
sargs = []
for key,val in scope.items() :
    sargs = sargs + [val ]
    print("KEY",  key, "VAL", val )
val =  sargs[0] + sargs[1] + sargs[2] + sargs[3]
fip = implemented_function(Function('fip'), lambda *sargs : sargs[0] + sargs[1] + sargs[2] + sargs[3] )
fp = lambdify( sargs , fip(*sargs) )
fp(1,2,3,4)



fip = implemented_function(Function('fip'), lambda *sargs : [*sargs] )
fp = lambdify( sargs , fip(*sargs) )
fp(1,2,3,4)


fip = implemented_function(Function('fip'), lambda *sargs : srepr( sargs ) )
fp = lambdify( sargs , fip(*sargs) )
fp(1,2,3,4)

def ui(name,argstring,valuestring ):
targs = argstring.lstrip('[').rstrip(']').split(',') 
scope = {arg : Symbol(arg)  for arg in targs }
value = sympify( 'a + b + c + 2 * d  ',scope)
sargs = []
for key,val in scope.items() :
        sargs = sargs + [val ]
        print("KEY",  key, "VAL", val )
print("SARGS = ", srepr(  sargs ) )
fip = implemented_function(Function('fip'), lambda *sargs : srepr( sargs ) )
print("FIP = ", srepr( fip ) )
gp = lambdify( sargs , fip(*sargs) , scope)
print("FP = ", srepr(gp) )
return gp




def ui(argstring, valuestring ):
    targs = argstring.lstrip('[').rstrip(']').split(',') 
    scope = {arg : Symbol(arg)  for arg in targs }
    sargs = []
    for key,val in scope.items() :
        sargs = sargs + [val ]
        print("KEY",  key, "VAL", val )
    sargs = [ val for (key,val) in scope.items() ]
    print("SARGS = ", srepr(  sargs ) )
    f = lambdify(  sargs , sympify( valuestring , scope ) )
    print("F = ", f(1,2,3,4) )
    return f


def ui(argstring, valuestring ):
    scope = {arg : Symbol(arg)  for arg in  argstring.lstrip('[').rstrip(']').split(',')  }
    sargs = [ val for (key,val) in scope.items() ]
    f = lambdify(  sargs , sympify( valuestring , scope ) )
    return f


funcs = [ {'name':'fun1','args':'[a,b,c]','value':'a + 100 * b + c ' },
  {'name':'fun2','args':'[a,b,c]','value':'a + 1000 * b + c ' },
  {'name':'fun3','args':'[a,b,c]','value':'a + 10000 * b + c ' },
]
funcscope = {}
for item in funcs :
    funcscope[item['name']]  = ui(item['args'], item['value'] )  

res = sympify('fun1(1,2,x) + fun2(1,y,3) + fun3(t,0,1)', funcscope)
    
    


valuestring = 'a + b + c + 2 * d '
argstring = '[a,b,c,d]'
g = ui2(argstring,valuestring)






args = [x,y]
fi4 = implemented_function(Function('fi4'), lambda *args :  args[0] + args[1]  )
f4 = lambdify( args , fi4(*args) )


fi = implemented_function(Function('fi'), lambda x: x+1)
f = lambdify(x, fi(x))

args = [x,y]


fi2 = implemented_function(Function('fi2'), lambda x,y:  x + y  )
f2  = lambdify((x,y), fi2(x,y))


Q = Symbol('Q')
gi = implemented_function(Function('gi'), lambda Q: diff(Q,x) )
gd = lambdify(Q, gi(Q))


d4i = implemented_function(Function('d4i'), lambda Q: diff( Q,x,x) + diff(Q,y,y) + diff(Q,z,z) -  diff(Q,t,t) )
lap = lambdify(Q, d4i(Q))


new = sexpr.replace(d4,gd)
