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
from .mathematica import mathematica_form
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
from .parsehints import parsehints
from .functions import *
from .checks import check_for_legal_answer, lambdifymodules, LinearAlgebraUnitError, check_units_new, mysqrt, check_answer_structure, check_consistency, check_for_undefined_variables_and_functions
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

def dprint(*args) :
    return



def question_check(question_json, question_xmltree, answer_data, global_xmltree, symex):
    hints = parsehints(question_xmltree, global_xmltree, answer_data)
    result = {}
    if hints is not None:
        if hints.get('correct', None) is not None:
            return hints
    check_units = True
    ret = getallvariables(global_xmltree, question_xmltree, assign_all_numerical=False)
    used_variables = list(ret['used_variables'])
    variables = ret['variables']
    funcsubs = ret['functions']
    authorvariables = ret['authorvariables']
    exposeglobals = (question_json.get('@attr').get('exposeglobals', 'false')).lower() == 'true'
    #if exposeglobals :
    #    okvariables = set( [item['name'] for item in authorvariables] + used_variables   )
    #else :
    #    okvariables = set(  used_variables   )
    blacklist = ret['blacklist']
    #okvariables = okvariables.difference( set( blacklist) )
    correct_answer = ret['correct_answer']
    equality = question_xmltree.find('equality')
    negate = False
    if equality is not None:
        correct_answer = equality.text
    istrue = question_xmltree.find('istrue')
    if istrue is not None:
        correct_answer = istrue.text
        if '==' not in istrue.text:
            correct_answer = istrue.text + "== 1 "
        check_units = False

    isfalse = question_xmltree.find('isfalse')
    if isfalse is not None:
        negate = True
        correct_answer = isfalse.text
        if '==' not in isfalse.text:
            correct_answer = isfalse.text + "== 1 "
        check_units = False
    precision = question_json.get('@attr').get('precision', '1e-6')
    precision = float(precision)
    # SYMEX CALLS LINEAR_ALGEBRA_EXPRESSION
    result = symex(
        precision,
        authorvariables,
        answer_data,
        correct_answer,
        check_units=check_units,
        blacklist=list(blacklist),
        used_variables=used_variables,
        funcsubs=funcsubs,
    )
    if negate:
        if 'correct' in list(result.keys()):
            if result['correct']:
                result['status'] = 'incorrect'
            else:
                result['status'] = 'correct'
            # result['status'] = 'incorrect' if result['correct'] else 'correct'
        elif 'error' in list(result.keys()):
            result['status'] = 'error'
    else:
        if 'correct' in list(result.keys()):
            if result['correct']:
                result['status'] = 'correct'
            else:
                result['status'] = 'incorrect'
        # result['status'] = 'incorrect' if result['correct'] else 'correct'
        # if 'correct' in result.keys() :
        #    result['status'] = 'correct' if result['correct'] else 'incorrect'
        elif 'error' in list(result.keys()):
            result['status'] = 'error'
    # if hints is not None:
    #    result.update(hints)
    #okvariables = [ reg.sub(r"variable",'',item) for item in list( okvariables) ] 
    #result['used_variable_list'] = list( set( okvariables ) )
    result['used_variable_list'] = used_variables
    return result

    

