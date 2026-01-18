# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import traceback
import random
import html
import glob
from exercises.util import p53
from sympy.parsing.sympy_parser import parse_expr
from django.core.cache import cache as core_cache
from django.core.cache import caches
from exercises.util import get_hash_from_string, mychop, CLEAN_PRECISION, COMPARISON_PRECISION
from exercises.questiontypes.core.core import CoreQuestionOps, declash, reclash, replace_primes, deimplicit, has_floatingpoint, to_latex, scope
from exercises.models import Exercise
from .functions import basic_defs
import dill
from sympy import *
import time
import deepdiff;
from django.conf import settings
import json
from sympy import *;
from sympy import FiniteSet
import os
import logging
import re as resub

from .basicutils import  random_fraction, samples, absify, flatten, index_of_matching_right, index_of_matching_left, setify, get_randomunits, is_a_rational, index_of_matching_right_paren, add_right_arg
from exercises.questiontypes.core.coreutils import index_of_matching_left_and_head
from exercises.questiontypes.core.functions import myabs, myFactorial
from exercises.questiontypes.core.functions import partial as myPartial
import numpy as np;
from exercises.utils import json_hook  as basic_json_hook
from sympy.core.function import AppliedUndef
from exercises.utils.checks import parens_are_balanced, brackets_are_balanced
from lxml import etree
from sympy.utilities.lambdify import implemented_function
import sympy;
from django.contrib.auth.models import User, Group
from exercises.question import get_usermacros
from exercises.parsing import exercise_xmltree 






def functionalize_matrix_elements( s, scope ):
    #print(f"FUNCTIONALIZE S = {s}")
    match = resub.search(r"[\w\)\$]+\[",s )
    found = True  if match else False ;
    i = 0;
    while  found  and i < 10 :
        ib = match.end() - 2 ;
        i1 = index_of_matching_left_and_head( s , ib )
        lhs = s[i1:ib+1];
        i2 = index_of_matching_right(s, ib+1);
        rhs = s[ib+1:i2+1];
        rhs = resub.sub(r"\[",'(',rhs);
        rhs = resub.sub(r"]",')',rhs);
        isin = lhs in scope;
        #print(f"LHS = {lhs} RHS = {rhs} ISIN={isin} " )
        if isin :
            val = scope[lhs]
            #print(f"LHS = {val} {type(val)} ")
        s = s[0:i1] + f"matrixElements({lhs},{rhs})" + s[i2+1: ];
        match = resub.search(r"[\w\)\$]+\[",s )
        found = True  if match else False 
        i = i + 1 ;
    return s
    



try :
   from exercises.questiontypes.safe_run import safe_run
except:
    pass
unitbaseunits = {"meter": 1, "second": 1, "kg": 1, "ampere": 1, "kelvin": 1, "mole": 1, "candela": 1}
import sympy
from sympy import *
from sympy.core.sympify import SympifyError
logger = logging.getLogger(__name__)





logger = logging.getLogger(__name__)

UNITS_OK = "Units OK"
IS_CORRECT = " is correct"
ii1 = sympy.Symbol('ii1');
ii2 = sympy.Symbol('ii2');

class com(sympy.Function):
    nargs = 2
    @classmethod
    def eval(cls, x, y ):
        return x*y - y*x


def isnum(res) :
    return isinstance( res, Float)  or isinstance(res, float ) or isinstance(res, int ) 








basic_defs.update(
    {
        "p53" : p53, 
        "var" : lambda x : Symbol(x, positive=True, commutative=True ),
        "com": com,
        "e" : E,
        "op" : lambda x : Symbol(x, commutative=False),
        "ndot" : lambda x,y : x.dot(y),
        "log" : lambda x : log(x),
        "log2" : lambda x : log(x,2) , 
        "log10" : lambda x : log(x,10) ,
        "Q": Q,
        "S": S,
        "exp": sympy.exp,
        "Matrix": sympy.Matrix,
        "ff": Symbol("ff"),
        "FF": Symbol("FF"),
        "npi" :  3.1415926535897932384626433832795028841971693993751058, 
        'sfloat' : N,
        'Not' : lambda x : 0 if x == 1 else 0 ,

   }
)
scope.update(basic_defs)


lambdifymodules = ["numpy", {"cot": lambda x: 1.0 / numpy.tan(x)}]




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
        latex = latex(sympify(BasicQuestionOps().asciiToSympy(expression), ns))  # _clash))
    except SympifyError as e:
        latex = "error"
    return latex

