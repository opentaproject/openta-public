# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import random;
import  re  as resub;
from sympy import *;
from .functions import  myabs
from exercises.util import p53

def replace_primes(expression ):
    searchstring = "([A-z0-9_]+)"
    p0 = resub.compile(r"(^|\s|\()" + searchstring + "[']*(?=\()")
    p1 = resub.compile(r"(^|\s|\()" + searchstring + "[']+(?=\()")
    allm = list(p1.finditer(expression))
    it = 0
    while len(allm) > 0 and it < 50:
        m = allm[0]
        (beg, end) = m.span()
        if expression[beg] == "(":
            beg = beg + 1
        ind = index_of_matching_right_paren(end, expression)
        head = expression[beg:end].strip()
        arg = expression[end:ind]
        ex1 = expression[0:beg]
        ex2 = expression[beg : ind + 1]
        ex3 = expression[ind:]  # if ind < len(expression) else ''
        add_paren = False
        if ex3:
            if ex3[0] == "'":
                ex3 = ex3[1:]
                add_paren = True
        fun = (resub.sub(r"\'*", "", head)).strip()
        order = str(head.count("'"))
        fun = "#" + fun
        middle = " Prime(" + fun + arg + "," + arg + "," + order + ")"  # + ',' + str(rep) + '(x)) '
        expression = ex1 + middle + ex3
        if add_paren:
            expression = "(" + expression + ")'"
        allm = list(p1.finditer(expression))
    expression = resub.sub(r"#", "", expression)
    expression = resub.sub(r"#" + searchstring, r"\1", expression)
    return expression


def random_fraction(iseed=None):
    if not iseed == None :
        random.seed(iseed)
    r = N(  ( 1.0  + 2 * random.random()  ) /  2.0 , p53 )
    return r

def get_randomunits(k ):
    randomunits = {"meter": random_fraction(k+1) , "second": random_fraction(k+2) ,   \
        "kg": random_fraction(k+3) , "ampere": random_fraction(k+4) , \
        "kelvin": random_fraction(k+5) , "mole": random_fraction(k+6) , \
        "candela": random_fraction(k+7) }
    return randomunits

def index_of_matching_left_and_head( s, right ):
    leftorig = index_of_matching_left(s,right);
    left = leftorig - 1;
    while left  >= 0 and ( s[left : leftorig ] ).isalnum()  or s[left] == '$' :
        left = left - 1;
    return left +1 

 
def cfrac(x, s=[] ) :
    if len(s) < 10 and N( x - int(x + .01 ) , p53 ) > 1.e-10  :
        i = int(x);
        s.append(i);
        x  = x - i 
        if not x == 0  :
            s = cfrac(1/x,s)
        else :
            return s
    else :
        s.append( int(x) );
        
    return s;

def rat(x) :
    s = cfrac(x,[]);
    if len(s) == 1 :
        return( [s[0],1] )
    [n,m] = [0,1];
    while s :
        q = s.pop();
        [n,m] = [ m, q * m + n ]
    return [n,m];
            
def is_a_rational( x ):
    try :
        x = N( sympify( myabs(x) ) )
        if not x * ( x - 1 )  == 0  :
            [n,m]  = rat(x);
        else :
            return False 
        return  m  < 100 
    except:
        return False 



def setify(expression):  # # {{{
    if not '}' in expression :
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
        if c == "{":
            if depth == 0 :
                left = len(s)
            if depth %2 == nc  :
                s += "set("
            depth -= 1
        if c == "}":
            depth += 1
        s += expression[i]
        if c == "}" and ( depth == 0  ) :
            right = len(s)
        if c == "}" and ( depth % 2  == nc  ) :
            s += ")";
            right = len(s);
        i += 1
    head = s[0:left];
    tail = s[right:len(s)]
    mid = s[left :right ];
    s = f"{head}{mid}{tail}";
    return s  # }}}






def absify( expression ) :
    p = resub.compile(r'[\+\-\*\/\|]\s*\|')
    q = p.search(expression )
    while not  q == None :
        l = len( expression) 
        (b,e) = q.span() 
        head = expression[0:e-1]
        tail = expression[e-1:l] 
        newtail = iof(0,tail)
        expression = f"{head}{newtail}"
        q = p.search(expression )
    while '|' in expression :
        expression = iof( 0, expression);
    expression = resub.sub(r"([^\w]|^)abs\(", r"\1 myabs(", expression)
    return expression