def linear_algebra_compare_expressions(
    precision,
    variables,
    student_answer,
    correct,
    check_units=True,
    blacklist=[],
    used_variables=[],
    funcsubs=[],
    validate_definitions=False,
    ):
    tbeg = time.time()
    _ , varsubs_sympify, sample_variables = parse_sample_variables(variables)
    compare_hash = get_hash_from_string( " %s %s %s %s %s %s %s %s %s " % ( str(precision), str(variables), str(student_answer), 
            str(correct), str(check_units), str(used_variables), str(blacklist), str(funcsubs)   , __file__ ) )
    ret = djangocache.cache.get(compare_hash)
    if not ret == None  and not validate_definitions:
            return ret
    if not validate_definitions and not settings.RUNTESTS :
        response = check_for_undefined_variables_and_functions( student_answer, used_variables ) 
        if response :
            return response
    student_answer = declash( student_answer)
    correct = declash( correct )
    try:
        (student_answer, correct ,varsubs_sympify ) = equality_remap( student_answer, correct ,varsubs_sympify)
    except:
        response = {'error' : "Equality syntax incorrect in student expression [%s] " % student_answer_unparsed }
        return response
    student_answer = insert_implicit_multiply( student_answer)
    correct_answer = insert_implicit_multiply( correct )
    student_answer_orig = student_answer
    time_start = time.time()
    precheck = check_for_legal_answer( precision, variables, student_answer, correct, check_units, blacklist)
    if precheck is not None:
        return precheck
    response = check_answer_structure( student_answer, correct, varsubs_sympify ) 
    if response :
        return response
    # FINALLY IF THE STUDENT RESPONSE STRING DOES NOT HAVE OBVIOUS ERRORS TRY SYMPIFY 
    try :
        prelhs = sympify_with_custom( student_answer , varsubs_sympify, {}, 'linear_algebra_compare_expressions-2' )
        lhs = prelhs.doit()
        prerhs = sympify_with_custom( correct, varsubs_sympify, {}, 'linear_algebra_compare_expressions-3' )
        rhs = prerhs.doit()
    except Exception as e:
        if '@' in str(e):
            explanation = "The character @ appears in author expression; check for macros with missing semicolon separator or missing :=  in macro definition"
        else:
            explanation = ""
        response = dict(error=_("ERROR IN AUTHOR EXPRESSION. " + explanation),
                        warning=("%s %s %s" % ( type(e), str(e), traceback.format_exc() )) )
        return response
    ret = linear_algebra_check_equality( precision, lhs, rhs, sample_variables, check_units=check_units,blacklist=blacklist)
    try:
        ret['mathematica'] = "Math Expression: {%s , %s }" % (  mathematica_form(student_answer), mathematica_form( correct_answer) )
    except:
        ret['mathematica' ] = "Cannot parse mathematica: [%s,%s]" % ( student_answer, correct_answer)
    djangocache.cache.set(compare_hash, ret , 600 )
    return ret




local_defs = {
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
    }

sample_defs = dict( local_defs)
sample_defs.update( {'sample' : lambda *x: dorand(x) } )
sample_module = [
    sample_defs,
    "numpy",
]


base_module = [
    local_defs,
    "numpy",
]







def dorand(x) :
    global kseed
    s = 0
    #print(" DORAND rr = ", rr )
    random.seed(kseed)
    for value in x :
        s = s + value  * ( 0.5  + random.random() ) + 0.1 * random.random() 
    return s


sample_project= [
    {
    'sample' : lambda *x: x[0] ,
    }, 
    "sympy"
]


kseed = 5



def linear_algebra_check_equality(precision, lhs, rhs, sample_variables, check_units=True,blacklist=None):  # {{{
    global kseed
    #if blacklist :
    response = check_consistency( lhs, rhs ,blacklist) 
    if response :
       return response
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
        #baseunits = {meter: 1, second: 1, kg: 1, ampere: 1, kelvin: 1, mole: 1, candela: 1}
        dprint("DO SAMPLE")
        miss = 0
        nsamples = 5
        if not 'sample' in str( rhs ) :
            nsamples = 1
        for k in range(0,nsamples) :
            kseed  = k
            #print("NSAMPLES = ", nsamples, "K = ", k )
            baseunits =  [('meter', random.random()), ('second', random.random()), ('kg', random.random()), ('ampere', random.random()), ('kelvin', random.random()), ('mole', random.random()), ('candela', random.random())] 
            #print("LHS W BASEUNITS", sympy.sympify(lhs) )
            sympy_wo_units1 = sympy.sympify(lhs).subs(baseunits)
            sympy_wo_units2 = sympy.sympify(rhs).subs(baseunits)
            pair = (sympy_wo_units1, sympy_wo_units2)
            try :
                pair =  sympy.lambdify( [], pair , modules=sample_module,)()
            except: 
                miss = miss + 1
            (sympy_wo_units1, sympy_wo_units2) = pair
            diff = numpy.absolute( ( sympy_wo_units1 - sympy_wo_units2 ) )
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
    return safe_run(
        linear_algebra_expression_runner,
        args=(
            precision,
            variables,
            student_answer,
            correct_answer,
            check_units,
            blacklist,
            used_variables,
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
