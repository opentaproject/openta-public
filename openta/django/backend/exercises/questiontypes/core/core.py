# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import traceback
import random
import html
import glob
from sympy import ShapeError
from sympy.parsing.sympy_parser import parse_expr
from django.core.cache import cache as core_cache
from django.core.cache import caches
from exercises.util import get_hash_from_string, mychop, p53
from exercises.models import Exercise
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

from .coreutils import  random_fraction, samples, absify, flatten, index_of_matching_right, index_of_matching_left, setify, get_randomunits, is_a_rational, index_of_matching_right_paren, add_right_arg
from .coreutils import  index_of_matching_left_and_head, replace_primes, has_floatingpoint, to_latex
from .functions import core_defs, myabs
from .functions import partial as myPartial
from .functions import myFactorial
import numpy as np;
from exercises.utils import json_hook  as core_json_hook
from sympy.core.function import AppliedUndef
from exercises.utils.checks import parens_are_balanced, brackets_are_balanced
from lxml import etree
from sympy.utilities.lambdify import implemented_function
import sympy;
from django.contrib.auth.models import User, Group
from exercises.question import get_usermacros
from exercises.parsing import exercise_xmltree 






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

scope = {};
from exercises.util import COMPARISON_PRECISION, CLEAN_PRECISION
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







def _core_set(*args):
    """Unified set constructor.

    Accepts either variadic elements (set(a,b,c)) or a single iterable/matrix
    (set([a,b,c]) or set(Matrix([...]))), producing a SymPy FiniteSet of the
    scalar elements. Falls back to treating a lone argument as a single element
    if it is not iterable.
    """
    try:
        if len(args) == 1:
            x = args[0]
            # Already a FiniteSet
            if isinstance(x, FiniteSet):
                return x
            # Unpack common iterables and matrices into elements
            try:
                return FiniteSet(*list(x))
            except Exception:
                return FiniteSet(x)
        else:
            return FiniteSet(*args)
    except Exception:
        # Best-effort fallback to preserve previous behavior
        return FiniteSet(*args)

core_defs.update(
    {
        "p53" : 16, 
        "set" : _core_set,
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
        "ff": Symbol("ff"),
        "FF": Symbol("FF"),
        "npi" :  sympy.pi, 
        "pi" : sympy.pi,
        'sfloat' : N,
        'Not' : lambda x : 0 if x == 1 else 0 ,

    }
)
scope.update(core_defs)


def reclash(expression) :
    result = expression;
    result = resub.sub(r"(ZETA)", "zeta", result)
    result = resub.sub(r"(GAMMA)", "gamma", result)
    result = resub.sub(r"(BETA)", "beta", result)
    result = resub.sub(r"(LAMBDA)", "lambda", result)
    result = resub.sub(r"(^|\W)Ö([^\(\w]|$)", r"\1N\2", result)
    result = resub.sub(r" npi ", r" pi ", result)
    result = resub.sub(r"\.osubs\(", ".subs(", result)
    result = resub.sub(r"variableFF", r"FF", result)
    result = resub.sub(r"variableff", r"ff", result)
    result = resub.sub(r"variableQ", r"Q", result)
    result = resub.sub(r"variableS", r"S", result)
    return result



def declash(expression):  ### RIDICULOUS beta and gamma are defined as functions# {{{
    result = expression;
    result = resub.sub(r"(zeta)", "ZETA", result)
    result = resub.sub(r"(gamma)", "GAMMA", result)
    result = resub.sub(r"(beta)", "BETA", result)
    result = resub.sub(r"(lambda)", "LAMBDA", result)
    result = resub.sub(r"\.subs\(", ".osubs(", result)
    result = resub.sub(r"partial", "myPartial", result)
    result = resub.sub(r"Adjoint\(", "localadjoint(", result)
    result = resub.sub(r"Transpose\(", "localtranspose(", result)
    result = resub.sub(r"Conjugate\(", "localconjugate(", result)
    result = resub.sub(r"(^|[\W]+)D\(", r"\1 Partial(", result)
    result = resub.sub(r"Inverse\(", "localinverse(", result)
    result = resub.sub(r"(^|\W)N([^\(\w]|$)", r"\1Ö\2", result)
    result = resub.sub(r"(e\^)(\w+)",r"exp( \2 )", result )

    result = resub.sub(r"([^n]|^)pi([^\w]|$)", r"\1( npi   )\2", result)
    result = resub.sub(r"([^e]|^)FF([^\w]|$)", r"\1variableFF\2", result)

    result = resub.sub(r"([^e]|^)ff([^\w]|$)", r"\1variableff\2", result)
    result = resub.sub(r"([^e]|^)Q([^\w]|$)", r"\1variableQ\2", result)
    result = resub.sub(r"([^e]|^)S([^\w]|$)", r"\1variableS\2", result)
    return result  # }}}

def deimplicit(expression) :


    def func(m):
        mid = m.group(2)
        p = ''.join( [chr(int(i) + 66 ) for i in mid ])
        return m.group(1) + p  + m.group(3)

    result  = resub.sub(r"([a-zA-Z]+)([0-9]+)([a-zA-Z]+)",func,expression)
    return result



lambdifymodules = ["numpy", {"cot": lambda x: 1.0 / numpy.tan(x)}]




