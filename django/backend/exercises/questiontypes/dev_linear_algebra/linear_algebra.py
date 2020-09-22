import time
from sympy.matrices.matrices import ShapeError
import django.core.cache as djangocache
from wolframclient.evaluation import WolframLanguageSession
from wolframclient.language import wl, wlexpr
from numpy.linalg import norm
from numpy import absolute
import types
import sys
from sympy import *
from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
from django.conf import settings
import re as reg
import traceback
import random
import itertools
from sympy.core import S
from exercises.util import get_hash_from_string
from sympy.utilities.lambdify import lambdify, implemented_function
from exercises.questiontypes.safe_run import safe_run
import logging
from .string_formatting import (
    absify,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
    paren_check,
    replace_sample_funcs
)
from .string_formatting import insert_implicit_multiply 
from .unithelpers import *
from sympy import DiagonalOf
import sympy
from .functions import *
from .checks import check_for_legal_answer, lambdifymodules, LinearAlgebraUnitError, check_units_new, mysqrt
import numpy
from .parsers import parse_sample_variables
from .variableparser import getallvariables, get_used_variable_list
from .sympify_with_custom import sympify_with_custom


logger = logging.getLogger(__name__)

# meter, second, kg , ampere , kelvin, mole, candela = sympy.symbols('meter,second,kg,ampere,kelvin,mole,candela', real=True, positive=True)
# see http://iamit.in/sympy/coverage-report/matrices/sympy_matrices_expressions_diagonal_py.html
# List of special handling in the conversion from sympy to numpy expressions for final evaluation


def linear_algebra_check_if_true(
    precision, variables, correct, expression, check_units=False, blacklist=[], funcsubs={}
):
    shouldbetrue = correct + '== 1'
    return linear_algebra_compare_expressions(
        precision, variables, expression, shouldbetrue, check_units=True, blacklist=[], funcsubs={}
    )

def mathematica_form( student_answer ) :
    #print("STUDENT_ANSWER = ", student_answer)
    s  = str( srepr( sympy.sympify( ascii_to_sympy( student_answer) ) ) )
    #print("S = ", s )
    s = reg.sub(r"\'","",s)
    s = reg.sub(r"\[","{",s)
    s = reg.sub(r"\]","}",s)
    s = reg.sub(r"\(","[",s)
    s = reg.sub(r"\)","]",s)
    s = reg.sub(r"Global.","",s)
    translations = {"Mul":"Times",
        "Pow":"Power",
        "Add": "Plus",
        "Integer": "Identity",
        "Symbol":"Identity",
        "cos": "Cos",
        "sin": "Sin",
        "tan": "Tan",
        "pi" : "Pi" ,
        "abs" : "Abs",
        }
    for key in translations.keys():
        s = reg.sub(r'%s' % key, translations[key], s )
    s = reg.sub(r'Identity\[([^\]]+)\]',"\\1",s)
    s = reg.sub(r'MutableDenseMatrix','Identity',s)
    #print("S = ", s )
    return s

def equality_remap( student_answer, correct, varsubs_sympify):
    tbeg = time.time()
    is_equality =  False
    equality = correct.split('==')
    if len(equality) > 1 and '$$' in correct:
            is_equality = True
            correct = equality[1]
            student_answer = (equality[0]).replace('$$', '(' + student_answer + ')')
    if '==' in student_answer:
            is_equality = True
            equality = correct.split('==')
            if not len(equality) == 2 :
                raise NameError("Error in equality syntax in student answer %s " % str(student_answer) )
            correct = 'Abs( (' + equality[0] + ') - ( ' + equality[1] + '))'
            correct = '0'
            equality = student_answer.split('==')
            student_answer = 'Abs( (' + equality[0] + ') - ( ' + equality[1] + '))'
    if is_equality : # DON'T DO SAMPLING IN EQUALITY 
        student_answer = replace_sample_funcs( student_answer )
        correct = replace_sample_funcs( correct )
        for key in varsubs_sympify.keys() :
            #dprint("KEY = ", key )
            varsubs_sympify[key] = sympy.sympify( replace_sample_funcs( str( varsubs_sympify[key]  ) ) )
    #print("TIME IN EQUALITY REMAP " , int( 1000 * (  time.time() - tbeg ) ) )
    return ( student_answer, correct ,varsubs_sympify)

