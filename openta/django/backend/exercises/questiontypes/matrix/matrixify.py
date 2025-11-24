# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

#dD( fg( fg( [x,y,z] ) ) , [dx,dy,dz] , [x,y,z], dD( fg([x,y,z]), [dx,dy,z] , [x,y,z] ,  [v1,v2,v3] ) )
import traceback
from sympy.parsing.sympy_parser import parse_expr
import time
import deepdiff;
from django.conf import settings
import json
from sympy import *;
from sympy import Expr, Function, Symbol
from sympy import FiniteSet
import os
import logging
import re as resub
import random

from exercises.util import mychop
from .matrixutils import  flatten,  bsplit
from exercises.utils.checks import parens_are_balanced, brackets_are_balanced
from sympy.core.function import AppliedUndef
from lxml import etree
import re;
from sympy.utilities.lambdify import implemented_function
import sympy;


#def mychop(expr, threshold=1.e-12):
#    if expr.is_Atom:  # Base case: if the expression is an atom (e.g., a number or a symbol)
#        if expr.is_number and abs(expr.evalf()) < threshold:
#            return sympy.S.Zero
#        else:
#            return expr
#    else:  # Recursively process arguments of the expression
#        return expr.func(*[mychop(arg, threshold) for arg in expr.args])








import sympy
from sympy import *
from sympy.core.sympify import SympifyError
logger = logging.getLogger(__name__)

MyArray = Function("MyArray", commutative=False)

logger = logging.getLogger(__name__)


bdefs   = {'Array' : {'name' : '',"left":'[' , "right" : ']' } };

def tomyarrays(expression):  # # {{{
    ssave = expression
    s = expression;
    s = resub.sub(r"\[","MyArray(",s );
    s = resub.sub(r"\]",")", s );
    return s  # }}}

def ar( expr,level=0):
    if 'MyArray' not in str(expr) :
        return expr;
    if expr.args   :
        if expr.func.__name__ == 'MyArray':
            expr = MyArray(  * [ ar(i, level + 1 ) for i in expr.args ] )
            return expr;
    nargs = [];
    if expr.args   :
        arglist = [ ar( i, level + 1 ) for i in expr.args ] ;
        j = 0;
        if len( arglist) == 1 :
            return expr
        while j < 10 :
            try :
                res = expr.func( *list( map( lambda x : x if not x.func.__name__ == \
                            'MyArray' else x.args[j] , arglist) ));
                nargs.append(res);
                j = j + 1;
            except :
                break;
    
    expr = MyArray(*nargs)
    
    return expr

def dear( expr):
    bdefs   = {'MyArray' : {'name' : '',"left":'[' , "right" : ']' } };
    if expr.args :
        f = expr.func.__name__;
        fn = bdefs.get(f,{'name' : f , "left" : '(' , "right" :')'})
        s =  f'{fn["name"]}{fn["left"]}' + ",".join( [  dear( i) for i in expr.args]) + f'{fn["right"]}' 
    else :
        s = str( expr)
    return s;




#    def arn( self, expr,level=0):
#        if 'MyArray' not in str(expr) :
#            return expr;
#        if expr.args   :
#            if expr.func.__name__ == 'MyArray':
#                expr = MyArray(  * [ self.arn(i, level + 1 ) for i in expr.args ] )
#                return expr;
#        nargs = [];
#        if expr.args   :
#            arglist = [ self.arn( i, level + 1 ) for i in expr.args ] ;
#            #dprint(level, f"FUN = {expr.func.__name__}" , "ARGLIST = ", arglist)
#            j = 0;
#            if len( arglist) == 1 :
#                return expr
#            while j < 10 :
#                try :
#                    res = expr.func( *list( map( lambda x : x if not x.func.__name__ == \
#                                'MyArray' else x.args[j] , arglist) ));
#                    nargs.append(res);
#                    j = j + 1;
#                except :
#                    break;
#        
#        expr = MyArray(*nargs) # THIS  FAILS
#        
#        return expr

class ExtraMethods:

    def dear(self, expr):
        bdefs   = {'MyArray' : {'name' : '',"left":'[' , "right" : ']' } };
        if expr.args :
            f = expr.func.__name__;
            fn = bdefs.get(f,{'name' : f , "left" : '(' , "right" :')'})
            s =  f'{fn["name"]}{fn["left"]}' + ",".join( [  self.dear( i) for i in expr.args]) + f'{fn["right"]}' 
        else :
            s = str( expr)
        return s;


 

