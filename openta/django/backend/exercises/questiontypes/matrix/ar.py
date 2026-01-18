# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

# PREDICTABLE ELEMENTWISE MULTIPLY ADD AND FUNCTIONS ON LISTS

from sympy import *;
import re as resub;
MyArray = Function("MyArray", commutative=False);

def dear( expr):
    bdefs   = {'MyArray' : {'name' : '',"left":'[' , "right" : ']' } };
    if expr.args :
        f = expr.func.__name__;
        fn = bdefs.get(f,{'name' : f , "left" : '(' , "right" :')'})
        s =  f'{fn["name"]}{fn["left"]}' + ",".join( [  dear( i) for i in expr.args]) + f'{fn["right"]}' 
    else :
        s = str( expr)
    return s;

def tomyarrays(expression):  # # {{{
    s = expression;
    s = resub.sub(r"\[","MyArray(",s );
    s = resub.sub(r"\]",")", s );
    return s  # }}}


def ar( expr,level=0):
    print(f" DO AR = { expr } " )
    if isinstance(expr, Matrix ):
        ml =  sympify( tomyarrays( str( expr.tolist() ) )) ;
        print("ml = ", ml);
        expr = ml
        return ml
    if not expr.args :
        return expr;
    if not 'MyArray' in str(expr):
        return expr;
    
    print(f"CONTINUE WITH {expr}")
    myarrays = [];
    if expr.args   :
        arglist = [ ar( i, level + 1 ) for i in expr.args ] ;
        print(f" ARGLIST = {arglist}")
        if len( arglist ) == 1  and not  arglist[0].func.__name__ == 'MyArray' :
            f = expr.func;
            arglist  = arglist[0].args
            ex = ar( MyArray( *[ f(x) for x in arglist ]) );
            return ex;
        else :
            fnames = [ x.func.__name__ for x in arglist if x.args];
            print(f"FNAMES = {fnames}");
            if 'MyArray' in fnames  and  not expr.func.__name__ == 'MyArray'  :
                print("MyArray FOUND");
                f = expr.func ;
                print(f"FUNC IS {f.__name__}")
                myarrays = [ x for x in arglist if x.func.__name__ == 'MyArray']
                myarray = myarrays[0];
                print(f"myarrayexample = {myarray} {myarray.args} ");
                jm = len(myarray.args);
                print(f" JM = {jm}") ;
                nargs = [];
                for j in range(0, jm ):
                    a = [ x.args[j]  if x.args else  x   for x in arglist ];
                    print(f"INSIDE LOOP DO {f.__name__}( {a} )")
                    r = f( *a );
                    print(f"R = {r} , A = ", a );
                    nargs.append( ar( r, level + 1 )  );
                print(f"NARGS = {nargs}")
                arglist = nargs;
                ex = MyArray( *arglist ) 
            
                #if len( myarrays ) > 1 and f.__name__ == 'Mul' :
                #    print(f"FOUND PRODUCT OF MYARRYS");
                #    ex = ar( Add( * arglist   ) )
                #    #ex = MyArray( *arglist ) ;
                #else :
                #    ex = MyArray( *arglist ) ;
                #print(f" EX = {ex}")
                       
            else :
                ex =expr.func( * arglist )
            print(f"FINALLY  ex = {ex}")
            print(f"FINALLY myarrays = {myarrays}");
            print(f"FINALLY func = {expr.func}")
            return ex

x = 1 ;
y = 2 ;
z = 3 ;
s = "[ 2 * [x,y,z] + 1 , [1,1,1], [1,0,1] ]"
ma = sympify( tomyarrays( s) , globals() )
print("MA = ", ma );
m = ar( ma);
print(dear( m ) )