def check_answer_structure( student_answer, correct , varsubs_sympify):
    response = None
    prelhs = None
    tbeg = time.time()
    try:
       tstudent_answer = replace_sample_funcs( student_answer)
       #print("      TSTUDENTANSWER = ", tstudent_answer)
       #print("      TYPE VARSUBS_SUMPFIY = ", type( varsubs_sympify) )
       tvarsubs_sympify = {}
       for key in varsubs_sympify.keys() :
            #print("     KEY = ", key )
            tvarsubs_sympify[key] = sympy.sympify( replace_sample_funcs( str( varsubs_sympify[key]  ) ) )
       #dprint("      TVARSUBS_SYMPIFY = ", tvarsubs_sympify)
       prelhs = sympify_with_custom( tstudent_answer, tvarsubs_sympify, {}, 'check-answer-structure-linear_algebra_compare_expressions')
    except TypeError as e:
        if 'required positional' in str(e) :
            response = dict(
                error = _( 'function is missing an argument')
                )
        else:
            response = dict(
                error=_( 'syntax error' ),
                debug="Error 187: " +  str(e) + traceback.format_exc()
                )
        #return response
    
    except NameError as e:
        response = dict(
                error=_( str(e) ),
                debug="Error 193: " +  str(e)
                )
        #return response
    
    except ShapeError as e:
        response = dict(
                error=_("Matrix dimensions inconsistent with each other or with the result. You must mul(A,B) for multiplying a matrix or matrix times vector"),
                debug="Error 202: " +  str(e)
                )
        #return response
    except Exception as e:
        response = dict(
            error=_(
                str( type(e)  )
                + " Error 213: Unidentified Error PROGRAMMING ERROR/ERROR \n "
                + str(student_answer)
                + "\n"
                + str(e)
            )
        )
    dprint("     RESSPONSE = ", response)
    dprint("     PRELHS = ", prelhs )
    #print("TIME CHECK_ANSWER_STRUCTURE " , int( 1000 * (  time.time() - tbeg ) ) )
    return response

def check_consistency(  lhs, rhs ,blacklist) :
    tbeg = time.time()
    response = None
    if hasattr(lhs, 'shape') and hasattr(rhs, 'shape'):
        if lhs.shape != rhs.shape:
            return {
                "error": _("incorrect dimensions")
                + ": your answer has the dimensions "
                + str(lhs.shape)
                + " whereas  the answer requires the dimensions "
                + str(rhs.shape)
            }
    #print("A6")
    if hasattr(lhs, 'shape') and not hasattr(rhs, 'shape') and ( not rhs == 0 ):
        return {
            "error": _("incorrect dimensions")
            + ": your expression is a matrix or vector; a scalar answer is required."
        }
    if hasattr(rhs, 'shape') and not hasattr(lhs, 'shape') and ( not lhs == 0 ) :
        return {
            "error": _("incorrect dimensions")
            + ": your expression is a scalar; a vector or matrix answer is required."
        }
    #print("A7")
    if isinstance(lhs, sympy.Basic) or isinstance(lhs, sympy.MatrixBase):
        specials = [
            ('cross', Cross),
            ('dot', Dot),
            ('norm', Norm),
            ('Braket', Braket),
            ('KetBra', KetBra),
            ('KetMBra', KetMBra),
            ('Trace', Trace),
            ('gt', gt),
        ]
        for special in specials:
            if special[0] in blacklist and (special[0] in str(lhs)):
                return {"error": _("(E) Forbidden token: ") + special[0]}
        atoms = lhs.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
        for atom in atoms:
            strrep = str(atom)
            funcstr = str(atom.func)
            if strrep in blacklist:
                return {"error": _("(F) Forbidden token: ") + strrep}
            if funcstr in blacklist:
                return {"error": _("(G) Forbidden token: ") + funcstr}
        #print("POSITION 5", 1000 * ( time.time() - time_start ) ); 
    #print("TIME CHECK_CONSISTENCY " , int( 1000 * (  time.time() - tbeg ) ) )
    return None



    