#    def new_matrixify(self, sin ):
#
#        #print(f"MYARRAY =  DO ",sin)
#        #print("r" in self.scope )
#        #print(sympify("r", self.scope ) );
#        s1 = sin 
#        if not resub.search(r'\[', sin ) : #  in sin :
#            #if not '[' in sin :
#            return sin
#        if not 'Matrix' in sin :
#            try :
#                e = 'a'
#                sn = s1;
#                e = 'b'
#                if '=' in s1 :
#                    sn = s1.split('=')[1].strip()
#                e = 'c'
#                #print(f"SN={sn}")
#                sp = tomyarrays( sn )
#                #print(f"SP={sp}")
#                e = 'd'
#                ap = sympify( sp )
#                e = 'e' 
#                #print(f"AP={ap}")
#                A = self.arn(  ap )
#                #print(f"A={A}")
#                e = 'f' 
#                d = self.dear(A)
#                #print(f" D = ", d )
#                dtest = sympify(d, self.scope)
#                # GENERATE ERROR IF IT CANNOT SYMPIFY 
#                #print(f" DTEST = ", dtest)
#                #assert not '[' in d , "SKIP"
#                e = 'g'
#                #print(f"D = {d}")
#                ea = sympify( d )
#                #print(f"EA = {eq}")
#                e = 'h'
#                eas = f"{ea}"
#                e = 'i'
#                eass = eas
#                e = 'j'
#                #print(f"eass={eass}")
#                if '=' in sin :
#                    [l,r] = sin.split('=')
#                    eass = ' = '.join( [l,eass] )
#                s1 = eass 
#            except :
#                #print(f"E = ", e )
#                #print(f"SP = ",sp)
#                pass
#        #print(srepr( s1 ) )
#        splits = bsplit( s1 );
#        pm = [];
#        #dprint(f"SPLITS = ", splits )
#        #if 'Matrix' in s1 :
#        #    return s1
#        for p in splits :
#            if '[' in p   :
#                p = p.strip();
#                p = self.matrixify_base( p );
#                if   resub.search(r'\[ *\[',p )  :
#                        p = 'Matrix(' + p + ')'
#            pm.append(p);
#        dprint(f"PM = ", pm )
#        pmm = [];
#        for p in pm :
#            dprint(" DO P = ", p )
#            if resub.search(r"^\[", p ) : 
#                p = "Matrix(" + str(p) + ")"
#            pmm.append(p)
#        dprint(f"PMM = ", pmm )
#        s4 = ''.join(pmm)
#        dprint(f"S4 = ", s4 )
#        return s4


#    def matrixify_base(self, s1) :
#        #print(f"MATRIXIFY_BASE S1 = ", s1 )
#        if not '[' in s1 :
#            return s1;
#        if 'Matrix' in s1  :
#            #print(f"RETURNING WITHOUT EVALUIATION")
#            return s1
#        #print("IN S1 = ", s1 )
#        #dprint("x" in self.scope)
#        if '=' in s1 :
#            [lhs,rhs] = s1.split('=')
#        else :
#            rhs = s1
#        #print("RHS = ",rhs )
#        #print("r" in self.scope)
#        rhss = sympify( rhs, self.scope );
#        #print(f" RHSS = ", rhss , str( type(rhss) ) )
#        if isinstance( rhss, list ):
#            erhsl = [];
#            for rh in rhss :
#                #print(f"RH = ", rh )
#                srh = sympify(str( rh ) , self.scope, evaluate=True) 
#                if isinstance(srh , MatrixBase ):
#                    srh = transpose( srh ).tolist()[0]
#                #print(f"SRH = ", srh )
#                erhsl.append( srh )
#            #print("RHSS IS A LIST")
#            erhs = erhsl
#        else :
#            erhs = sympify(rhs, self.scope, evaluate=True)
#        rhs2 = str(erhs)
#        #if   resub.search(r'\[ *\[',rhs2 )  and not 'Matrix' in rhs2 :
#        #    rhs2 = "Matrix(" + rhs2 + ")"
#        if '=' in s1 :
#            s2 = '='.join( [lhs,rhs2 ] )
#        else :
#            s2 = rhs2
#        dprint("OUT = ", s2 )
#        return s2

    def matrixify(self,s1) :
        if '==' in s1 :
            parts = s1.split('==');
            pnew = [ self.old_matrixify( i ) for i in parts ]
            s1 = ' == '.join( pnew )
        res = self.old_matrixify(s1)
        #print(f"MATRIXIFY OUT = {res} <-{s1} ")
        return res


