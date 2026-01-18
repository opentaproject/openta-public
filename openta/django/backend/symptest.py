# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from sympy import *
from sympy.abc import x, y, z
from sympy.core.function import AppliedUndef
from copy import deepcopy


def func_sub_single(expr, func_def, func_body):
    # Find the expression to be replaced, return if not there
    for unknown_func in expr.atoms(AppliedUndef):
        if unknown_func.func == func_def.func:
            replacing_func = unknown_func
            break
    else:
        return expr
    arg_sub = {from_arg: to_arg for from_arg, to_arg in zip(func_def.args, replacing_func.args)}
    func_body_subst = func_body.subs(arg_sub)
    return expr.subs(replacing_func, func_body_subst)


def func_sub(expr, func_def, func_body):
    if any(func_def.func == body_func.func for body_func in func_body.atoms(AppliedUndef)):
        raise ValueError("Function may not be recursively defined")

    while True:
        prev = expr
        expr = func_sub_single(expr, func_def, func_body)
        if prev == expr:
            return expr


def pre(expr, level=0):
    # fun = expr.func
    # print("LEVEL = ", level, "  ", expr, "   ",'FUNC = ', fun , type(fun) , expr.args)
    name = "NONAME" if not hasattr(expr, "name") else getattr(expr, "name")
    newargs = None
    if expr.is_Function:
        if str(expr.func) == "tanh":
            print("TANH FOUND")
            expr = Function("cosh")(*expr.args)
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
    else:
        print("COMPLEX EXPRESSION", expr)
        newargs = [pre(item, level) for item in expr.args]
        print("NEWARGS = ", newargs)
        # expr.args.__class__.__setattr__ =  expr.args.__class__.__setattr__
        # for oldarg,newarg in  zip( expr.args, newargs) :
        #        print("OLDARG = ", oldarg)
        #        if not oldarg  == None:
        #            print("OLD,NEW = ", oldarg, newarg )
        #            #oldarg.__class__ = newarg.__class__
        #        #expr.args.__class__ =  expr.args.__class__
        print("NEWARGS ", newargs)
        expr = expr.__class__(*newargs)
    for arg in expr.args:
        print("ARG ", arg)
        print("ARG func ", arg.func)
    # expr.__class__.__setattr__ = newargs
    print("NEW = ", expr)
    return expr


def test(expression):
    pre(expression)


g = Symbol("g")
f = Function("f")
# expression =  'x + y  + tanh(x) + f(g)'
expression = sympify("1 + tanh(x) ")
sexpr = sympify(expression)
# new = pre( sexpr )
# q = Symbol('q')
# print("NEW = ", new )
# sexpr = sympify( expression)
# sexpr = x + y
# print( sexpr )
# pre( expr )
# expression =  'x + y  + tanh(x) + f(g)'
# sexpr = sympify( expression, strict=False)

# print( func_sub( sexpr, f(q), ( q + 3 ) * ( q + 1 ) ) )