def dprint(*args) :
    return

def linear_algebra_compare_expressions(
    precision,
    variables,
    student_answer,
    correct,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs={},
    ):
    tbeg = time.time()
    _ , varsubs_sympify, sample_variables = parse_sample_variables(variables)
    dprint("VARIABLES = ", variables )
    student_answer_unparsed = student_answer
    # #############################################
    # IF EQUALITY IS USED, SAMPLING IS DISABLED 
    # AND zero = LHS - RHS 
    # ############################################
    #print("TIME B0a" ,  1000 * ( time.time() - tbeg ) )
    #print("STUDENT_ANSWER = ", student_answer)
    #illegal = reg.findall(r'(^|\s|[+-/*\(\)])+[0-9\.]+[a-zA-Z]+', student_answer)
    #if len(illegal) >  0 :
    #    #print("WAS ILLEGAL",illegal)
    #    s = ",".join( [ "".join(item) for item in illegal])
    #    ret = dict(error= _('Illegal pattern %s in %s ' % (s, student_answer)  ) ) 
    #    return ret
    #if not  len(correct.split('==') )  == len( student_answer.split('==') ) :
    #    response = {"error" : "inconsistent equality in %s . " % str(student_answer)  , 
    #        "warning" : "must be consistent with %s " % correct }
    #    return response
    student_answer = declash( student_answer)
    correct = declash( correct )
    try:
        (student_answer, correct ,varsubs_sympify ) = equality_remap( student_answer, correct ,varsubs_sympify)
    except:
        response = {'error' : "Equality syntax incorrect in student expression [%s] " % student_answer_unparsed }
        return response
    #print("TIME B0b" ,  1000 * ( time.time() - tbeg ) )
    student_answer = insert_implicit_multiply( student_answer)
    correct_answer = insert_implicit_multiply( correct )
    compare_hash = get_hash_from_string( " %s %s %s %s %s %s %s %s %s " % ( str(precision), str(variables), str(student_answer), 
            str(correct_answer), str(check_units), str(used_variables), str(blacklist), str(funcsubs)   , __file__ ) )
    #ret = djangocache.cache.get(compare_hash)
    #if not ret == None :
    #        return ret
    student_answer_orig = student_answer
    time_start = time.time()
    #print("LINEAR_ALGEBRA_COMPARE_EXPRESSIONS")
    #print("VARIABLES" , variables )
    #print("STUDENT_ANSWER", student_answer)
    #print("CORRECT", correct)
    #print("USED_VARIABLES", used_variables)
    #print("VARSUBS_SYMPIFYF ", varsubs_sympify)
    #print("TIME B0" ,  1000 * ( time.time() - tbeg ) )
    precheck = check_for_legal_answer( precision, variables, student_answer, correct, check_units, blacklist)
    #print("TIME B1" ,  1000 * ( time.time() - tbeg ) )
    #print("PRECHECK = ", precheck)
    if precheck is not None:
        return precheck
    
    dprint("VARSUBS_SYMPIFY = ", varsubs_sympify)
    dprint("SAMPLE_VARIABLES = ", sample_variables)
    response = check_answer_structure( student_answer, correct, varsubs_sympify ) 
    #print("TIME B2" ,  1000 * ( time.time() - tbeg ) )
    if response :
        return response
    try :
        #print("TIME B3" ,  1000 * ( time.time() - tbeg ) )
        prelhs = sympify_with_custom( student_answer , varsubs_sympify, {}, 'linear_algebra_compare_expressions-2' )
        lhs = prelhs.doit()
        #print("TIME B4" ,  1000 * ( time.time() - tbeg ) )
        prerhs = sympify_with_custom( correct, varsubs_sympify, {}, 'linear_algebra_compare_expressions-3' )
        rhs = prerhs.doit()
        #print("TIME B5" ,  1000 * ( time.time() - tbeg ) )
    except Exception as e:
        if '@' in str(e):
            explanation = "The character @ appears in author expression; check for macros with missing semicolon separator or missing :=  in macro definition"
        else:
            explanation = ""
        response = dict(error=_("ERROR IN AUTHOR EXPRESSION. " + explanation),
                        warning=("%s %s %s" % ( type(e), str(e), traceback.format_exc() )) )
        return response
    #print("POSITION 4", 1000 * ( time.time() - time_start ) );
    #print("TIME B6" ,  1000 * ( time.time() - tbeg ) )
    response = check_consistency( lhs, rhs ,blacklist) 
    if response :
        return response
    #print("TIME B7" ,  1000 * ( time.time() - tbeg ) )
    #print("CHECK LHS = ", lhs )
    #print("CHECK RHS = ", rhs)
    #print("SAMPPLE_VARIABLES = ", sample_variables)
    ret = linear_algebra_check_equality( precision, lhs, rhs, sample_variables, check_units=check_units)
    #print("POSITION6")
    #print("TIME B8" ,  1000 * ( time.time() - tbeg ) )
    #try:
    #    ret['mathematica'] = "Math Expression: {%s , %s }" % (  mathematica_form(student_answer), mathematica_form( correct_answer) )
    #except:
    #    ret['mathematica' ] = "Cannot parse mathematica: [%s,%s]" % ( student_answer, correct_answer)
    #print("TIME B9" ,  1000 * ( time.time() - tbeg ) )
    #ret['mathematica'] =  str( mathematica_form(correct_answer)  )
    #print("RET = ", ret )
    #time_beg = time.time()
    #with WolframLanguageSession() as wl_session:
    #    res = wl_session.evaluate(wlexpr( mathematica_form( student_answer ) ) )
    #print("RES = ", res )
    #print("TIME = ", ( time.time() - time_beg ) * 1000 )
    djangocache.cache.set(compare_hash, ret , 600 )
    return ret