#    def new_new_matrixify( self, s ):
#        s5 = ''
#        try :
#            if not '[' in s :
#                return s
#            if '=' in s :
#                s1 = s.split('=')[1].strip()
#            else :
#                s1 = s 
#            #print(f"S1 = ", s1 )
#            if resub.search(r'^Matrix',s1 ):
#                return s
#            s2 = tomyarrays( s1 );
#            #print(f"S2 = ", s2 );
#            sympy2 = sympify( s2 , self.scope, evaluate=True);
#            #print(f"SYMPY2 = ", sympy2 )
#            list2 = self.myarray_tolist( sympy2 );
#            #print(f"LIST2 = " , list2 )
#            list3 = [ x.tolist() if isinstance( x, Matrix) else x for x in list2 ];
#            #print(f"LIST3 = ", list3 )
#            s4 = dear( list2) 
#            #print(f"S4 = ", s4 )
#            s4 =  str( sympify( s4  ) ) 
#            #print(f"S4 = ", s4 )
#            if '=' in s :
#                s5 = '='.join( [ s.split('=')[0].strip(), s4 ] )
#            else :
#                s5 = s4;
#            #print(f" S5 = ", s5 , type(s5) )
#        except  Exception as e :
#            logger.error(f" {type(e).__name__} {str(e)}")
#            formatted_lines = traceback.format_exc()
#            logger.error(f"TRACEBACK  = {formatted_lines}")
#
#        s6 = self.new_matrixify( s )
#        #print(f"SHOULD BE ", s6 , type(s6) )
#        return s6
#        #s3 = dear( list2 );
#        #print(f" S3 = ", s3 )
#        #return list2

#    def myarray_tolist(self, expr,level=0):
#        #print(f" DO AR = { expr } " )
#        if isinstance(expr, Matrix ):
#            ml =  sympify( tomyarrays( str( expr.tolist() ) ), self.scope) ;
#            #print("ml = ", ml);
#            expr = ml
#            return ml
#        if not expr.args :
#            return expr;
#        if not 'MyArray' in str(expr):
#            return expr;
#        
#        #print(f"CONTINUE WITH {expr}")
#        myarrays = [];
#        if expr.args   :
#            arglist = [ self.myarray_tolist( i, level + 1 ) for i in expr.args ] ;
#            #print(f" ARGLIST = {arglist}")
#            if len( arglist ) == 1  and not  arglist[0].func.__name__ == 'MyArray' :
#                f = expr.func;
#                arglist  = arglist[0].args
#                ex = self.myarray_tolist( MyArray( *[ f(x) for x in arglist ]) );
#                return ex;
#            else :
#                fnames = [ x.func.__name__ for x in arglist if x.args];
#                #print(f"FNAMES = {fnames}");
#                if 'MyArray' in fnames  and not expr.func.__name__ == 'MyArray' :
#                    #print("MyArray FOUND");
#                    f = expr.func ;
#                    #print(f"FUNC IS {f.__name__}")
#                    myarrays = [ x for x in arglist if x.func.__name__ == 'MyArray']
#                    myarray = myarrays[0];
#                    #print(f"myarrayexample = {myarray} {myarray.args} ");
#                    jm = len(myarray.args);
#                    #print(f" JM = {jm}") ;
#                    nargs = [];
#                    for j in range(0, jm ):
#                        a = [ x.args[j]  if x.args else  x   for x in arglist ];
#                        #print(f"INSIDE LOOP DO {f.__name__}( {a} )")
#                        r = f( *a );
#                        #print(f"R = {r} , A = ", a );
#                        nargs.append( self.myarray_tolist( r, level + 1 )  );
#                    #print(f"NARGS = {nargs}")
#                    arglist = nargs;
#                    ex = MyArray( *arglist ) 
#                
#                    #if len( myarrays ) > 1 and f.__name__ == 'Mul' :
#                    #    print(f"FOUND PRODUCT OF MYARRYS");
#                    #    ex = self.myarray_tolist( Add( * arglist   ) )
#                    #    #ex = MyArray( *arglist ) ;
#                    #else :
#                    #    ex = MyArray( *arglist ) ;
#                    #print(f" EX = {ex}")
#                           
#                else :
#                    ex =expr.func( * arglist )
#                #print(f"FINALLY  ex = {ex}")
#                #print(f"FINALLY myarrays = {myarrays}");
#                #print(f"FINALLY func = {expr.func}")
#                return ex