def iof(beg, expression):
    if not '|' in expression :
        return expression;
    level = 1
    ind = beg
    while expression[ind] != '|' :
        ind = ind + 1 ;
    ibeg = ind;
    ind = ind + 1 ;
    while expression[ind] != '(' and expression[ind] != '|':
        ind = ind + 1 ;
    if expression[ind] != '|' :
        while level > 0 and ind < len(expression):
            if expression[ind] == ")":
                level = level - 1;
                if level == 1 :
                    break;
            elif expression[ind] == "(":
                level = level + 1
            ind = ind + 1
        while expression[ind] != '|'  and ind < len(expression):
            ind = ind + 1 ;
    iend = ind;
    ret = ''.join([ expression[0:ibeg], 'abs(' , expression[ibeg + 1 :iend  ],')' , expression[ iend + 1 : len(expression) ] ] )
    return  ret

def add_right_arg( result, fun , s ):
    result = result.replace(fun,"Cookie" )
    while  "Cookie" in result :
        indbeg = result.index("Cookie(") + len( 'Cookie')
        indend = index_of_matching_right( result, indbeg);
        beg = result[0 : indbeg ];
        beg = beg.replace("Cookie",fun )
        mid = result[indbeg : indend ];
        tail = result[ indend : len( result)  ];
        result  = f"{beg}{mid}, {s} {tail}"
    return result


def index_of_matching_right(result, indbegin):
    if result[indbegin] in ['(' , '[' ] :
        r = result[indbegin]
    else :
        return indbegin 
    pats = {'(':')','[':']'}
    level = 1
    l = pats[r];
    ind = indbegin
    while level > 0 and ind > 0:
        ind = ind + 1
        if result[ind] == l :
            level = level - 1
        elif result[ind] == r :
            level = level + 1
    assert result[indbegin] == r , "LEFT PAREN  MISSING"
    assert result[ind] == l,  "RIGHT PAREN  MISSING"
    return ind



def index_of_matching_left(result, indbegin):
    if result[indbegin] in [')' , ']' ] :
        r = result[indbegin]
    else :
        return indbegin 
    pats = {')':'(',']':'['}
    level = 1
    l = pats[r];
    ind = indbegin
    while level > 0 and ind > 0:
        ind = ind - 1
        if result[ind] == l :
            level = level - 1
        elif result[ind] == r :
            level = level + 1
    assert result[indbegin] == r , "RIGHT PAREN  MISSING"
    assert result[ind] == l,  "LEFT PAREN  MISSING"
    return ind


def index_of_matching_left_paren(result, indbegin):
    level = 1
    ind = indbegin
    while level > 0 and ind > 0:
        ind = ind - 1
        if result[ind] == "(":
            level = level - 1
        elif result[ind] == ")":
            level = level + 1
    assert result[indbegin] == ")", "RIGHT PAREN  MISSING"
    assert result[ind] == "(", "LEFT PAREN  MISSING"
    return ind


def index_of_matching_right_paren(beg, expression):
    level = 1
    ind = beg + 1
    while level > 0 and ind < len(expression):
        if expression[ind] == ")":
            level = level - 1
        elif expression[ind] == "(":
            level = level + 1
        ind = ind + 1
    assert expression[beg] == "(", "LEFT PAREN WRONG beg = %s, expression = %s , [%s] " % (
        beg,
        expression,
        expression[beg],
    )
    assert expression[ind - 1] == ")", "RIGHT PAREN WRONG = %s , expression= %s , [%s] " % (
        ind - 1,
        expression,
        expression[ind - 1],
    )
    return ind

def flatten(data ):

    def traverse(o, tree_types=(list, tuple)):
        if isinstance(o, tree_types):
            for value in o:
                for subvalue in traverse(value, tree_types):
                    yield subvalue
        else:
            yield o
        
    return list( traverse(data))

    
def samples(s):
    if not 'sample' in s :
        return [s];
    s = s.replace(";",";#")

    def red(s):
        index = s.find("sample")
        if index !=  -1   :
            m = s[index + len("sample")];
            p1  = index ;
            p2  = index + len("sample")
            p3  = index_of_matching_right_paren(p2, s)
            p4  = len(s);
            s4  = s[p3:]
            args = s[p2+1:p3-1].split(',');
            if len( args)  == 1 :
                args = [  args[0] + "*"  + f"{ 0.5 +  0.5 * random.random()}" ]
            r = [ red(f"{s[0:p1]}{i}{s4}" )  for i in args ];
            return r;
        else:
            return  s;
    
    r = red(s);
    flat = flatten( r )
    flat = [ i.replace("#","") for i in flat ]
    return flat;
    

def has_floatingpoint(s):
    if not resub.search(r"\.",s) :
        return False
    res = False
    if resub.search(r"([^\w]+|^)[0-9]+\.([^\w]*|$)",s) :
        res = True
    elif resub.search(r"\.[0-9]+(\W|$)",s) :
        res = True
    return res 


def to_latex(expression):
    latex = ""
    try:
        latex = latex(sympify(CoreQuestionOps().asciiToSympy(expression), ns))  # _clash))
    except SympifyError as e:
        latex = "error"
    return latex