#samplemodule = [
#    {
#        'cot': lambda x: 1.0 / numpy.tan(x),
#        'exp': lambda x:  numpy.exp(x),
#        'sqrt': lambda x: numpy.sqrt(x),
#        'real': lambda x: numpy.real(x),
#        'norm': lambda x: numpy.linalg.norm(x),
#        'logicaland': numpy.logical_and,
#        'logicalor': numpy.logical_or,
#        'eq': numpy.equal,
#        'Norm': lambda x:  numpy.linalg.norm(x) ,
#        'abs':  lambda x:  numpy.linalg.norm(x) ,
#        'cross': lambda x, y: numpy.cross(x, y, axis=0),
#        'crossfunc': lambda x, y: numpy.cross(x, y, axis=0),
#        'dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
#        'Dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
#        'zoo': numpy.inf,
##        'I': numpy.complex(0, 1),
#    },
#    "numpy",
#]


#sample_module = [
#    {
#    'sample' : lambda *x: dorand(x) ,
#    'Norm': lambda x: numpy.linalg.norm(x),
#    }, 
#    "numpy"
#]

sample_module = [
    {
        'sample' : lambda *x: dorand(x) ,
        'cot': lambda x: 1.0 / numpy.tan(x),
        'exp': lambda x:  numpy.exp(x),
        'sqrt': lambda x: mysqrt(x),
        'real': lambda x: numpy.real(x),
        'norm': lambda x: numpy.linalg.norm(x),
        'eq': lambda x,y: 1.0 if numpy.equal(x,y) else 0.0 ,
        'logicaland': numpy.logical_and,
        'logicalor': numpy.logical_or,
        'Norm': lambda x:  numpy.linalg.norm(x) ,
        'abs':  lambda x:  numpy.linalg.norm(x) ,
        'cross': lambda x, y: numpy.cross(x, y, axis=0),
        'crossfunc': lambda x, y: numpy.cross(x, y, axis=0),
        'dot': lambda x, y: numpy.vdot(x,y),
        'Dot': lambda x, y: numpy.vdot(x,y),
        'zoo': numpy.inf,
        'I': numpy.complex(0, 1),
    },
    "numpy",
]


#def mysqrt(x) :
#    x = x + numpy.complex(0,0)
#    if  numpy.isscalar(x) :
#        return numpy.sqrt(numpy.abs(x) )
#    else :
#        print("Trying to take sqrt( %s ) type= %s " % ( str(x), type(x)  ) )
#        return 0
#        #raise ValueError("Trying to take sqrt( %s ) type= %s " % ( str(x), type(x)  ) )