class BasicQuestionOps(CoreQuestionOps):

    scope = scope;
    used_variable_list = [];
    is_staff = settings.RUNTESTS # runtests never gets a chance to set this properly via json


    def __init__(self):
        self.name = "basic_class";
        self.hide_tags =  ["expression","value"] 
        self.userpk = 0


    def scope_update(self, nss ) :
        self.scope.update(nss); 
        return self.scope 


    def answer_class( self, *args, **kwargs ):
        #print(f"BASIC_QUESTION_OPS_ANSWER_CLASS")
        r = super().answer_class( *args, **kwargs);
        return r

    def noanswer_class( self, hijacked, view_solution_permission, user, user_agent, exercise_key, question_key, answer_data, old_answer_object=None, db=None,):
        #r = self.reduce_using_defs(expression1, global_text,preamble, unitbaseunits) 
        r = super().answer_class( hijacked, view_solution_permission, user, user_agent, exercise_key, question_key, answer_data, old_answer_object, db)




    def reduce_using_defs(self, expression, global_text, preamble, units , use_wedgerules='wedgerules', docache=settings.DO_CACHE):
        try:
            return super().reduce_using_defs(
                expression, global_text, preamble, units,
                use_wedgerules=use_wedgerules, docache=docache,
            )
        except Exception as e:
            # Fallback: retry without cache (avoids Redis/network in tests)
            logger.error(f"ERROR REDUCE_USING_DEFS {str(e)}")
            try:
                return super().reduce_using_defs(
                    expression, global_text, preamble, units,
                    use_wedgerules=use_wedgerules, docache=False,
                )
            except Exception as e2:
                logger.error(f"ERROR REDUCE_USING_DEFS (fallback) {str(e2)}")
                # Last-resort: parse without applying globals to preserve type
                try:
                    return sympify(self.asciiToSympy(expression), self.scope)
                except Exception:
                    return sympify("0")

    def is_zero(self, v, precision=COMPARISON_PRECISION , float_allowed=True, scale=1.0):
        return super().is_zero(v,precision=precision, float_allowed=float_allowed, scale=scale);

    def compare_with_units(self, expression1, expression2,global_text,preamble, precision_string ,units, testing_equality ):
        response = {}
        if has_floatingpoint( expression2 ) and not has_floatingpoint(expression1 )  and precision_string == "0" :
            response['error'] = "Exact required ";
            if 'correct' in response :
                del response['correct']
            return response;
        use_wedgerules = True
        rulename = 'wedgerules'
        if testing_equality :
            use_wedgerules = False
            rulename = None
        sympy1 = self.reduce_using_defs(expression1, global_text,preamble, units, use_wedgerules=rulename);
        sympy2 = self.reduce_using_defs(expression2, global_text,preamble, units, use_wedgerules=False);
        target = str( sympy2)
        isfiniteset =  'set' in str( type( sympy1) ) or 'Set' in str( type( sympy1) ) 
        if isfiniteset :
            ex1 = [ N( i , p53 ) for i in list( sympy1 ) ];
            ex2 = [ N( i , p53 ) for i in list( sympy2 ) ];
            s1 = FiniteSet( *ex1 );
            s2 = FiniteSet( *ex2 );
            areequal = ( s1 == s2 );
            result = {};
            if areequal :
                result['correct']  = True
                return result
            if len( s1) != len(s2) :
                result['error'] = "Incorrect: length of the set is wrong."

            sympy1 = list( s1 )
            sympy2 = list( s2 )
            sympy1 = Matrix( sympy1 )
            sympy2 = Matrix( sympy2 )

        def patch_bool( sy ):
            if isinstance( sy, bool ) :
                sy = sympify("1") if sy else sympify("0")
            if 'True' in str( type(sy) ):
                sy = sympify('1');
            elif 'False' in str( type(sy) ):
                sy = sympify('0');
            return sy




        try :
            sympy1 = patch_bool( sympy1);
            sympy2 = patch_bool( sympy2);
            sympy1 = N( sympy1, p53 );
            sympy2 = N( sympy2, p53 );
        except SympifyError as e :
            if sympy1 == True:
                sympy1 = 1;
            if sympy1 == False :
                sympy1 = 0;
            return {'error' : f" ERROR COMPARE {str(e)}"}
            pass
        try :
            sympy2 = N( sympy2, p53 );
        except :
            if sympy2 == True :
                sympy2 = 1
            if sympy2 == False: 
                sympy2 = 0
            pass

        try :
            diffy = sympy2 - sympy1
            func1 = [i.func for i in diffy.atoms(Function) if isinstance(i, AppliedUndef) and not i.func.__name__ in self.scope ]
            if func1 :
                funcs = (',').join([ str(i) for i in func1 ])
                response['warning'] = f"{funcs} is undefined"
                response['correct'] = False
                response['clean'] = True
                return response

        except ShapeError as e :
            response['warning'] = "matrix does not have the correct dimensions "
            return response
        except Exception as e :
            if 'Matrix' in str( type( sympy1 )) :
                response['warning'] =  f"Your submitted object is of the wrong type; should  be matrix or vector .    "
            else :
                response['warning'] =  f"Your submitted object is of the wrong type.   "
            return response
            
        fd = sympy1.free_symbols
        try :
            t = []
            scalars = [ i for i in  fd if  i.is_commutative ]
            if scalars :
                for _ in range(4)  :
                    rr = []
                    for fs in scalars :
                        if fs.is_commutative:
                            rr.append( ( fs, random.random() ))
                    t.append(abs( diffy.subs(rr) ))
            if t :
                diffy = max(t)
                sympy1 = sympy1.subs(rr);
                sympy2 = sympy2.subs(rr);

        except TypeError as e :
            pass
        except Exception as e :
            logger.error(f" {type(e).__name__} EXCPTION TO NUMERICAL EVALUATION OF UNDEFINED VARIABLES")
        
        precision = self.get_precision( abs( sympy1) , precision_string)
        print(f"PRECISION = {precision}")
        response["exact"] = True;
        if resub.search(r"\.",f"{expression1}"):
            response["exact"] = False;
        float_allowed = False
        if not precision_string  == "0" :
            response["exact"] = False
            float_allowed = True
        scale = 1 ;
        if precision_string == "0"  or '%' in precision_string :
            scale =  myabs( sympy1 ) ;
        if scale == 0 :
            scale = 1;
        ts1 = self.reduce_using_defs(expression1, global_text,preamble, unitbaseunits)  
        response['target'] = target
        if not precision_string == "0" and not '%' in precision_string  :
            ts1 = myabs( ts1 )
            if not ts1 == 0 :
                ts1b = myabs( sympy1 )
                scale = ts1b/ts1 # WITHOUT THIS ABSOLUTE SCALE IN EXPRESSIONS WITH UNITS IS MEANINGLESS


        response = self.is_zero(diffy, precision , float_allowed, scale ) 
        diffytype = type(diffy)

        def apply_to_nested_list(nested_list):
            func = lambda xx: 'y' if self.is_zero( xx, COMPARISON_PRECISION  , True, 1 )['correct']  else 'N'
            result = []
            for item in nested_list:
                if isinstance(item, list):  # Check if the item is a list (nested)
                    result.append(apply_to_nested_list(item, func))
                else:
                    result.append(func(item))
            return result

        if not response.get('correct', False ):
            ismatrix = 'Matrix' in str( type(diffy) )
            if ismatrix :
                (nr,nc) = shape( diffy )
                ls = list( diffy )
                rr = apply_to_nested_list( ls)
                if nr != 1 and nc != 1 :
                    rr = [rr[i:i + nc] for i in range(0, len(rr), nc)]
                rr = f"{rr}".replace("\'",'')
                if 'y' in rr :
                    response['warning']  = response.get('warning','') + '  Hint: ' +   f"{rr}  ."
        if response.get('correct', False ) :
            return response 
        if not 'sympy' in f"{type( sympy1 )}"  or  not 'sympy' in f"{type( sympy2 )}"  :
            return response
        isin = "npi" in self.scope
        try :    
            free1 = [ i for i in sympy1.free_symbols if not str(i) in self.scope  ]
            free2 = [ i for i in sympy2.free_symbols if not str(i) in self.scope  ]
            ok = self.used_variable_list
            if testing_equality :
                allfree = list( set( free1 + free2) )
            else :
                allfree = free2
            free = [i for i in allfree if not str(i) in self.used_variable_list ]
            if len( free ) > 0  :
               response['warning'] =  f"Undefined variables1 {free}";
               if 'correct' in response :
                    del response['correct']
            func1 = [i.func for i in sympy1.atoms(Function) if isinstance(i, AppliedUndef)]
            func2 = [i.func for i in sympy2.atoms(Function) if isinstance(i, AppliedUndef)]
            func = list( set( func2) - set( func1 ) )
            if len( func ) > 0  : 
               response['warning'] =  response.get('warning','') + f"Undefined functions {func}  ";
        except Exception  as err :
            logger.error(f"ERROR 1710252 {sympy1} {sympy2} {type(err).__name__} ")
            logger.error(f"ERROR 1710252 {expression1} {expression2} {type(err).__name__} ")
            logger.error(f"ERROR 1710252 {sympy1} {sympy2} {type(err).__name__} ")
            formatted_lines = traceback.format_exc()
            logger.error(f"TRACEBACK  1710252 = {formatted_lines}")

        ts1 =self.reduce_using_defs(expression1, global_text,preamble, unitbaseunits) 
        if  False and isnum( ts1 ) : # THIS MISCUES STUDENTS IN MANY CASES WHEN FEW DECIMALS EXIST IN SUBSTITUYION
            mag = N( myabs( ts1 ) )
            isa = is_a_rational( mag  ) ;
            if isa :
                return response
            ns1 = N( myabs( sympy1 ) )
            ns2 = N( myabs( sympy2 ) )
            if not ns1 == 0 and precision_string == "0"   : # and not is_a_rational( ts1) :
                rat = ns1 / ns2 
                isarat = is_a_rational( rat );
                if isarat :
                    response['warning'] = response.get('warning','  ' ) + 'Your answer appears to be correct except for an overall  rational or integer factor'
    
        response['target'] = f"{target}"

        return response  # }}}



    def parse_matrix_transforms(self,s,fake=False):
        return s



    def _compare_expressions(self, expression1, expression2,global_text_raw, preamble="" ,  \
                precision_string="0", skip_syntax_check=False, testing_equality=False ):
        return super()._compare_expressions( expression1, expression2,global_text_raw, preamble , \
                precision_string, skip_syntax_check, testing_equality )

    def simplify_lists(self,s):
        return s

    def asciiToSympy(self, expression, recur=True, debug=False,fake=False):
        dict = {
            "^": "**",
        }
        if resub.search(r"[\w\)]+\[",expression) :
           expression = functionalize_matrix_elements( expression, self.scope)
        return super().asciiToSympy(expression, recur,debug,fake);


    def get_text(self, gtree) :
        if gtree == None :
            return ''
        global_text = ''
        vv3 = ""
        for otype in ['ops','oneforms'] :
            pat = f"./{otype}"
            if gtree.xpath(pat) :
                txts =  [ i.text for i in  gtree.xpath(pat)] 
                for txt in txts :
                    vv4 = [ i.strip() for i in txt.split(',')]
                    for vv in vv4 :
                        vv3 = vv3 + f"{vv} = op(\"{vv}\") ;\n" 




        global_text = super().get_text(gtree)
        global_text = vv3 + global_text 

        if gtree.xpath("./oneforms") :
            pats = "./oneforms"
            txts =  [ i.text for i in  gtree.xpath(pats)] 
            wedgerules = []
            wedgecheck = []
            for txt in txts :
                token = sorted( [ i.strip() for i in txt.split(',') ] )
                imax = len( token);
                for dx  in token :
                    x = dx.lstrip('d')
                    vv3 = vv3 + f"{x} = var(\"{x}\") ;\n" 
                for i in range(imax ):
                    wedgerules.append( f"{token[i]}**2 : 0 ")
                    wedgerules.append( f"{token[i]} * {token[i]} : 0 ")
                    for j in range( i+1 , imax) :
                        wedgerules.append( f"{token[j]} * {token[i]} : - {token[i]} * {token[j]}")
                        wedgecheck.append( f"{token[i]} * {token[j]} : 0")
            wedgerules = "{" + ','.join( wedgerules) + '}'
            wedgecheck = "{" + ','.join( wedgecheck) + '}'
            global_text = global_text + f" ; wedgerules = {wedgerules} ;  wedgecheck = {wedgecheck}  \n"
    



        if not global_text :
            global_text = ''
        if not vv3 :
            vv3 = ''
        global_text =  vv3 + global_text + ';\n'
        if not global_text :
            global_text = ''
        return global_text



    def matrixify(self, s ):
        return s
    

    def json_hook(self,  safe_question, full_question, question_id, user_id, exercise_key, feedback,db=None) :
        safe_question_ = basic_json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback)
        return  safe_question_
        

def osubs(self ,*args, **kwargs ):
    ruls = simplify( args , BasicQuestionOps.scope, evaluate=True)
    res = self.subs( *ruls , **kwargs) 
    return res


sympy.Basic.osubs = osubs
sympy.MutableDenseMatrix.osubs = osubs