#    def new_reduce_nested(  self, e3 ):
#       #print(f"REDUCE_NESTED {e3}")
#       res = e3;
#       e3orig = e3;
#       funcname = e3.func.__name__ 
#       #print(f"FUNCNAME = {funcname} {e3} ")
#       if funcname == 'Symbol' :
#           isin  = e3 in self.scope
#           e3 = sympify(e3, self.scope,evaluate=True)
#       if 'Matrix' in e3.func.__name__ :
#           args = e3.args 
#           #print(f"MATRIX ARGS = {args}")
#           lis = list( e3 )
#           e3 = MyArray( *lis )
#           #print(f"E3 BECAME {e3}")
#           #print(f"LIS = {lis}")
#       if e3.func.__name__ == 'Mul' and e3.args :
#           argin = list( e3.args )
#           args = [ self.new_reduce_nested( i ) for i in argin ]
#           scalars = [ i for i in args if  not i.func.__name__  == 'MyArray' ];
#           arrays  = [ list( i.args ) for i in args if      i.func.__name__  == 'MyArray' ];
#           scalars.append(1)
#           #print(f"SCALARS = {scalars}")
#           prefactor = sympy.Mul( *scalars  );
#           #print(f"PREFACTOR = {prefactor}")
#           #print(f"arrays = {arrays}")
#           zipped = zip( * arrays);
#           a = [ self.new_reduce_nested( prefactor * Mul( *z ) ) for z in zipped ]
#           #print(f"a1 = {a}")
#           #print(f"a = {a}")
#           if a :
#               res =  MyArray( * a ) 
#       elif e3.func.__name__ == 'Add' and e3.args   :
#           argin = list( e3.args )
#           args = [ self.new_reduce_nested( i ) for i in argin ]
#           scalars = [ i for i in args if  not i.func.__name__  == 'MyArray' ];
#           arrays  = [ list( i.args ) for i in args if      i.func.__name__  == 'MyArray' ];
#           scalars.append(0)
#           #print(f"SCALARS = {scalars}")
#           prefactor =  sympy.Add( *scalars  );
#           #print(f"preadd  = {prefactor}")
#           #print(f"arrays = {arrays}")
#           zipped = zip( * arrays);
#           a = [ self.new_reduce_nested( prefactor +  Add( *z ) ) for z in zipped ]
#           #print(f"a2 = {a}")
#           if a :
#               res = MyArray( *a ) 
#       elif e3.func.__name__ == 'MyArray'  :
#           argin = list( e3.args )
#           #print(f"ARGIN = {argin}")
#           a  = [ self.new_reduce_nested( i ) for i in argin ]
#           #print(f"a3 = {a}")
#           res =  MyArray( * a )
#       elif e3.func and e3.args:
#           funcname = e3.func.__name__
#           if not funcname == 'Pow' :
#               argin = list( e3.args );
#               nargs = []
#               for ar  in argin :
#                   #print(f"AR = {ar}")
#                   ar = self.new_reduce_nested( ar );
#                   if ar.func.__name__ == 'MyArray' :
#                       na = [ e3.func( i ) for i in ar.args]
#                       nargs.append( MyArray( *na ) )
#                   else :
#                       nargs.append( e3.func( ar ) )
#               #print(f"nargs  = {nargs}")
#               a = nargs
#               #print(f"{funcname} : a4 = {a}")
#               res = a[0]
#       e3 = res;
#       #print(f"REUCE_NESTED OUT  {e3orig} -> {e3}")
#       return e3 
#


    def reduce_nested( self, e3 ):
        return self.old_reduce_nested( e3)


    def old_reduce_nested( self, e3 ):

        def denewline(s) :

            return resub.sub( r"\n","",str( s ) )

        e3save = e3
        funcname = e3.func.__name__ 
        trig = False
        if e3.func.__name__ == 'MyArray' :
            trig = True
            newargs = [];
            argsave = e3.args
            for a in e3.args :
                asave = a
                funcname = a.func.__name__ 
                if 'Matrix' in funcname :
                    #print(f"funcname = {funcname} a = {a} ")
                    margs = a.args
                    nargs = list( a )
                    #print(f"MATRIX FOUND IN SUBFUNC with nargs {nargs} ")
                    nargs = MyArray( *nargs)
                    a = nargs
                elif funcname == 'Mul' :
                    margs = a.args
                    #print(f"MULFOUND {margs} ")
                    margs = list( margs )
                    prod = 1;
                    for i in margs :
                        t = str( type(i) )
                        if not 'MyArray' in t :
                            prod = prod * i 
                        else :
                            try :
                                im = None
                                im = self.matrixify( dear(i) );
                                #print(f"IM = {im}")
                                d = sympify( self.matrixify( dear(i) ), self.scope )
                                prodin = prod
                                prod = prod * d;
                            except :
                                print(f"FAILED margs={margs}")
                                print(f"FAILED ON {i} im={im} d = {d} prodin={prodin} ")
                        #print(f"I = {i} {t}")
                        #print(f"prod= {prod}")
                    if 'Matrix' in str( type(prod) ) :
                        prod = MyArray( * list( prod) )
                    #print(f"PROD = {prod}" )
                    a = prod;
                    #a = sympy.sympify( self.matrixify(dear(a)) , self.scope)
                if funcname == 'Add' :
                    margs = a.args
                    #print(f"ADD FOUND {margs} ")
                    n = [ sympify( self.matrixify( dear( i) ) , self.scope) for i in a.args ]
                    a = self.add(  * n )
                    #print(f"ADD FOUND {margs} and became {a}  ")
                    if 'Matrix' in str( type(a) ) :
                        a = MyArray( * list( a ) )
                    #print(f"ADD FOUND {margs} and finally became {a}  ")


                    #sum_ = 0;
                    #for i in margs :
                    #    t = str( type(i) )
                    #    if not 'MyArray' in t :
                    #        sum_ = sum_+ i 
                    #    else :
                    #        d = sympify( self.matrixify( dear(i) ), self.scope )
                    #        sum_ = d * sum_
                    #    print(f"I = {i} {t}")
                    #    print(f"sum_= {sum_}")
                    #if 'Matrix' in str( type(sum_) ) :
                    #    sum_ = MyArray( * list( sum_) )
                    #print(f"SUM = {sum_}" )
                    #a = sum_;
                    #n = [ sympify( self.matrixify( dear( i) ) , self.scope) for i in a.args ]
                    #a = self.add(  * n )


                newargs.append( a)
            newargs = [ self.old_reduce_nested(i) for i in newargs ]
            e3 = MyArray( *newargs)
        #if trig :
        #    print(f"OLD_REDUCE_NESTED {denewline(e3save)} -> {denewline(e3)}")
        #print(f"OLD_REDUCE_NESTED ARGS {denewline(argsave)} -> {denewline(e3)}")
        return e3



    def old_matrixify(self, s1 ):
        if not '[' in s1 :
            return s1;
        s1save = s1
        p2 = bsplit(s1);
        p3 = [];
        try :
            for pp2 in p2 :
                if '[' in pp2 :
                    if parens_are_balanced( pp2 ) and  brackets_are_balanced( pp2 ) :
                        s2 = tomyarrays(pp2);
                        s2a = self.asciiToSympy( s2 , recur=True)
                        student_answer = self.scope.get("student_answer","")
                        s2a = resub.sub(r"\$\$",student_answer, s2a )
                        #print(f"S2A = {s2a}")
                        e3 = s2a 
                        try :
                            isin = 'matrixElements' in self.scope
                            e3 = sympify( s2a, self.scope, evaluate=True).doit()
                        except Exception as err :
                            #logger.error(f"S2a failed {s2a} ")
                            #logger.error(f"ERR = {str(err)}")
                            if 'Matrix(MyArray' in s2a :  # GET RID OF REDUNTANTLY DEFINED MATRIX
                                s2a = s2a.replace('Matrix(MyArray','(MyArray')
                            e3 = sympify( s2a, self.scope, evaluate=True).doit()
                        #e3 = sympify( s2a, self.scope, evaluate=True).doit() # CHECK THIS CAREFULLY ; FRAGILE
                        e3 = sympify(e3, self.scope )
                        e3 = self.reduce_nested( e3)
                        if e3.func.__name__ == 'MyArray' :
                            nr = len( e3.args )
                        else :
                            nr = len( [ * ( e3.args[0].args ) ] );
                        e4 = ar(e3);
                        s5 = "Matrix(" + dear(e4) + ")"
                        e5 = sympify( s5 , self.scope);
                        sp =  [ * shape( e5  )];
                        if len(sp) > 0 and nr != 0 :
                            nc = int( sp[0] * sp[1] / nr );
                            if not nr * nc == 0 :
                                e5  = e5.reshape(nr,nc);
                                s5 = str( e5 );
                        pp2 = s5;
                    else :
                        pass
                p3.append(pp2);

            s7 = ''.join(p3);
            return s7
        except Exception as e :
            msg = f"the string {s1} can't be  matrixified {type(e).__name__} Here P2 = {p2}  "
            formatted_lines = traceback.format_exc()
            logger.error(f"E16682 error {str(e).__name__} in old_matrixify = {str(e)} ")
            assert False,  msg
    