base_module = [
    {
        'cot': lambda x: 1.0 / numpy.tan(x),
        'exp': lambda x:  numpy.exp(x),
        'sqrt': lambda x: mysqrt(x),
        'real': lambda x: numpy.real(x),
        'norm': lambda x: numpy.linalg.norm(x),
        'Norm': lambda x: numpy.linalg.norm(x),
        'logicaland': numpy.logical_and,
        'logicalor': numpy.logical_or,
        'eq': lambda x,y: 1.0 if numpy.equal(x,y) else 0.0 ,
        'Norm': lambda x:  numpy.linalg.norm(x) ,
        'abs':  lambda x:  numpy.linalg.norm(x) ,
        'cross': lambda x, y: numpy.cross(x, y, axis=0),
        'crossfunc': lambda x, y: numpy.cross(x, y, axis=0),
        'dot': lambda x, y: numpy.vdot(x,y),
        'Dot': lambda x, y: numpy.vdot(x,y),
        'zoo': numpy.inf,
        'I': numpy.complex(0, 1),
    },
    "numpy",
]






def dorand(x) :
    global kseed
    s = 0
    #print(" DORAND rr = ", rr )
    random.seed(kseed)
    for value in x :
        s = s + value  * ( 0.5  + random.random() )
    return s


sample_project= [
    {
    'sample' : lambda *x: x[0] ,
    }, 
    "sympy"
]




kseed = 5

