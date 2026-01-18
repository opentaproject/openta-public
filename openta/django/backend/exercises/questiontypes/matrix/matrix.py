# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

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

from .matrixutils import  random_fraction, samples,  flatten, index_of_matching_left, setify, bsplit
from exercises.questiontypes.basic import BasicQuestionOps
from exercises.questiontypes.basic.basic import scope
from exercises.questiontypes.matrix.matrixify import ExtraMethods
from .functions import matrix_defs, myabs;
import numpy as np;
from exercises.utils import json_hook  as matrix_json_hook
from exercises.util import mychop, COMPARISON_PRECISION, CLEAN_PRECISION, p53
from sympy.core.function import AppliedUndef
from exercises.utils.checks import parens_are_balanced, brackets_are_balanced
from lxml import etree
import re;
from sympy.utilities.lambdify import implemented_function
import sympy;
from django.contrib.auth.models import User, Group
from exercises.question import get_usermacros
from exercises.parsing import exercise_xmltree 


def index_of_matching_left_and_head( s, right ):
    leftorig = index_of_matching_left(s,right);
    left = leftorig - 1;
    while left  >= 0 and ( s[left : leftorig ] ).isalnum() :
        left = left - 1;
    return left +1 




try :
   from exercises.questiontypes.safe_run import safe_run
except:
    pass
unitbaseunits = {"meter": 1, "second": 1, "kg": 1, "ampere": 1, "kelvin": 1, "mole": 1, "candela": 1}
import sympy
from sympy import *
from sympy.core.sympify import SympifyError
logger = logging.getLogger(__name__)

MyArray = Function("MyArray", commutative=False)



logger = logging.getLogger(__name__)

scope = {};
UNITS_OK = "Units OK"
IS_CORRECT = " is correct"

class com(sympy.Function):
    nargs = 2
    @classmethod
    def eval(cls, x, y ):
        return x*y - y*x





def isnum(res) :
    return isinstance( res, Float)  or isinstance(res, float ) or isinstance(res, int ) 

def getkind( s1 ):
    if isnum( s1 ):
        return 'number';
    try :
        tt1= ( str( s1.kind).split('Kind')[0] ).lower()
    except :
        tt1 = 'undefined'
    return tt1





#def dot_(a,b):
#    res = a.dot(b.T);
#    return res;

matrix_defs.update(
    {
        "MyArray" : Function("MyArray", commutative=False),
        # Use core's unified `set` implementation (do not override here)
        "var" : lambda x : Symbol(x, positive=True ),
        "com": com,
        "e" : E,
        "op" : lambda x : Symbol(x, commutative=False),
        "Matrix": sympy.Matrix,
        "ff": Symbol("ff"),
        "FF": Symbol("FF"),
        "npi" : N( 3.1415926535897932384626433832795028841971693993751058, p53 ),
        'Not' : lambda x : 0 if x == 1 else 0 ,
        'NullSpace' : lambda x: x.nullspace() ,

    }
)

from exercises.questiontypes.basic.basic import declash, deimplicit, has_floatingpoint, to_latex

scope.update( matrix_defs)


#lambdifymodules = ["numpy", {"cot": lambda x: 1.0 / numpy.tan(x)}]