class CoreQuestionOps():

    scope = scope;
    used_variable_list = [];
    is_staff = settings.RUNTESTS # runtests never gets a chance to set this properly via json


    def __init__(self):
        self.name = "core_class";
        self.hide_tags =  ["expression","value"] 
        self.userpk = 0


    def scope_update(self, nss ) :
        self.scope.update(nss); 
        return self.scope 


    def compare_expressions(self,  expression1, expression2, global_text, preamble="",precision_string="0",skip_syntax_check=False,testing_equality=False):
        args = ( expression1,expression2, global_text, preamble, precision_string, skip_syntax_check, testing_equality )
        try :
            ret = safe_run(self.core_runner, args )
            return ret
        except Exception as err  :
            return self._compare_expressions(args)



    def core_runner(self,*args, **kwargs ):

        response = self._compare_expressions(*args)
        result_queue = kwargs['result_queue']
        result_queue.put(response)





    def define_function_from_string(self, s):
        [lhs,rhs] = s.split(':=');
        substring = rhs.split('.osubs(',2)
        sub = ''
        if len( substring) == 2 :
            rhs = substring[0];
            sub = '(' + substring[1]
        pp    =  resub.split(r'\(|\)',lhs.strip()) 
        name = pp[0].strip()
        args = (',').join( [ i.strip() for i in pp[1].split(',') ] )
        erhs = rhs.strip()  ;
        serhs = sympify( erhs )
        funcs = list( set( [i.func for i in serhs.atoms(Function) if isinstance(i, AppliedUndef)]  ) )
        for func in funcs  :
            rhs = resub.sub(f"{func}",f"dummy{func}", rhs )
        erhs = sympify( rhs , self.scope, evaluate=False )
        vardefs =  ";\n".join( [ f"{arg} = Symbol(\"{arg}\", commutative=False  )" for arg in args.split(',') ] )+";";
        if sub  == '' :
            lambdadef = f"{name} = lambdify([{args}], implemented_function(\'{name}\', lambda {args}: {erhs})({args}), dummify=True );";
        else :
            lambdadef = f"{name} = lambdify([{args}], implemented_function(\'{name}\', lambda {args}: ({erhs}).osubs{sub})({args}), dummify=True );";
        for func in funcs  :
            lambdadef = resub.sub(f"dummy{func}",f"{func}", lambdadef )

        return lambdadef;




    def add(self, *xin):
        x = [ sympify( str(i), self.scope ) for i in xin ]
        m = [ i for i in x if isinstance(i, MatrixBase)];
        if len(m) > 0 :
            dims = shape(m[0]);
            if len( dims  ) == 2 and  dims[0] == dims[1] :
                id = eye(dims[0] )
                s  = tuple( [  i * id for i in x ] ) ;
                res = Add( *s)
                return res
            else :
                o = ones( *dims)
                newx = []
                for i in x :
                    ismatrix = isinstance( i, MatrixBase)
                    if not ismatrix :
                        newx.append(  sympify( o * i  ) )
                    else :
                        newx.append( i )
                res = Add(*newx)
                return res
        else :
            return Add(*x)
        ret = Add(*s)
        return ret

    def gobble_global_defs( self, global_text, preamble, **kwargs ) : # use_wedgerules=True, docache=settings.DO_CACHE):
        rulename = kwargs.get('use_wedgerules',None)
        use_wedgerules = ( rulename == None )
        do_cache = kwargs.get('do_cache',settings.DO_CACHE)
        global_text = resub.sub(r"[;]+",";",global_text)
        msg = None
        if preamble :
            exec( preamble ) # , globals() , locals() )
        self.scope_update(scope)
        self.scope_update(unitbaseunits)
        self.scope_update(globals());
        global_text_n = declash( global_text);
        lines = []
        gdefs = None
        if lines :
            gdefs = {}
            for line in lines :
                exec( line , self.scope );
                key = line.split('=',1)[0].strip();
                gdefs[key] = sympify( key, self.scope );
                self.scope_update({key : gdefs[key]})
        splits = global_text.split(";");
        isin = 'm1' in self.scope 
        
        if gdefs == None  : # or ':=' in global_text  :
            gdefs = {}
            ps = [ item.strip()   for item in global_text.split(";") ];
            for p in ps :
                p = p.strip();
                p = p.rstrip(';')
                parts = [ i.strip() for i in p.split('=',2 ) ]
                if len(parts) == 2 and  '[' in parts[0]  and not ':' == parts[0][-1]  :
                    lhs = sympify(parts[0] )
                    rhs = sympify(parts[1], self.scope)
                    zipped = zip( lhs, rhs );
                    ppnew = [];
                    for (right,left) in   zipped :
                        ppnew.append(f"{right} = {left}")
                else :
                    ppnew = [p] 
                try :
                    for q in ppnew :
                        q = self.asciiToSympy( q )
                        if ":=" in q :
                            q = self.define_function_from_string(q);
                        else :
                            if '[' in q :
                                pp = q.split('=');
                                if len(pp) == 2  and not '(' in pp[0] :
                                    [lhs,rhs] = pp;
                                    rhs = self.asciiToSympy( rhs)
                                    erhs =  sympify( rhs, self.scope);
                                    q =  f"{lhs} = {erhs}"
                        if q.strip() != ''  : # and not 'answer' in q :
                            try :
                                exec( q , self.scope )
                                pp = q.split("=")
                                key = pp[0].strip();
                                gdefs[key] = sympify( key, self.scope)
                                line = q.rstrip("\\;")
                                lines.append(line)
                            except Exception as e   :
                                if 'answer' in q :
                                    pass
                                else :
                                    logger.error(f"EXCEPTION RAISED IN p= {p } PARSING GLOBALS {str(e)} ")
                                    #assert False, str(e) 
                except Exception as e:
                    if not 'answer' in q : # DO NOT CHOKE ON OTHER ANSWERS BEING BROKEN
                        raise SympifyError(f"line {q} gives errors { str(e)} ");
                    #if 'name' in str(e):
                    #    raise e
        if gdefs :
            self.scope_update( gdefs)
        return True





    def reduce_using_defs(self, expression, global_text, preamble, units , **kwargs ) :
        #use_wedgerules = kwargs.get('use_wedgerules', True);
        docache = kwargs.get('docache', settings.DO_CACHE);
        rulename = kwargs.get('use_wedgerules',None)
        use_wedgerules = not rulename == None
        checkname = 'wedgecheck'
        
        if not hasattr(self, 'userpk') :
            self.userpk = 0;
        expression = expression.strip();
        expression_orig = expression
        sexpression = expression
        varhash =  get_hash_from_string(global_text + preamble  + str( units )  + f"{self.userpk}" )
        varhashb = get_hash_from_string(varhash + expression)
        if docache and settings.DO_CACHE:
            cache = caches["default"]
            resd = cache.get(varhashb)
        else:
            cache = None
            resd = None
        if ':=' in global_text  and settings.SAFE_CACHE :
            docache = False # CANNOT PICKLE LAMBDADEFS
        if docache and not resd == None  and settings.DO_CACHE :
            res = dill.loads( resd )
            return res
        pr = []

        global_text = resub.sub(r"[;]+",";",global_text)
        msg = None
        if preamble :
            exec( preamble, globals() , locals() )
        self.scope_update(scope)
        self.scope_update(units);
        self.scope_update(globals());
        global_text_n = declash( global_text);
        lines = []
        if docache and settings.DO_CACHE:
            lines = cache.get(varhash)
            if lines:
                lines = dill.loads(lines)
            else:
                lines = []
        else:
            lines = []

        gdefs = None
        if lines :
            gdefs = {}
            for line in lines :
                exec( line , self.scope );
                key = line.split('=',1)[0].strip();
                gdefs[key] = sympify( key, self.scope );
        splits = global_text.split(";");
        
        if gdefs == None  : # or ':=' in global_text  :
            gdefs = {}
            ps = [ item.strip()   for item in global_text.split(";") ];
            for p in ps :
                p = p.strip();
                p = p.rstrip(';')
                parts = [ i.strip() for i in p.split('=',2 ) ]
                if len(parts) == 2 and  '[' in parts[0]  and not ':' == parts[0][-1]  :
                    lhs = sympify(parts[0] )
                    rhs = sympify(parts[1], self.scope)
                    zipped = zip( lhs, rhs );
                    ppnew = [];
                    for (right,left) in   zipped :
                        ppnew.append(f"{right} = {left}")
                else :
                    ppnew = [p] 
                try :
                    for q in ppnew :
                        q = self.asciiToSympy( q )
                        if ":=" in q :
                            q = self.define_function_from_string(q);
                        else :
                            if '[' in q :
                                pp = q.split('=');
                                if len(pp) == 2  and not '(' in pp[0] :
                                    [lhs,rhs] = pp;
                                    rhs = self.asciiToSympy( rhs)
                                    erhs =  sympify( rhs, self.scope);
                                    q =  f"{lhs} = {erhs}"
                        if q.strip() != ''  : # and not 'answer' in q :
                            try :
                                exec( q , self.scope );
                                pp = q.split("=")
                                key = pp[0].strip();
                                gdefs[key] = sympify( key, self.scope)
                                line = q.rstrip("\\;")
                                lines.append(line)
                            except Exception as e   :
                                if 'answer' in q :
                                    pass
                                else :
                                    logger.error(f"EXCEPTION RAISED IN p= {p } PARSING GLOBALS {str(e)} ")
                                    assert False, str(e) 
                except Exception as e:
                    if not 'answer' in q : # DO NOT CHOKE ON OTHER ANSWERS BEING BROKEN
                        raise SympifyError(f"line {q} gives errors { str(e)} ");
                    if 'name' in str(e):
                        raise e
            try :
                if docache :
                    lines = dill.dumps( lines );
                    cache.set(varhash, lines , 60 * 60 )
            except Exception as err:
                logger.error(f" {str(err)} CORE CACHE NOT SET ")
                pass
        if gdefs :
            self.scope_update( gdefs)
        isin = rulename in self.scope
        
        wedgerules = {}
        if isin :
            wedgerules = self.scope[rulename]
            wedgecheck = self.scope[checkname]
        if type( expression  ) is str :
            sexpression =  self.asciiToSympy(expression , recur=True, debug=False)
        else :
            sexpression = str( expression )
        formatted_lines = ''
        try :
            sexpression = str( sexpression)
            sexpression = sexpression.rstrip().rstrip(';').rstrip();
            sexpression = resub.sub(f"IsEqual","eq",sexpression)
            pieces = str( sexpression).split('.subs(')
            isin = [ i  in self.scope  for i in ['IsEqual','npi','th','eq']  ]
            is_validation = self.scope.get('is_validation', False )
            if not is_validation  or rulename not in self.scope :
                use_wedgerules = None
            if len(pieces) == 1 :
                isin1 = 'dD' in self.scope
                isin2 = 'fg' in self.scope
                res = sympify(sexpression, self.scope, evaluate=True) # NECESSARY OR RUNTEST
                if use_wedgerules :
                    res = res.subs( wedgerules)
                    resz = simplify( expand( res ).subs(wedgecheck) )
                else :
                    if rulename and ( rulename in self.scope  ):
                        wedgecheck = self.scope[ checkname]
                        res1 = mychop( simplify( expand( res ).subs(wedgecheck) ) )
                        wedgerules = self.scope[rulename];
                        keys = set(  wedgerules.keys() ) 
                        atoms = set()
                        for key in keys :
                            atoms = atoms.union(  key.atoms(Symbol) )
                        isfree = True
                        for atom in list( atoms  ) :
                            if res1.has( atom ) :
                                isfree = False
                        if not isfree :
                            res2 = simplify( expand( res ) )
                            resz = simplify( expand( res1 - res2 ) )
                            if resz != 0  :
                                assert False, f"Incorrectly  reduced form in {res}"
            else :
                pieces[0] = pieces[0].replace('partial','myPartial')
                pieces[1] = '(' + pieces[1]
                if use_wedgerules :
                    p1 =  simplify( sympify(pieces[0] , self.scope, evaluate=True).subs(wedgerules))
                    p2 = simplify( sympify( pieces[1] , self.scope, evaluate=True).subs(wedgerules)) ;
                else :
                    p1 =  simplify( sympify(pieces[0] , self.scope, evaluate=True))
                    p2 = simplify( sympify( pieces[1] , self.scope, evaluate=True)) ;
                res =  p1.subs( p2 ) 
                res = res.doit()
                sexpression = str(res) 


        except ShapeError as e :
            assert False, f"ShapeError {str(e)}"
        except AssertionError as e :
            raise e
        except ValueError as e :
            if 'callable' in str(e) :
                msg = "illegal function use in {expression}"
            assert False, f"{str(e)}"
        except SyntaxError as e :
            msg = str(e)
            res['error'] = str(e)
            return res
        except Exception as e :
            formatted_lines = traceback.format_exc()
            msg = ''
            res = sympify(sexpression, evaluate=False)
            frees = [ i for i in res.free_symbols if not i in self.scope.keys()  ]
            funcs = [i.func for i in res.atoms(Function) if isinstance(i, AppliedUndef)]
            for func in funcs:
                pat = f"{func}(";
                if pat in sexpression:
                    ps = sexpression.split(pat)
                    pat = pat[0:len(pat)-1];
                    if type(e)  == AssertionError :
                        msg = f"{str(e)}"
                    else :
                        if not func.name in  ['Prime'] :
                            msg = msg + f"Illegal use of function {func}   ";

            for free in frees:
                pat = f"{free}(";
                if pat in sexpression:
                    ps = sexpression.split(pat)
                    pat = pat[0:len(pat)-1];
                    msg = msg + f"Illegal use of function {free}    ";
            
        if msg :
            #if formatted_lines :
            #    logger.info(f"FORMATTED_LINES {formatted_lines}")
            assert False, msg

        try :
            res = res.replace(partial, myPartial)
            res = res.replace(myFactorial, factorial)
        except :
            pass
        if docache and (isinstance(res, Float) or isinstance(res, float) or isinstance(res, int)):
            resd = dill.dumps(res)
            if settings.DO_CACHE and cache is not None:
                cache.set(varhashb, resd)
            return res 
        else :
            try :
                res = res.replace(Add,self.add);
            except :
                pass
        try :
            res = expand( simplify( res.doit()  ) );
        except  AttributeError as e :
            if 'tuple' in str(e) :
                assert False, "Error. Decimals use period, not comma. "
        except Exception as e :
            res['error'] = "Unknown error";
            logger.error(f"UNKNOWN_ERROR  {type(e).__name__} {str(e)} WITH  {expression}")

        if isinstance(res, bool):
            res = sympify("1") if res else sympify("0")
        if 'True' in str( type(res) ):
            res = sympify('1');
        elif 'False' in str( type(res) ):
            res = sympify('0');
        try :
            if docache and settings.DO_CACHE and cache is not None:
                resd = dill.dumps(res)
                cache.set(varhashb, resd)
        except  Exception as e :
            pass
        return res

    def get_free_atoms( self, v ):
        free = [ i for i in v.free_symbols if not i in self.scope  ]
        free = [ i for i in free if not str(i) in self.used_variable_list];
        res = ''
        if len(free) > 0 :
           res = f"Undefined symbols1 {free}"
        funcs = [i.func for i in v.atoms(Function) if isinstance(i, AppliedUndef)]
        if len( funcs) > 0 :
            res = f"Undefined function {funcs}"
        return res

    def get_precision(self, v, precision_string ):
        try :
            free = [ i for i in v.free_symbols if not i in self.scope.keys()  ]
            if len(free ) > 0 :
                return 0
        except :
            pass;
        vn = N(v,p53);
        if isinstance(v, MatrixBase):
            flat = [ abs(x) for x in flatten( v.tolist() ) if x.is_number ];
            vn = max( flat );
        if '%' in precision_string :
            np = sympify( precision_string.split('%')[0]) 
            precision = abs( N( np, p53 ) * N( .01, p53 ) * vn );
        else :
            precision = sympy.sympify( precision_string)
        return precision





    def is_zero(self, v, precision=COMPARISON_PRECISION , float_allowed=True, scale=1.0):
        print(f"PRECISION = {precision}")
        if isinstance( scale , Float) :
            print(f"IS_FLOAT")
            v = v/scale;
            precision = precision / scale;
            scale = 1.0;
        if hasattr( scale, "free_symbols") :
            if scale.free_symbols :
                scale = 1.0
        response = {};
        response['clean'] = True;
        if 'Infinity' in str( type(v) ):
            response['error'] = 'Your answer is infinite!'
            response['correct'] = False
            return response
        exact_required = not float_allowed
        try :
            vn = N( v ,p53,chop=True);
            vn = mychop(vn)
            free = [ i for i in v.free_symbols if not i in self.scope.keys()  ]
            funcs =  [i.func for i in v.atoms(Function) ] 
            if vn == 0 :
                return {'correct' : True , 'clean' : True }
            try :
                if simplify(v).is_zero :
                    return {'correct' : True , 'clean' : True };
            except :
                pass
        except Exception as e :
            formatted_lines = traceback.format_exc()
            logger.error(f"TRACEBACK  IN NAIVE ERROR TESTING = {formatted_lines}")
            logger.error(f" ERROR IN NAIVE ERROR TESTING {type(e).__name__} {str(e)}")
            pass

        vn = mychop(vn)
        vn = N( Abs(vn).doit(), chop=True);
        try :
            precision = max( precision, COMPARISON_PRECISION )
        except :
            return {};
        if vn.is_number :
            try :
                if vn <= CLEAN_PRECISION :
                    scale = 1.0;
            except  Exception as e :
                msg = "Failed : " 
                if  funcs   :
                    msg += f" Cannot evaluate {funcs}";
                if free :
                    msg += f" Undefined  variables2 {free}";
                msg = resub.sub(r"mymul","mul",msg)
                raise SympifyError(msg)
            precision = max( precision, COMPARISON_PRECISION * scale )
            response['debug'] = f" E3 diff={v} vn={vn} precision={precision}"
            if precision and float_allowed :
                vn = 0.99999999999 * vn;
            notsmall = abs(vn) > precision * scale
            nonzero  = abs(vn) > COMPARISON_PRECISION * scale 
            clean = abs(vn) <= CLEAN_PRECISION * scale ;
            response['correct'] =  bool( not notsmall );
            if exact_required :
                if response['correct'] and  nonzero :
                    del response['correct']
                if not clean :
                    response['clean'] = False
                if notsmall :
                    response['clean'] = True
            return response;
        try :
            response['correct'] = bool(  v == 0 )
        except :
            response['correct'] = False;
        return  response

    def compare_with_units(self, expression1, expression2,global_text,preamble, precision_string ,units, testing_equality ):
        response = {}
        if has_floatingpoint( expression2 ) and not has_floatingpoint(expression1 )  and precision_string == "0" :
            response['error'] = "Exact required ";
            if 'correct' in response :
                del response['correct']
            return response;
        use_wedgerules = True
        if testing_equality :
            use_wedgerules = False
        if use_wedgerules :
            rulename = 'wedgerules'
        else :
            rulename = None

        sympy1 = self.reduce_using_defs(expression1, global_text,preamble, units, use_wedgerules=rulename);
        sympy2 = self.reduce_using_defs(expression2, global_text,preamble, units, use_wedgerules=None);
        target = str( sympy2)
        isfiniteset =  'set' in str( type( sympy1) ) or 'Set' in str( type( sympy1) ) 
        if isfiniteset :
            ex1 = [ N( i , p53 ) for i in list( sympy1 ) ];
            ex2 = [ N( i , p53 ) for i in list( sympy2 ) ];
            s1 = FiniteSet( *ex1 );
            s2 = FiniteSet( *ex2 );
            result = {}
            if len( s1) != len(s2) :
                result['error'] = "Incorrect: length of the set is wrong."
            if areequal :
                result['correct']  = True
            else :
                result['correct'] = False
            return result


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
        if False  :
            tt1 = getkind(sympy1);
            tt2 = getkind(sympy2);
            skip = ( tt1 == 'undefned' ) or ( tt2 == 'undefined' )
            if not skip and   not ( tt1 == tt2 ) : ##  DISABLE TYPE TESTING IF UNDEFINED
                response['warning'] = self.get_free_atoms( sympy2 );
                if response["warning"] :
                        response['error'] = "Incorrect"
                else :
                    response['error'] = f"Answer should be a {tt1} but yours is  {tt2}"
                    response['correct'] = False
                response['clean'] = True;
                return response
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
                response['warning'] =  f"your submitted object is of the wrong type; it should be a matrix or vector.    "
            else :
                response['warning'] =  f"your submitted object is of the wrong type.   "
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
        response["exact"] = True;
        if resub.search(r"\.",f"{expression1}"):
            response["exact"] = False;
        float_allowed = False
        if not precision_string  == "0" :
            response["exact"] = False
            float_allowed = True
        scale = 1 ;
        if precision_string == "0" :
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

        tt1 = getkind(sympy1);
        tt2 = getkind(sympy2);
        if False :
            if not skip and not (tt1 == tt2 ) :
                response['error'] = f"Wrong type : your answer should be  {tt1} whereas it is {tt2} "
                response['clean'] = True;
                return response

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
        if  False and isnum( ts1 ) : # MISCUES STUDENTS IN TOO MANY CASES
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



    def check_for_disallowed( self,  expression1, expression2,global_text_raw ):
        rulename = 'wedgerules'
        checkname = 'wedgecheck'
        result = {}
        if self.is_staff  and settings.RUNTESTS : #
            return result
        try: 
            try :
                try :
                    ex2 = sympify( self.asciiToSympy( self.parse_matrix_transforms( declash( expression2),True)   ), evaluate=False);

                except SyntaxError as e :
                    assert False, f"disallowed syntax or variable (E1230)"

                except SympifyError as e :
                    assert False, f"disallowed syntax or variable (E1231)"
                except Exception as e :
                    assert False, f"disallowed syntax or variable (E1232) "
                try :
                    ex2 = ex2.doit()
                except AttributeError as e :
                    pass
            except Exception as e :
                raise e
            ex1 = sympify( self.asciiToSympy( self.parse_matrix_transforms( declash( expression1),True)   ), evaluate=False)
            try :
                ex1 = ex1.doit() 
            except AttributeError as e :
                pass

            m1atoms = []
            if hasattr( ex1, "atoms" ) :
                m1atoms =  list( ex1.atoms(Function)  )
            m1atoms = [ x for x in m1atoms if hasattr(x,'name')]
            nm1 = [ f.name for f in  m1atoms  ]
            m2atoms = []
            if hasattr( ex2, "atoms" ):
                m2atoms =  list( ex2.atoms(Function)  )
            m2atoms = [ x for x in m2atoms if hasattr(x,'name')]
            nm2 = [ f.name for f in  m2atoms ]
            v2 = [];
            v1 = [];
            if hasattr(ex2,'free_symbols') :
                v2 = [ str(i) for i in ex2.free_symbols  if not i in locals() ]
            if hasattr(ex1,'free_symbols') :
                v1 = [ str(i) for i in ex1.free_symbols  if not i in locals() ]

            f1 = [ str(i) for i in nm1 if not i in locals() ]
            f2 = [ str(i) for i in nm2 if not i in locals() ]
            funcs = []
            try :
                funcs = set( [ str( i.func ) for i in ex1.atoms(Function)  ]  ) # if isinstance(i, AppliedUndef)]
            except :
                pass
            

            ok = self.used_variable_list
            okstring = ','.join(ok);
            okstring = deimplicit( declash(okstring) );
            ok = okstring.split(',') +  ['e','pi','npi','I',rulename] + list( unitbaseunits.keys() )  + list(  self.scope.keys()  ) + list( funcs) 
            

            notok =  set( f2  + v2 )  - set( ok) 
            nv = [ str(i) for i in notok];
            nvs = ",".join(nv);
            nvs = deimplicit( reclash( nvs) );
            if len( nv ) > 0 :
                if self.is_staff:
                    if not 'correct' in result :
                        result["warning"] =   f"Not valid variables and the answer will not be permitted for students:: {nvs} "
                else :
                    result["warning"] =  f"Not valid variables:: {nvs}"
        except TypeError as e :
            result['warning'] = 'E1932: your input form is not allowed::'

        except AssertionError as e :
            result['warning'] = str(e)



        except  Exception as e :
            result["warning"] = f" Syntax error: {type(e).__name__}  "
            #formatted_lines = traceback.format_exc()
            #logger.error(f"FORMATTED_LINES {formatted_lines}")
            result['warning'] = 'E1933: your input form is not allowed'
        return result

    def parse_matrix_transforms(self,s,fake=False):
        return s



    def _compare_expressions(self, expression1, expression2,global_text_raw, preamble="" , precision_string="0", skip_syntax_check=False, testing_equality=False ):  # {{{
        orig1 = expression1;
        orig2 = expression2;
        result = self.check_syntax(expression2, global_text_raw );
        if result.get('error', False ):
            return result
        reveal_syntax = expression2
        expression1 = declash(  expression1);
        expression2 = declash(  expression2);
        warning = None
        if not skip_syntax_check  and ( expression1 != "0" or expression2 != "0") :
            result = self.check_for_disallowed( expression1, expression2, global_text_raw)
            warning  = result.get('warning', None)
            if  not self.is_staff and  warning :
                return result
        global_text_raw = declash(  global_text_raw);
        r = {};
        float_allowed = True
        global_texts = samples( global_text_raw);
        if not skip_syntax_check :
            result = self.check_syntax( expression1 , global_text_raw)
            if not result.get('correct',False )  :
                return result
        

        def hasunits( s ):
            r = False 
            for u in unitbaseunits :
                if u in s :
                    r = True;
            return r


        ng = 0;
        for global_text in global_texts :
            ng = ng + 1;
            
            global_text =       resub.sub(r"(\s|=|/|\+|-|\*)([0-9]*\.[0-9]*)(\s|/|\+|-|\*|$|;)", r"\1N(\2,p53)\3 ",global_text) 
    
            kseed = 1 ;
            try :
                global_text= declash( global_text); 
                randomunits = get_randomunits( kseed  ) 
                r = self.compare_with_units( expression1, expression2,global_text,preamble, precision_string ,unitbaseunits, testing_equality  );
                #if not r.get('correct') and r.get('clean') :
                #    break
                #if not r.get('correct' ) :
                #    assert False, r.get('error', str(r))
                unitless_correct = r.get('correct', False );
                if not float_allowed  and precision_string == "0" :
                   r['warning'] = "Exact responses only; no decimal poings allowed";
                   if 'correct' in response :
                        del response['correct']
                   #break;
                if not unitless_correct  and not skip_syntax_check  and not 'Matrix' in expression1 and not 'Matrix' in expression2  and not '{' in  expression1 and not '}' in  expression2:
                    if hasunits( global_text_raw + expression1 + expression2 ) :
                        e1 = self.reduce_using_defs( expression1, global_text, preamble, randomunits )
                        e2 = self.reduce_using_defs( expression2, global_text, preamble, randomunits )
                        if 'Matrix' in f"{e1} {e2}" :
                            break;
                        kseed = kseed + 8;
                        randomunits2 = get_randomunits( kseed ) 
                        ue1 = self.reduce_using_defs( expression1, global_text, preamble, randomunits2)
                        ue2 = self.reduce_using_defs( expression2, global_text, preamble, randomunits2)
                        scale = N( e1 * ue2 + e2 * ue1, p53 )
                        if scale == 0 :
                            scale = 1 
                        scale = myabs(scale).doit()
                        if not isnum( scale):
                            comment = self.get_free_atoms( scale )
                            r['comment'] = comment
                            return r
                        diff = abs( N( e1 * ue2 - e2 * ue1, p53 )).doit() ;
                        if not isnum( diff ):
                            comment = self.get_free_atoms( diff )
                            r['comment'] = comment
                            return r


                        diff = diff / scale;
                        try  :
                            if diff.is_zero()  :
                                break;
                        except :
                            pass 
                        try :
                            if abs( diff ) > COMPARISON_PRECISION :
                                r['warning'] = "Incorrect units"
                            else :
                                pass
                                #r['warning'] = r.get('warning', UNITS_OK )
                        except:
                            pass
                    break;
            except ShapeError as err :
                msg =  f"{type(err).__name__} { str(err) }";
                if '{' in expression2 :
                    msg = 'Incorrect number of independent entries in your list::'
                    r['error'] = msg 
                else :
                    r['error'] = f" incorrect vector or matrix shapes :: {str( err)}   ";
                break;
            except SympifyError as err :
                formatted_lines = traceback.format_exc()
                warning = ''
                if self.is_staff:
                    if 'not defined' in str(err) and 'lambdif' in str(err) :
                        try :
                            p = str(err).split('name')[1].split('\'')[1]
                        except :
                            p = 'x,y,z'
                        warning =  f'Author probably made function definition error:: The dummy variable {p} may not be defined. Set with  <vars> ... {p}</vars>' # \"&lt;vars&gtx,y,x&lt;/vars&gt;\".'
                    if warning :
                        return {'correct': False, 'error' : warning }
                    else :
                        return {'correct' : False ,  'error' :  str(err) }
                if ':' in str(err) :
                        msg = str(err).split(':')[1].strip('\"');
                        if 'Illegal' in msg and 'function' in msg :
                            msg = 'Perhaps you are using a variable as a function. '
                else :
                    msg =  resub.sub("SympifyError: ","", f"{str(err)}");
                formatted_lines = traceback.format_exc()
                logger.error(f"MSG1 = {msg}::  {expression1} ")
                if 'SyntaxError' in str(err) :
                    r['error'] = f'syntax error :: {reveal_syntax}'
                    r['debug'] = " E4 debug3"
                elif 'function' in str(err) :
                    r['error'] = 'function error ::'
                    return r;
                else :
                    formatted_lines = traceback.format_exc()
                    r['error'] = f"{msg} error:: {reveal_syntax}";
                break;
            except TypeError as err :
                if 'Symbol' in str(err) and 'subscriptable' in str(err) :
                    r['error'] = 'Looks like you are trying to take elements from an object that is not a matrix.::'
                    return r
                if 'One' in str(err) and 'callable' in str(err) :
                    r['error'] = 'Integer cannot multiply parenthesis without a space or multiplcation sign.::'
                if 'Integer' in str(err) and 'callable' in str(err) :
                    r['error'] = 'Integer cannot multiply parenthesis without a space or multiplcation sign.::'
                    return r
                if 'Float' in str(err) and 'callable' in str(err) :
                    r['error'] = 'Floating point number cannot multiply parenthesis without a space or multiplcation sign.::'
                    return r
                formatted_lines = traceback.format_exc()
                r['error'] =  f"Unknown syntax error; {reveal_syntax} illegal implicit multiply of variable?::"
                formatted_lines = traceback.format_exc()
                #logger.error(f"TRACEBACK1 = {formatted_lines}")
                e1 = sympy.sympify( self.asciiToSympy( expression1), self.scope );
                ismatrix = isinstance( e1, Matrix) 
                isscalar = isinstance( e1, Float)
                
                if 'cannot add ' in str(err) :
                    if ismatrix :
                        return {r'error' : f"Your answer  needs to be a matrix.:: " };
                    elif isscalar :
                        return {r'error' : f"Your answer  needs to be a number.:: " };
                    else :
                        return {r'error' : f"Your answer  is not of proper type; check if matrix or scalar is needed.:: " };

                try :
                    expression2 = self.parse_matrix_transforms( expression2 )
                    ex2 = sympify( expression2,  evaluate=False)
                    frees = [ i for i in sympify( ex2).free_symbols if not i in self.scope.keys()  ]
                    for free in frees :
                        pat = f"{free}(";
                        if pat in expression1 :
                            ps = expression1.split(pat)
                            pat = pat[0:len(pat)-1];
                            msg = f"Implicit multiply error:: {free} in {ps[0]} >{pat}<  ({ps[1]} is not permitted" 
                            r['error'] = msg;

                except Exception as err :
                    logger.error(f"EXEPTION OF EXCEPTION {str(type(err))}")
                logger.error(f"ERROR IN EXPRESSION  ABOVE WAS FOR expression1={expression1} expression2={expression2}")
            except ValueError as err :
                formatted_lines = traceback.format_exc()
                logger.error(f"TRACEBACK2 = {formatted_lines}")
                if 'shape'  in str(err) :
                    r['error'] = 'The shape of your matrix is inconsistent and/or wrong.::'
                else :
                    r['error'] = f"VALUE ERROR.:: ";
                break;
            except IndexError as err :
                formatted_lines = traceback.format_exc()
                logger.error(f"TRACEBACK3 = {formatted_lines}")
                r['correct'] = False;
                if 'list index out of range' in str(err) :
                    r['warning'] = "No answer given"
                    del r['correct'];
                return r            
            except AssertionError as err :
                if 'form' in str(err) :
                    r['error'] = f"error:: {str(err)}"
                    r['correct'] = False
                else :
                    r['error'] = f"Error:: {orig2} : {str(err)} "
                break;
            except AttributeError as err :
                r['error'] = f"Attribute Error: cannot parse :: {orig2}"
                break;
            except Exception as err :
                formatted_lines = traceback.format_exc()
                logger.error(f"TRACEBACK4 = {formatted_lines}")
                msg =  f"{type(err).__name__} { str(err) }";
                logger.error(f"MSG2 = {msg}")
                r['error'] = r.get("error",  f"A2 {type(err).__name__} ");
                logger.error(f"ORIG1 = {orig1}")
                logger.error(f"ORIG2 = {orig2}")
                break;
            if not r.get('correct',False ) :
                break;
        if warning :
            r['warning'] = warning

        return r

    def simplify_lists(self,s):
        return s

    def asciiToSympy(self, expression, recur=True, debug=False,fake=False):
        dict = {
            "^": "**",
        }
        rulename = 'wedgerules'
        expression_orig = expression
        expression = expression.replace("\n",'');
        expression = add_right_arg( expression, "Wedge",rulename)
        result = expression;



        if resub.search(r"[\w\)]+\[",result ) :
            result = functionalize_matrix_elements( result , self.scope)
            
        it = 0
        while result.find(")'") > 0 and it < 20:
            indend = result.index(")'")
            indbegin = index_of_matching_left(result, indend)
            ind = indbegin
            while ind > 0 and not result[ind - 1] in " +-/*":
                ind = ind - 1
            left = result[0 : max(0, ind - 1)]
            middle = result[ind : indend + 1]
            right = result[indend + 2 :]
            result = left + "myPartial(" + middle + ")" + right
            it = it + 1
        foundit = False
        if '!' in result :
            foundit = True
            it = 0
            result = resub.sub(r"(\w+)\s*!",r"myFactorial( \1 )",result)
            while result.find(")!") > 0  and it < 20 :
                indend = result.index(")!") 
                indbegin = index_of_matching_left(result, indend )
                ind = indbegin
                left = result[0 : max(0, ind )]
                middle = result[ind + 1 : indend  ]
                right = result[indend + 2 :]
                result = left + " myFactorial(" + middle + ")" + right
                it = it + 1

        if resub.search(r"[\w\)\$]+\[",result ) :
            result = functionalize_matrix_elements( result , self.scope)
        result = deimplicit( result.strip() )
        result = replace_primes( result)
        result = absify ( result );
        result = self.parse_matrix_transforms( result );
        result = resub.sub(r"e\^\(","exp(",result)
        result = resub.sub(r"\)\(",") (",result)
        result = resub.sub(r"(?<=[\w)])\s+(?=[(\w])", r" * ", result)
        result = resub.sub(r"(\W*[0-9]+)([A-Za-z]+)", r"\1 * \2", result)
        result = resub.sub(r"([a-zA-Z0-9\(\)])\)\(([a-zA-Z0-9\(\)])", r"\1)*(\2", result)
        result = resub.sub(r"\)\s+\[", r") * [ ", result)
        result = resub.sub(r"([0-9a-zA-Z])\s+\[", r"\1 * [ ", result)
        result = resub.sub(r"\]\s*([0-9a-zA-Z])",r"] * \1",result)
        result = resub.sub(r"\]\s*(\()",r"] * (",result)
        for old, new in dict.items():
            result = result.replace(old, new)
        if recur :
            result = self.matrixify( result);
        return result




    def check_syntax( self, s, xml="", validate=False):
        if '[' in str( xml  ):
            self.scope_update( {'matrices' : True } );
        result = {};
        if s.strip() == '' :
            result['error'] = "Blank response!::"
            return result
        result['correct'] = False
        s =  self.parse_matrix_transforms(s);
        m1 = resub.search(r"(acot|atan|arctan|acos|arccos|acos|arcos|asin|arcsin)", s )
        m2 = resub.search(r"(logger|print|sum)", s )
        m10 = resub.search(r"(acot|atan|arctan|acos|arccos|acos|arcos|asin|arcsin)", str( xml ) )
        syntax_error_flag = 'warning'
        if resub.search(r'\n+\s*\n+\s*\n+',s) :
            result[syntax_error_flag] = 'Remove multiple blank lines.::'
        elif resub.search(r'=',s ) and not resub.search(r'==',s ):
            result[syntax_error_flag] = 'Equal signs are not permitted in responses.::'
        elif resub.search(r"(?:^|\s)[0-9\.]+\(",s) :
            result[syntax_error_flag] = 'Incorrect implict multiply; space needed befor parenthesis.::'
        elif resub.search(r"\s+mul\(",s) :
            result[syntax_error_flag] = 'Use of mul is deprecated . Instead use ordinary muliplication symbol * to indicate matrix multiplication.::'
        elif resub.search(r"^mul\(",s) :
            result[syntax_error_flag] = 'Use of mul is deprecated . Instead use ordinary muliplication symbol * to indicate matrix multiplication.::'
        elif resub.search(r"\]\s*\[",s):
            result[syntax_error_flag] = "zero or more spaces between ] and [ is not permitted. Use multiplication sign, parenthesis  or comma to clarify your syntax.::"
        elif resub.search(r"(\^|/|\+|-|\*|/)[0-9\.]+\(", s ):
            result[syntax_error_flag] = 'Incorrect implicit multiply; insert space before the parenthesis.::'
        elif resub.search(r"\W[0-9\.]{2,}[a-zA-Z]+",s):
            result[syntax_error_flag] = 'Incorrect implicit multiply; insert space after the number.::'
        elif resub.search(r"\^(\+|-)", s ):
            result[syntax_error_flag] = 'Exponent cannot be followed by sign; use parenthesis .::'
        elif resub.search(r"\^\s", s ):
            result[syntax_error_flag] = 'Exponent cannot be followed by blank.::'
        elif resub.search(r"(?:^|\W)[0-9]+[A-Za-z]+",s):
            result[syntax_error_flag] = 'Illegal2 implicit multiply.::'
        elif resub.search(r"\\", s ):
            result[syntax_error_flag] = 'backslash not allowed.::'
        elif resub.search(r"(?:^|\s)[0-9\.]+\[",s):
            result[syntax_error_flag] = 'illegal implicit multiply : number precedes square bracket. Insert space muliplication sign or parenthesis to clarify your expression.::'
        elif resub.search(r"-\+", s ):
            result[syntax_error_flag] = '-+ not allowed.::'
        elif resub.search(r"\+-", s ):
            result[syntax_error_flag] = '+- not allowed.::'
        elif resub.search(r"--", s ):
            result[syntax_error_flag] = '-- not allowed.::'
        elif resub.search(r"\+\+", s ):
            result[syntax_error_flag] = '++ not allowed.::'
        elif resub.search(r"\s\^", s ):
            result[syntax_error_flag] = 'Blank cannot precede exponent.::'
        elif resub.search(r"\)(\w)", s ):
            result[syntax_error_flag] = 'Illegal3 implicit multiply ; add a space between close-open parens if you want multiply.::'
        elif resub.search(r"\)\[", s ):
            result[syntax_error_flag] = 'Illegal implicit multiply ; add a space between close-paren open-square-bracket if you want multiply.::'
        elif len( s.split('==')  ) > 2 :
            result[syntax_error_flag] = f" == can appear only once.::"
            return result
        elif resub.search(r"\^\[",s):
            result[syntax_error_flag] = "If you want to exponentiate matrix, use parenthesis around the brackets.::"
        elif resub.search(r"([^\w]|^)[0-9\.]{2,}[a-zA-Z]",s ) :
            result[syntax_error_flag] = f"Implicit multiply without space in is not allowed.:: {s}"
        elif not parens_are_balanced( s ):
            result[syntax_error_flag] = f"Parentheses are unbalanced in :: {s} ";
        elif not brackets_are_balanced( s ):
            result[syntax_error_flag] = "Brackets are unbalanced.:: ";
        elif m1   and not m10 and validate :
            result["error"] = f"The inverse trig function " + m1.group(1) + (" is forbidden in :: {s}  ")
        elif m2 :
            result[ "error"] = "forbidden function.::" + m2.group(1)
        else :
            result['correct'] = True

        return result

    def get_preamble(self, question_xmltree ):
        attribs = question_xmltree.attrib
        exerciseassetpath = attribs.get('exerciseassetpath','.');
        basepath = '/'.join( exerciseassetpath.split('/')[0:5] )
        searchpath = list( set( [exerciseassetpath] + glob.glob(f"{basepath}/*ettings*/*") ) )
        preamble = ""
        helperfiles = ['customfunctions', 'questions']
        extra_content = {}
        for sp in searchpath :
            for h in helperfiles :
                path = os.path.join(sp , f"{h}.py");
                if os.path.exists( path ) :
                    extra_content = open( path,"r").read();
                    preamble = preamble + extra_content

        preamble = resub.sub("scope\.update","self.scope_update",preamble) # Backward compatibility with devLinearAlgebra
        exec( preamble)
        self.scope_update(locals() )
        preamble = "from sympy import *\n" + preamble
        return preamble



    def get_text(self, gtree) :
        if gtree == None :
            return ''
        global_text = ''
        if len(gtree) == 0 :
            global_text = gtree.text
        else :
            ss = ''
            sn = [];
            for i in  gtree.xpath("./text()") :
                p = i.split(';')
                sn += p;
            s = [ i.strip() for i in sn if i.strip() ]
            if s:
                ss = ';\n'.join(s)
            global_text = ss
        globalvars = gtree.findall("var")
        if not globalvars  == None :
            for g in globalvars :
                if not g.find('token') == None and not g.find('value')  == None :
                    token = ( g.find('token').text ).strip() ;
                    value = ( g.find('value').text ).strip();
                    if token != None and value  != None :
                        global_text = global_text.strip()  + f"{token} = {value} ;\n"
        vv1 = ""
        if len( gtree.xpath("./vars")  ) >  0 :
            txt =  ( gtree.xpath("./vars")[0] ).text
            vv2 = [ i.strip() for i in txt.split(',')]
            for vv in vv2 :
                vv1 = vv1 + f"{vv} = var(\"{vv}\") ;\n" 

        vv3 = ""

        for otype in ['funcs'] :
            pat = f"./{otype}"
            if len( gtree.xpath(pat)  ) > 0 :
                txts =  [ i.text for i in  gtree.xpath(pat)] 
                for txt in txts :
                    vv4 = [ i.strip() for i in txt.split(',')]
                    for vv in vv4 :
                        vv3 = vv3 + f"{vv} = Function(\"{vv}\") ;\n" 



        if not global_text :
            global_text = ''
        if not vv1:
            vv1 = ''
        if not vv3 :
            vv3 = ''
        global_text = vv1    + vv3 + global_text + ';\n'
        if not global_text :
            global_text = ''
        return global_text

    def get_global_text(self, question_json, global_xmltree, question_xmltree) :

        global_text = self.get_text( global_xmltree)
        lines = global_text.split(';');
        i = 0;
        for line in lines :
            assert parens_are_balanced( line ), f"Unbalanced parenthesis in expression {i} \n  \" {line} \" "
            assert brackets_are_balanced( line ), f"Unbalanced brackes in expresion {i}  \n \" {line} \""
            i = i + 1 ;
        others = question_json.get('other_answers',{} )
        try :
            question_key = question_json['@attr']['key']
        except :
            question_key = 'DUMMY123'
        
        for key in others.keys() :
            val = others[key]
            if val  and not key== question_key :
                global_text += f"answer{key} = {val};\n"
        local_text = ''
        for tag in ['variables','local'] :
            try :
                local_text += question_xmltree.find(tag).text.strip();
            except :
                pass
        local_texts =  [ i.strip() for i in local_text.split(';') ]


        def rep(match) :
            key = match.group(1);
            return others.get( key ,"")
        tt = [];
        for t in local_texts :
            if '$$' in t :
                s = resub.sub(r"\$\$\((\w+)\)",rep,t)
                tt.append(s);
            else :
                tt.append(t);
        local_text = ';\n'.join( tt  ) + ';\n'
        global_text = global_text  + local_text;
        if global_text :
            global_text = global_text.strip();
        else :
            p = "npi = N( 3.1415926535897932384626433832795028841971693993751058, p53) ;\n " 
            return p;
        if "import" in global_text:
            global_text = "";
            raise NameError("imports are not allowed in global ")
        p = ';\n'.join( [ i.strip() for i in global_text.split(';') ] );
        p = "npi = N( 3.1415926535897932384626433832795028841971693993751058, p53) ;\n " + p
        p = p.lstrip(';').lstrip();
        return p


    def validate_question(self, question_json, question_xmltree, global_xmltree):
        db = question_json.get('db');
        subdomain = db
        if 'is_staff' in question_json :
            self.is_staff = question_json.get('is_staff')
        global_text = self.get_global_text(question_json, global_xmltree, question_xmltree)
        preamble = self.get_preamble( question_xmltree)
        question_key = question_json['@attr']['key']
        for b in  ['isfalse','istrue','iscorrect','isincorrect','expression']  :
            bbs = question_xmltree.findall(b) 
            for bb in bbs :
                if not parens_are_balanced( bb.text ):
                    assert False, f" : unbalanced parenthesis in  \"{b}\" "
                if not brackets_are_balanced( bb.text ):
                    assert False, f":  unbalanced bracket   in \"{b}\" "




        self.gobble_global_defs( global_text, preamble, use_wedgerules=None, docache=settings.DO_CACHE)
        correct_answer = None
        validate =  question_xmltree.attrib.get('validate', "True")  == "True"
        question_key = question_json['@attr']['key']
        if not validate :
            return (('warning' , f"skip validation for {question_key} ") )
        question_xml = etree.tostring( question_xmltree);
        others = question_json.get('other_answers',{} )
        keys = others.keys()
        student_answers =  question_xmltree.xpath('./expression')
        if not student_answers :
            return (('error' , f"Question  has no answer.:: {question_key}"))
        student_answer =  (question_xmltree.xpath('./expression')[0] ).text
        correct_answer = student_answer
        self.scope_update({"student_answer" : student_answer})


        if  '@' in global_text :
            question_key = question_json['@attr']['key']
            exercise_key = str( question_json.get('exercise_key') )
            username = 'super'
            try :
                subdomain = settings.SUBDOMAIN
                dbexercise = Exercise.objects.usign(db).get(exercise_key=exercise_key)
                user = User.objects.using(db).get(username=username)
                path = dbexercise.get_full_path() 
            except  Exception as err :
                if not settings.RUNTESTS :
                    raise err
                subdomain = 'openta';
                path = '.'
                user = 1
            db = subdomain
            usermacros = get_usermacros(user , exercise_key, question_key, None,  db)
            try :
                root = exercise_xmltree( path, usermacros)
                global_xpath = '/exercise/global'
                global_xmltree = (root.xpath(global_xpath) or [None])[0]
                question_xpath = f'/exercise/question[@key=\"{question_key}\"]'
                question_xmltree = root.xpath(question_xpath)[0]
            except Exception as e :
                if not settings.RUNTESTS :
                    raise e
        lines = global_text.split(';')
        lines = [ line for line in lines if line.strip() != '' ]
        for  line in lines:
            parts = line.split(' := ')
            if len( parts ) == 1 :
                parts = line.split(' = ')
            elif len( parts ) == 2 :
                rhs = parts[1]
                if len( rhs.split('=') ) > 1 :
                    return (("error" , "forgotten semicolon? Splits on \"=\" results in error :: {rhs} "))
                tst = self.check_syntax(rhs,'', validate=False)
                if not tst.get('correct',True) :
                    msg = tst.get('warning','') + f": error in global line :: {line} "
                    return  (("error", msg ))
            else :
                return (("error" , f"forgotten semicolon? Splits on \"=\" results in error :: {rhs}"))
        if preamble :
            exec( preamble ) # globals() here before
        bbs = question_xmltree.findall('isfalse') 
        corrects = question_xmltree.findall('iscorrect');
        expressions = question_xmltree.findall('expression')
        if expressions :
            expression =  ( expressions[0] ).text
        res = (("success" , "core xml validation done"))
        key  = question_json['@attr']['key']
        qtype = question_json['@attr'].get('type','default')
        for correct in corrects :
            txt = correct.text.strip();
            r =  self.answer_check(  question_json, question_xmltree, txt, global_xmltree,validate=False)
            if not r.get('correct',False ) :
                warning = ''
                if 'error' in r :
                    warning = r['error']
                    if 'unsupported' in warning :
                        warning = warning.split('unsupported')[0]
                        warning = warning + '. Check for undefined variable '
                elif 'warning' in r :
                    warning = r['warning']
                if 'valid variables' in warning :
                    match = resub.search(r"\w+\(", expression )
                    if match :
                        s = match.group()
                        warning = f'Illegal implicit multiply flagged in the substring: \"{s}\" : {warning} '
                target = r.get('target','')
                target = str( r ) 
                if target :
                    target = target.replace('Matrix','')
                    target = f' \nTo be consistent, a correct expression should be: \n{target}'
                msg =  html.escape( f" {warning}\n   The assertion that \n{expression}\n is equivalent to \n{txt}\n fails.  TARGET = :: {target}  " )
                return (('error',msg))
        for expression in expressions :
            txt = self.asciiToSympy(  declash( expression.text.strip().strip(';').strip() )); 
            r =  self.answer_check(  question_json, question_xmltree, txt , global_xmltree,validate=False)
            warning = r.get('warning','') + r.get('error',"") 
            if not r.get('correct',True) and not 'inverse' in warning :
                xml = etree.tostring( question_xmltree)
                if "istrue" or 'isfalse' in xml :
                    warning = warning + f": Make sure that  &lt;istrue&gt; .. &lt;/istrue>  and/or &lt;isfalse &lt;/istrue> evaluates to boolean"
                msg = html.escape( warning )
                assert False, msg
            correct_answer = txt

        incorrects = question_xmltree.findall('isincorrect');
        for incorrect in incorrects:
            txt = self.asciiToSympy(  declash( incorrect.text.strip() ));
            r =  self.answer_check(  question_json, question_xmltree, txt, global_xmltree ,validate=False)
            if r.get('correct',True) :
                res = (("error",f"A5 Validation error of {txt} in {qtype} question {key}  as incorrect fails. ::"))
                return res
        global_texts =  samples( global_text )
        kseed = 200;
        if correct_answer == None :
            return res 
        for global_text in global_texts :
            for b in  ['isfalse','istrue']  :
                bbs = question_xmltree.findall(b) 
                for bb in bbs :
                    self.scope_update({"is_validation" : True})
                    itxt = resub.sub(r"\s*;\s*$",'', bb.text )
                    itxt = declash( itxt.strip() )
                    itxt = itxt.replace('$$',f"( {correct_answer} )")
                    itxt = self.asciiToSympy( itxt, recur=True )
                    txtsub = itxt
                    randomunits2 = get_randomunits( kseed ) 

                    try :
                        if '==' in txtsub : # and 'IsEqual' in self.scope:
                            parts = txtsub.split('==')
                            txtsub = f"IsEqual( {parts[0]} , {parts[1]})"
                            parts =  [ self.reduce_using_defs( i , global_text, preamble, randomunits2, use_wedgerules=None, docache=False) for i in parts ]
                            parts = [ str( simplify( sympify( i, self.scope, evaluate=True ) ) ) for i in parts ]
                            txtsub = f"IsEqual( {parts[0]} , {parts[1]})"
                        else :
                            txtsub =  self.reduce_using_defs( txtsub , global_text, preamble, randomunits2)
                            txtsub = str( simplify( sympify( txtsub , self.scope, evaluate=True ) ) )
                    except AssertionError as err :
                        if b == 'istrue' :
                            raise err
                    randomunits =  get_randomunits( kseed );
                    kseed = kseed + 8 ;
                    txtsub = txtsub.rstrip().rstrip(';').rstrip().lstrip();
                    txtsub = resub.sub(f"[0-9\.]+e-[0-9]+",'0',txtsub)
                    rulename = 'wedgerules'
                    r = self.reduce_using_defs(txtsub , global_text, preamble, randomunits, use_wedgerules=rulename, docache=False)
                    isin = [ "IsEqual" in self.scope, "eq" in self.scope, "myeq" in self.scope  , "s" in self.scope, "exp" in self.scope  ]
                    tp = str( type( r )  )
                    try :
                        if not( 'bool' in tp or 'One' in tp or 'Zero' in tp ) :
                            res = (("error" , f" Boolean error ::  {b} returned {r} ; it must be a boolean such as $$ == {correct_answer} "))
                    except Exception as e :
                        res = (("error" , str(e)))
                    if len( global_texts) == 1 : # IF SAMPLES EXIST ALL THESE ARE NOT VALIDATED 
                        if b == 'isfalse' :
                            if int(r) == 1 or True == bool( r) :
                                res = (("error" , f"{b} returns {r}  for {bb.text} : it must be zero or False "))
                        if b == 'istrue' :
                            if r == 0 or False == bool( r) :
                                res = (("error" , f"{b} returns {r}  for {bb.text} : it must be 1 or True "))
        return res


    def mathematica_form(self, student_answer):
        s = str(srepr(sympify(self.asciiToSympy(student_answer))))
        s = resub.sub(r"\'", "", s)
        s = resub.sub(r"\[", "{", s)
        s = resub.sub(r"\]", "}", s)
        s = resub.sub(r"\(", "[", s)
        s = resub.sub(r"\)", "]", s)
        s = resub.sub(r"Global.", "", s)
        translations = {
            "Mul": "Times",
            "Pow": "Power",
            "Add": "Plus",
            "Integer": "Identity",
            "Symbol": "Identity",
            "cos": "Cos",
            "sin": "Sin",
            "tan": "Tan",
            "pi": "Pi",
            "abs": "Abs",
        }
        for key in translations.keys():
            s = resub.sub(r"%s" % key, translations[key], s)
        s = resub.sub(r"Identity\[([^\]]+)\]", r"\1", s)
        s = resub.sub(r"MutableDenseMatrix", "Identity", s)
        return s

    def matrixify(self, s ):
        return s
    
    def get_hints(self, student_answer, correct_answer ):
        return {} 
        s1 = self.matrixify( self.asciiToSympy( declash( student_answer )) );
        s2 = self.matrixify( self.asciiToSympy( declash( correct_answer ) ) );
        result = {};
        tss = sympify( s1  , evaluate=False);
        tsc = sympify( s2  , evaluate=False);


        more_symbols = ['npi'];
        more_funcs = ['sqrt'];
        
                
        frees =  [ i for i in tss.free_symbols ] # if not i in scope.keys()  ] )
        funcs =  [i.func for i in tss.atoms(Function) ]  #  if isinstance(i, AppliedUndef)] )
        freec =  [ i for i in tsc.free_symbols  ]  # if not i in scope.keys()  ] )
        funcc =  [i.func for i in tsc.atoms(Function) ]  #  if isinstance(i, AppliedUndef)] )
        
        for sym in more_symbols :
            if sym in s1 :
                frees.append(sym) ;
            if sym in s2:
                freec.append(sym) ;
                
        for sym in more_funcs :
            if sym in s1 :
                funcs.append(sym);
            if sym in s2:
                 funcc.append(sym) ;
        freec =  [ f"{i}" for i in freec ] ;
        frees = [ f"{i}" for i in frees ]
        funcc = [ f"{i}" for i in funcc ]
        funcs = [ f"{i}" for i in funcs ]
        
        extra_funcs = set(funcs) - set( funcc );
        extra_syms = set(frees) - set(freec);
        if not is_equality and extra_funcs or extra_syms :
            result['warning'] = result.get('warning','')
            result['warning'] += ' Hint: '
            if extra_funcs  :
                result['warning'] +=  f" functions : {extra_funcs}";
            if extra_syms:
                result['warning'] +=   f" symbols : {extra_syms}";
                result['warning'].replace("npi","pi")
            result['warning'] += ' are  not needed';
            result['warning'] = result['warning'].replace("npi","pi")
            result['warning'] = result['warning'].replace("Norm","abs")

        return result

    def answer_class( self, question_json, question_xmltree, student_answer, global_xmltree={} , level=0, validate=True) :
        preamble = self.get_preamble( question_xmltree)
        global_text = self.get_global_text( question_json, global_xmltree , question_xmltree)
        expression = student_answer
        units = unitbaseunits
        r = sympify( self.reduce_using_defs( expression, global_text, preamble, units , use_wedgerules=None) ).evalf()
        c = re( r ) + 500 * im(r)
        return c

    

    def answer_check( self, question_json, question_xmltree, student_answer, global_xmltree={} , level=0, validate=True) :
        expressions = question_xmltree.findall("expression")
        self.userpk = question_json.get('username',1)
        if not expressions : # IF THERE ARE NO CORRECT ANSWERS IN GRADING PUT IN ZERO TO AVOID ERROR 
            r = self.answer_check_( question_json, question_xmltree, '0' , student_answer, global_xmltree , level, validate )
            if r.get('correct',False ):
                return r
        for expression in expressions :
            correct_answer = expression.text.split(";")[0];
            if not parens_are_balanced( correct_answer ):
                r={'correct' : False, 'warning' : "unbalanced parenthesis"}
                return r
            if not brackets_are_balanced( correct_answer ):
                r={'correct' : False, 'warning' : "unbalanced brackets"}
                return r
            r = self.answer_check_( question_json, question_xmltree, correct_answer, student_answer, global_xmltree , level,validate)
            if r.get('correct',False ):
                return r
        return r

    def answer_check_(self, question_json, question_xmltree, correct_answer, student_answer, global_xmltree , level,validate):
        is_clean = True
        testing_equality = False;
        all_correct_answers = question_xmltree.find("expression")
        xml = etree.tostring( question_xmltree )
        if global_xmltree  == None :
            global_xml = ''
        else :
            global_xml = etree.tostring( global_xmltree)

        ok = question_json.get('used_variable_list',[]);
        self.used_variable_list = ok;
        if 'is_staff' in question_json :
            self.is_staff = question_json.get('is_staff')
        result = self.check_syntax( student_answer, correct_answer , validate=validate)
        reveal_syntax = student_answer
        r = {};
        if "==" in correct_answer and not "==" in student_answer :
            reveal_syntax = ''
            r['error'] = 'Answer in the form of an equality.:: '
            return r;
        if '==' in student_answer and not '==' in correct_answer :
            reveal_syntax = ''
            r['error'] = 'Equality is not allowed in your answer.::'
            return r
        if "==" in student_answer and '==' in correct_answer :
            testing_equality = True;
            reveal_syntax = ''
            if len( student_answer.split('==') ) > 2 :
                return {'error' : 'Only one equality can be tested.::' };
            [ student_answer , correct_answer ] = student_answer.split('==')
            r1 = self.check_syntax( student_answer ,global_xml ,validate=validate)
            if not r1.get('correct', False ) :
                return r1
            r2 = self.check_syntax( correct_answer, global_xml ,validate=validate)
            if not r2.get('correct', False ) :
                return r2
        precision_string = question_xmltree.attrib.get('precision',"0");
        result = self.check_syntax( student_answer ,global_xml,validate=validate)
        if not result.get('correct',False )  :
            if 'correct' in result and 'warning' in result :
                del result['correct']
            return result
        if not precision_string :

            if not has_floatingpoint( correct_answer ) :
                if has_floatingpoint( student_answer) :
                    r['error'] = "Exact answer required; no decimals in the reply.::";
                    return r

        preamble = self.get_preamble( question_xmltree)
        global_text = self.get_global_text( question_json, global_xmltree , question_xmltree)



        [ expression1 , expression2 ] = [ correct_answer , student_answer ]
        result = {}
        did_logicals = False
        rc = {};
        rc['correct'] = True
        for logical in ['isfalse','istrue'] :
            tests = question_xmltree.findall(logical)
            for test in tests :
                did_logicals = True
                txt = test.text
                testing_equality = True
                if '==' in txt :
                    r = txt ;
                    try :
                        r = resub.sub(r"\$\$\(\s*(\w*)\s*\)",  lambda x : o[ x.group(1) ] , r )
                    except KeyError as e :
                        assert False, ("The answer referenced is not defined. ")
                    r = r.replace("$$",f"({student_answer})" );
                    p = [ i.strip() for i in r.split('==') ];
                    [p2, p1] = p;
                else :
                    p2 = resub.sub(r"(\$\$)",student_answer,txt)
                    p1 = "1"
                [ tp1 , tp2 ] = [ p1 , p2 ]
                result = self.compare_expressions(tp1 , tp2 ,global_text,preamble,precision_string,skip_syntax_check=True,testing_equality=testing_equality)
                if logical == "istrue" :
                    if  not result.get('correct',False)  :
                        rc['correct'] = False
                        comments = test.findall("if-not-so") 
                        for comment in comments :
                            rc['error'] = rc.get('error','')  +  result.get('error','') + comment.text
                    if  result.get('correct',False)  :
                        comments = test.findall("if-so") 
                        for comment in comments :
                            rc['comment'] =  rc.get('comment','') + comment.text

                if logical == "isfalse" :
                    if 'warning' in result :
                        rc['warning'] = result['warning']
                    if  result.get('correct',False)  == True :
                        if 'rue' in test.attrib.get('sufficient',"True" )  :
                            rc['correct'] = False
                        comments = test.findall("if-not-so") 
                        for comment in comments :
                            rc['error'] =   comment.text
                    if  result.get('correct',False)   == False :
                        comments = test.findall("if-so") 
                        for comment in comments :
                            rc['comment'] =  comment.text
                            if 'warning' in result :
                                rc['warning'] = result['warning']






        if did_logicals :
            if rc.get('correct', False) and rc.get('warning',False):
                if rc['warning'] == UNITS_OK :
                    del rc['warning']
            if 'correct' in rc :
                return rc
        result = self.compare_expressions(expression1 , expression2 ,global_text,preamble,precision_string,skip_syntax_check=False , testing_equality=testing_equality)
        if 'comment' in rc :
            result['comment'] = result.get('comments','') + rc['comment'] + "::"
        if "correct" in result:
            result["status"] = "correct" if result["correct"] else "incorrect"
        elif "error" in result:
            result["status"] = "error"
            return result;



        if 'correct' in result :
            is_clean = True;
        if 'clean' in result :
            is_clean = result['clean']
        if 'error' in result :
            is_clean = True


        chars_student = len( resub.sub(r"\s+",'', student_answer ));
        chars_correct = len( resub.sub(r"\s+",'', correct_answer ));

        freq = 1;
        n_attempts = question_json.get('n_attempts',0)

        if n_attempts % freq  ==  freq - 1   and not testing_equality and not result.get('correct',False) :
            try :
                hints =  self.get_hints( student_answer, correct_answer) 
                result.update( hints );
            except :
                pass
    

        if not testing_equality and not is_clean   and  level < 1  :


            level = level + 1;

            try :
                old_student_answer = student_answer;
                ts = self.asciiToSympy( declash( student_answer ) );
                ts = resub.sub("npi","pi",ts)
                ts = simplify( trigsimp( powsimp( ts) ));
                new_student_answer = f"{ts}"
                resnew = self.answer_check( question_json, question_xmltree, new_student_answer, global_xmltree=global_xmltree , level=level)
                if 'correct' in resnew :
                    if not resnew['correct']  :
                        del resnew['correct'];
                result.update( resnew)

            except Exception as e :
                logger.error(f"{type(e).__name__} COULD NOT SIMPLIFY {ts}")
                pass

            if 'correct' in result :
                if result.get('correct',False ) :
                    result['warning'] = "OpenTA could identify your answer as correct only after the algebra was cleaned up! Simplify if you want the green box."
            return result

        if not result.get("comment",False )  and result.get('correct',False ):
            result['comment'] = IS_CORRECT
        if rc.get('comment',False ) :
            result['comment'] =  result.get('comment','')  + '  (' + rc['comment']  + ') .::' 
        return result
    
    def json_hook(self,  safe_question, full_question, question_id, user_id, exercise_key, feedback) :
        safe_question_ = core_json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback)
        return  safe_question_
        

def osubs(self ,*args, **kwargs ):
    ruls = simplify( args , CoreQuestionOps.scope, evaluate=True)
    res = self.subs( *ruls , **kwargs) 
    return res


sympy.Basic.osubs = osubs
sympy.MutableDenseMatrix.osubs = osubs