def linear_algebra_check_equality(precision, lhs, rhs, sample_variables, check_units=True):  # {{{
    global kseed
    lhsorig = lhs
    rhsorig = rhs
    tbeg = time.time()
    dprint("LINEAR_ALGEBRA_CHECK_EQUALITY check_units",  check_units)
    # LHS = student_answer
    # RHS = correct
    if rhs == 0.0 :
        rhs = 0.0 * lhs
        #print("RHS = 0", rhs )
        check_units = False
    if lhs == 0.0 :
        lhs = 0.0 * rhs
        check_units = False
        #print("LHS == 0 ", lhs )
    number_of_points = 5
    response = {}
    # response['ABC'] = 'ABC';
    time_start = time.time()
    #print("LHS, RHS = ", lhs, rhs )
    inner = 'BEGIN: '
    #print("LINEAR_ALGEBRA CHECK EQUALITY LHS ", str( lhs ) )
    #print("LINEAR_ALGEBRA_CHECK_EQUALITY RHS ",  str( rhs ) )
    #print("LINEAR_ALGEBRA_CHECK_EQUALITY SAMPLE_VARIABLES",  sample_variables)
    try:
        baseunits = {meter: 1, second: 1, kg: 1, ampere: 1, kelvin: 1, mole: 1, candela: 1}
        dprint("DO SAMPLE")
        miss = 0
        nsamples = 5
        if not 'sample' in str( rhs ) :
            nsamples = 1
        for k in range(0,nsamples) :
            kseed  = k
            #print("NSAMPLES = ", nsamples, "K = ", k )
            baseunits =  [('meter', 1), ('second', 1), ('kg', 1), ('ampere', 1), ('kelvin', 1), ('mole', 1), ('candela', 1)] 
            #print("LHS W BASEUNITS", sympy.sympify(lhs) )
            sympy_wo_units1 = sympy.sympify(lhs).subs(baseunits)
            sympy_wo_units2 = sympy.sympify(rhs).subs(baseunits)
            pair = (sympy_wo_units1, sympy_wo_units2)
            try :
                pair =  sympy.lambdify( [], pair , modules=sample_module,)()
            except: 
                miss = miss + 1
            (sympy_wo_units1, sympy_wo_units2) = pair
            #print("SYMPY1 = ", sympy_wo_units1)
            #sympy_wo_units1 = sympy.lambdify( [], sympy_wo_units1  , modules=sample_module,)()
            #print("SYMPY1 = ", sympy_wo_units1)
            #sympy_wo_units2 = sympy.sympify(rhs).subs(baseunits)
            #print("SYMPY2 = ", sympy_wo_units2)
            #sympy_wo_units2 = sympy.lambdify( [], sympy_wo_units2  , modules=sample_module,)()
            #print("SYMPY2 = ", sympy_wo_units2 )
            diff = numpy.absolute( ( sympy_wo_units1 - sympy_wo_units2 ) )
            #print("DIFF = ", diff )
            try: 
                if numpy.any( numpy.abs( diff ) > precision ) :
                    miss = miss + 1 
            except:
                miss = miss + 1
        response['debug'] = " Sampling: %s of %s ok" % ( str( nsamples - miss), str(nsamples) )
        if miss < nsamples * 0.3 :
            response['correct'] = True
            check_units = False
        else :
            response['correct'] = False
                
        if check_units:
            try:
                s1 = sympy.sympify( replace_sample_funcs( str(lhs) ) )
                s2 = sympy.sympify( replace_sample_funcs( str(rhs) ) )
                dprint("S1 = ", s1 )
                dprint("S2 = ", s2 )
                resp = check_units_new( s1,s2, sample_variables)
                dprint("returned from check_units_new", resp )
                inner = inner + 'B'
            except LinearAlgebraUnitError as e:
                dprint("FAILED LinearAlgberUnit Error", str(e) )
                response['warning'] = ' ' + str(e) + ' ' 
            except Exception as e:
                dprint("FAILED CHECK_UNITS_NEW", type(e), str(e) )

    except ShapeError as e :
        response['error'] = _("Illegal matrix operation in %s" % lhsorig)
    except SympifyError as e:
        inner = ''
        logger.error([str(e), str(lhs), str(rhs)])
        response['error'] = _("Error 533 Failed to evaluate expression. %s " + inner % lhsorig)
    except AttributeError as e:
        parts = str(e).split('attribute')
        response['error'] = str(parts[1]) + ' is undefined  ( Error 347 ) inner = ' + inner
        response['debug'] = str( e ) + inner
        #print("RESPONSE = ", response )
    except NameError as e:
        #print("ERROR 3 ", inner , str(e))
        response['error'] = "(Error 483: ) " + str(e)
    except Exception as e:
        #print("error caught = ", str(e) )
        inner = ''
        logger.error([str(e), str(lhs), str(rhs)])
        logger.error(traceback.format_exc())
        response['error'] = _("Unknown error 533 comparing  [%s , %s] check your expression." + inner % ( str(lhs), str(rhs) ) )
        print("UNCAUGHT ERROR 533 FOUND AND PRINT", response['error'] )
    #print("DELTA T2  = ", 1000 * ( time.time() - time_start ) );
    #print("RESPONSE = ", response )
    dprint("TIME IN CHECK_EQUALTITY ", 1000 * ( time.time() - tbeg) )
    return response  # }}}


def linear_algebra_expression_runner(
    precision,
    variables,
    expression1,
    expression2,
    check_units,
    blacklist,
    used_variables,
    funcsubs,
    result_queue,
):
    response = linear_algebra_compare_expressions(
        precision,
        variables,
        expression1,
        expression2,
        check_units,
        blacklist,
        used_variables,
        funcsubs,
    )
    result_queue.put(response)


def linear_algebra_expression(
    precision,
    variables,
    student_answer,
    correct_answer,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs={},
):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_', '#', '@', '&', '?', '"']
    for i in invalid_strings:
        if i in student_answer:
            return {'error': _('Answer contains invalid character ') + i}
    #print(compare_numeric_internal(variables, expression1, expression2))
    return safe_run(
        linear_algebra_expression_runner,
        args=(
            precision,
            variables,
            student_answer,
            correct_answer,
            check_units,
            blacklist,
            variables,
            funcsubs,
        ),
    )


def linear_algebra_expression_blocking(
    precision,
    variables,
    student_answer,
    correct_answer,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs={},
):
    """
    Starts a process with compare_numeric_internal that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    return linear_algebra_compare_expressions(
        precision,
        variables,
        student_answer,
        correct_answer,
        check_units,
        blacklist,
        used_variables,
        funcsubs,
    )