class BaseMatrixQuestionOps( ExtraMethods, BasicQuestionOps):

    scope = scope;
    used_variable_list = [];
    is_staff = settings.RUNTESTS # runtests never gets a chance to set this properly via json


    def __init__(self):
        super().__init__()
        self.name = "matrix_class";
        self.hide_tags =  ["expression","value"] 
        self.scope = scope;
        self.scope_update( BasicQuestionOps().scope )


    #def scope_update(self, nss ) :
    #    self.scope.update(nss); 
    #    return self.scope 

    def reduce_using_defs(self, expression, global_text, preamble, units , use_wedgerules=True , docache=settings.DO_CACHE):
        return super().reduce_using_defs( expression , global_text, preamble, units, use_wedgerules, docache)
    
    def get_precision(self, v, precision_string ):
        if not isinstance(v, MatrixBase ):
            ret = super().get_precision(  v, precision_string)
            return ret       
        try :
            free = [ i for i in v.free_symbols if not i in self.scope.keys()  ]
            if len(free ) > 0 :
                return 0
        except :
            pass;
        vn = N(v,p53);
        if isinstance(v, MatrixBase):
            flat = [ abs(x) for x in flatten( v.tolist() ) if x.is_number ];
            if len(flat) == 0 :
                return 0
            else :
                vn = max( flat );
        if '%' in precision_string :
            np = sympify( precision_string.split('%')[0]) 
            precision = abs( N( np, p53 ) * N( .01, p53 ) * vn );
        else :
            precision = sympy.sympify( precision_string)
        return precision

    def is_zero(self, v, precision=COMPARISON_PRECISION , float_allowed=True, scale=1):
        if hasattr( scale, "free_symbols") :
            if scale.free_symbols :
                scale = 1.0
        if not isinstance(v, MatrixBase ):
            ret = super().is_zero(  v, precision, float_allowed, scale)
            return ret                
        response = {};
        response['clean'] = True;
        exact_required = not float_allowed
        try :
            vn = N( v ,p53,chop=True);
            vn = mychop(vn)
            free = [ i for i in v.free_symbols if not i in self.scope.keys()  ]
            funcs =  [i.func for i in v.atoms(Function) ] 
            if v == 0 :
                return {'correct' : True , 'clean' : True }
            try :
                if simplify(v).is_zero :
                    return {'correct' : True , 'clean' : True };
            except :
                pass
            numpy_matrix = np.array( abs( v ) ).astype(float)
            if np.all(numpy_matrix == 0):
                return {'correct' : True, 'clean' : True  };
        except TypeError as e :
            pass

        except Exception as e :
            formatted_lines = traceback.format_exc()
            logger.error(f"TRACEBACK  IN NAIVE ERROR TESTING = {formatted_lines}")
            logger.error(f" ERROR IN NAIVE ERROR TESTING {type(e).__name__} {str(e)}")
            pass

        vn = N( Abs(vn).doit(), chop=True);
        vn = mychop(vn)
        try :
            precision = max( precision, COMPARISON_PRECISION )
        except :
            return {};
        flat = flatten( vn.tolist() );
        response['debug'] = f" E1 diff={flat} precision={precision}";
        flat = [ sympify(x) for x in flat ];
        nonumbers = [ x for x in flat if not x.is_number ];
        if len( nonumbers ) > 0 :
            response['correct']  = False;
            return response;
        notsmall = [ abs(x) for x in flat  if x.is_number  and abs(x) >= precision * scale ] ;
        nonzero = [ abs(x) for x in flat  if x.is_number  and abs(x) >=  COMPARISON_PRECISION  * scale];
        if len( notsmall ) == 0 :
            response['correct'] = True;
            response['debug'] = f" E2 diff={flat}";
            if exact_required and len(nonzero ) >  0 :
                if response['correct'] :
                    del response['correct']
        else :
            response['correct'] = False
        return response

        try :
            response['correct'] = bool(  v == 0 )
        except :
            response['correct'] = False;
        return  response


    

    def compare_with_units(self, expression1, expression2,global_text,preamble, precision_string ,units, testing_equality ):
        return super().compare_with_units( expression1, expression2,global_text,preamble, precision_string ,units, testing_equality )


    def compare_expressions(self, expression1, expression2,global_text_raw, preamble="" , precision_string="0", skip_syntax_check=False, testing_equality=False):  # {{{
        res = self.check_syntax( expression2 , global_text_raw )
        if res.get('error',False ) :
            return res
        # STUDENT = expression1 CORRECT =expression2
        if 'set' == expression1.strip()[0:3] :
            ex1 = sympify( self.asciiToSympy( declash( expression1 ) ) , self.scope );
            ex2 = sympify( self.asciiToSympy( declash( expression2 ) ), self.scope );
            if 'Matrix' in  ex1.args[0].func.__name__  :
                ex1 = FiniteSet( * flatten( ex1.args[0] ) )
            if 'FiniteSet' in str( type(ex2)  ):
                if 'Matrix' in  ex2.args[0].func.__name__  :
                    ex2 = FiniteSet( * flatten( ex2.args[0] ) )
            elif 'Matrix' in str( type(ex2) ) :
                ex2 = FiniteSet( * flatten( ex2) )
            expression1 = str(ex1);
            expression2 = str(ex2);
        elif 'set' == expression2.strip()[0:3]:
            # Correct answer is a set; normalize the student expression to a set too
            ex2 = sympify(self.asciiToSympy(declash(expression2)), self.scope)
            ex1 = sympify(self.asciiToSympy(declash(expression1)), self.scope)
            # If student provided a matrix/vector or a list-like, flatten to a FiniteSet
            try:
                if 'Matrix' in str(type(ex1)):
                    ex1 = FiniteSet(*flatten(ex1))
                else:
                    # attempt to iterate and build a set from elements
                    ex1 = FiniteSet(*list(ex1))
            except Exception:
                # Fallback: wrap single value
                ex1 = FiniteSet(ex1)
            # Ensure ex2 is a FiniteSet of elements (handles set([...]) and set(a,b))
            try:
                if 'FiniteSet' in str(type(ex2)):
                    args = list(ex2)
                    ex2 = FiniteSet(*args)
                elif 'Matrix' in str(type(ex2)):
                    ex2 = FiniteSet(*flatten(ex2))
            except Exception:
                pass
            expression1 = str(ex1)
            expression2 = str(ex2)

        try :
            res = super().compare_expressions(expression1, expression2,global_text_raw, preamble , precision_string, skip_syntax_check, testing_equality)
        except ShapeError as err :
            if 'set' in expression1 :
                msg = "incorrect number of unique element in your answer"
            else :
                msg =  f"{type(err).__name__} i.e.  {expression1} incorrect vector or matrix shapees : {str( err)} ";
            r['error'] = msg
            return r
        return  res 


    def parse_matrix_transforms(self,s,fake=False):
        fake = False
        if not 'matrices' in self.scope  and not fake :
            return s
        if not resub.search(r"\.[AICT]",s) :
            return s
        sprev = '';
        nit = 0;
        if not fake :
            ops = {'T' : 'Transpose','I' : 'Inverse', 'C' : 'Conjugate', 'A' : 'Adjoint' };
        else :
            # FAKE IS SO THAT A SYNTAX CHECK CAN BE MADE WITHOUT TRIGGERING SHAPE ERROR
            ops = {'T' : 'faketranspose','I' : 'fakeinverse', 'C' : 'fakeconjugate', 'A' : 'fakeadjoint' };
        while not sprev == s  and nit < 10 :
            nit = nit + 1 ;
            sprev = s;
            pa0 = resub.compile("([\w\)\]]+)(\.[TICA])([\s\)]*)")
            mpa0 = pa0.search(s);
            if not mpa0 == None :
                (start,end) = mpa0.span() ;
                mm = s[start:end];
                mp = resub.search(r"([TICA])",mm)
                c = mm[ mp.start() ];
                key = c;
            else :
                break;
            val = ops[key];
            pp = f'(.)\.{key}(\)|\.|\s|$)?'
            p = resub.compile(pp)
            m = p.search( s );
            if not m == None :
                (start,end) = m.span();
                right = start;
                left = index_of_matching_left_and_head( s, right );
                mid = s[left: right+1] ;
                head = s[0: left ];
                tail = s[ right + 3 : len(s) ];
                s =  f"{head}({val}({mid})){tail}"
        return s;


    #def noadd(self, *xin):
    #    x = [ sympify( str(i), self.scope ) for i in xin ]
    #    m = [ i for i in x if isinstance(i, MatrixBase)];
    #    if len(m) > 0 :
    #        dims = shape(m[0]);
    #        if len( dims  ) == 2 and  dims[0] == dims[1] :
    #            id = eye(dims[0] )
    #            s  = tuple( [  i * id for i in x ] ) ;
    #            res = Add( *s)
    #            return res
    #        else :
    #            o = ones( *dims)
    #            newx = []
    #            for i in x :
    #                ismatrix = isinstance( i, MatrixBase)
    #                if not ismatrix :
    #                    newx.append(  sympify( o * i  ) )
    #                else :
    #                    newx.append( i )
    #            res = Add(*newx)
    #            return res
    #    else :
    #        return Add(*x)
    #    ret = Add(*s)
    #    return ret


    def asciiToSympy(self, expression, recur=True, debug=False, fake=False):
        expression = self.parse_matrix_transforms( expression);
        return super().asciiToSympy(  expression, recur, debug, fake) 

    def check_syntax( self, s, xml , validate=False):
        return super().check_syntax(s,xml, validate );

    def get_preamble(self, question_xmltree ):
        return super().get_preamble( question_xmltree)

    def get_global_text(self, question_json, global_xmltree, question_xmltree) :
        return super().get_global_text(  question_json, global_xmltree, question_xmltree )

    def validate_question(self, question_json, question_xmltree, global_xmltree):
        return super().validate_question( question_json, question_xmltree, global_xmltree )

    def get_hints(self, student_answer, correct_answer ):
        student_answer = self.parse_matrix_transforms( student_answer);
        return super().get_hints(  student_answer, correct_answer )


    def answer_check(self, question_json, question_xmltree, student_answer, global_xmltree={} , level=0,validate=True):
        #res = self.check_syntax(student_answer,"")
        #if not res.get('error', False ) :
        #    return res
        student_answer = self.parse_matrix_transforms( student_answer);
        return super().answer_check(  question_json, question_xmltree, student_answer, global_xmltree, level,validate)


    def json_hook(self,  safe_question, full_question, question_id, user_id, exercise_key, feedback,db=None) :
        safe_question_ = matrix_json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback)
        return  safe_question_
        


def osubs(self ,*args, **kwargs ):
    ruls = simplify( args , BaseMatrixQuestionOps.scope, evaluate=True)
    res = self.subs( *ruls , **kwargs) 
    return res

sympy.Basic.osubs = osubs
sympy.MutableDenseMatrix.osubs = osubs
