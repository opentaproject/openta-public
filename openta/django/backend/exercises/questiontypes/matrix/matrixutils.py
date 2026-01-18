# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import random;
import  re  as resub;
from sympy import *;
from .functions import matrix_defs, myabs
from exercises.questiontypes.core.functions import  myabs
from exercises.util import p53
from exercises.questiontypes.core.coreutils import random_fraction, get_randomunits, cfrac, rat, is_a_rational, setify, absify, iof
from exercises.questiontypes.core.coreutils import add_right_arg, index_of_matching_right, index_of_matching_left
from exercises.questiontypes.core.coreutils import index_of_matching_left_paren, index_of_matching_right_paren, flatten, samples



bdefs   = {'Array' : {'name' : '',"left":'[' , "right" : ']' } };

def tomyarrays(expression):  # # {{{
    s = expression;
    s = resub.sub(r"\[","MyArray(",s );
    s = resub.sub(r"\]",")", s );
    #print(f"S = {s}")
    return s  # }}}

def toarrays(expression):  # # {{{
    s = expression;
    s = resub.sub(r"\[","Array([",s );
    s = resub.sub(r"\]","])", s );
    #print(f"S = {s}")
    return s  # }}}

def bsplit(expression):  # # {{{
    """PUT A MATRIX( ) around outer square brackets"""
    l = len(expression)
    i = 0
    depth = 0
    s = [''];
    k = 0;
    while i < l:
        c = expression[i]
        if c == "[":
            if depth == 0:
                k = k + 1 ;
                s.append('');
            depth -= 1
        if c == "]":
            depth += 1
        s[k]   += expression[i]
        if c == "]" and depth == 0:
            s.append('');
            k = k +1 ;
        i += 1
    return s  # }}}

MyArray = Function("MyArray")

def hat( x ):
    #print(f" HAT X = ", x , type(x) )
    name = str( type( x) )
    #print(f"NAME = {name}")
    n = myabs(x);
    #print("N = ", n )
    if 'Matrix' in name :
        r = Matrix(  x /n );
        #print(f"RETURNING R = ", r )
        return r 
    elif 'MyArray' in name :
        nargs = [ i / n for i in  x.args ];
        return MyArray( *nargs);
    elif 'Array' in name :
        nargs = [ i / n for i in  x.args ];
        return Array( nargs )
    elif 'list' in name :
        r = [ i / n for i in x ]
    else :
        r = 1
    #print(f"RETURNING {r}")
    return r


matrix_defs.update({"hat" : hat })

def nomatrixify(s1) :
    if not '[' in s1 :
        return s1;
    bscope = {'Array' : Array};
    p2 = bsplit(s1);
    p3 = [];
    for pp2 in p2 :
        if '[' in pp2 :
            s2 = toarrays(pp2);
            #print("S2 = ", s2 );
            e2 = sympify(s2, bscope);
            #print("E2 = ", e2 );
            #s3 = arrayify_( e2  );
            #print(f"S3 = {s3}")
            #s4 = dearrayify_( s3 );
            #print(f"S4 = {s4}")
            #s5 = f"Matrix({s4})";
            #print(f"s5 = {s5}")
            #s6 = sympify(s5, matrix_defs, evaluate=False);
            #pp2 = str(s6);
            e2p = Matrix(e2);
            #print(f"PP2 = {pp2} and e2 = {e2p} {type(e2p)} ")
            pp2 = str( e2p );
        p3.append(pp2);
    s7 = ''.join(p3);
    return s7




def oldmatrixify(expression):  # # {{{
    if not ']' in expression :
        return expression
    l = len(expression)
    i = 0
    s = ""
    depth = 0
    left = 0;
    right = len( expression);
    nc = 0;
    while i < l:
        c = expression[i]
        if c == "[":
            if depth == 0 :
                left = len(s)
            if depth %2 == nc  :
                s += "Matrix("
            depth -= 1
        if c == "]":
            depth += 1
        s += expression[i]
        if c == "]" and ( depth == 0  ) :
            right = len(s)
        if c == "]" and ( depth % 2  == nc  ) :
            s += ")";
            right = len(s);
        i += 1
    head = s[0:left];
    tail = s[right:len(s)]
    mid = s[left :right ];
    s = f"{head}{mid}{tail}";
    return s  # }}}












    
    
