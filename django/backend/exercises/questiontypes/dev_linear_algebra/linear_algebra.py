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

from exercises.questiontypes.safe_run import safe_run
import logging
import traceback
from .string_formatting import (
    absify,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
    paren_check
)
from .string_formatting import insert_implicit_multiply 
from .unithelpers import *
from sympy import DiagonalOf
from .functions import *
from .checks import check_for_legal_answer, lambdifymodules, LinearAlgebraUnitError, check_units_new
import numpy
from .parsers import *
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
    student_answer = insert_implicit_multiply( student_answer)
    correct_answer = insert_implicit_multiply( correct )
    compare_hash = get_hash_from_string( " %s %s %s %s %s %s %s %s %s " % ( str(precision), str(variables), str(student_answer), 
            str(correct_answer), str(check_units), str(used_variables), str(blacklist), str(funcsubs)   , __file__ ) )
    ret = djangocache.cache.get(compare_hash)
    student_answer_orig = student_answer
    time_start = time.time()
    try:
        #print("A")
        precheck = check_for_legal_answer( precision, variables, student_answer, correct, check_units, blacklist)
        #print("B")
        if precheck is not None:
            return precheck
        varsubs, varsubs_sympify, sample_variables = parse_sample_variables(variables)
        equality = correct.split('==')
        if len(equality) > 1 and '$$' in correct:
            correct = equality[1]
            student_answer = (equality[0]).replace('$$', '(' + student_answer + ')')
        if '==' in student_answer:
            equality = correct.split('==')
            if len(equality) != 2:
                return {'error': 'Response is not an equality'}
            correct = 'Abs( (' + equality[0] + ') - ( ' + equality[1] + '))'
            correct = '0'
            equality = student_answer.split('==')
            student_answer = 'Abs( (' + equality[0] + ') - ( ' + equality[1] + '))'
        zero = '(' +  student_answer + ') -  (' +  correct + ')' 
        allvariables = get_used_variable_list( zero )
        #print("C")
        try:
           prelhs = sympify_with_custom(
                student_answer, varsubs_sympify, {}, 'linear_algebra_compare_expressions'
           )
        except TypeError as e:
            if 'required positional' in str(e) :
                response = dict(
                    error = _( 'function is missing an argument')
                    )
            else:
                response = dict(
                    error=_( 'syntax error' ),
                    debug="Error 187: " +  str(e)
                    )
            return response
        
        except NameError as e:
            response = dict(
                    error=_( str(e) ),
                    debug="Error 193: " +  str(e)
                    )
            return response
        
        except ShapeError as e:
            response = dict(
                    error=_("Matrix dimensions inconsistent with each other or with the result. You must mul(A,B) for multiplying a matrix or matrix times vector"),
                    debug="Error 202: " +  str(e)
                    )
            return response
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
            return response
        
        try :
            #print("PRELHS = ", prelhs )
            lhs = prelhs.doit().subs(varsubs).subs(varsubs).subs(varsubs).doit()
            #print("A1")
            #print("CORRECT = ", correct )
            prerhs = sympify_with_custom( correct, varsubs_sympify, {}, 'linear_algebra_compare_expressions' )
            #print("A2")
            varhash = get_hash_from_string('rhs' + str( prerhs) + str( varsubs) )
            #print("A3")
            rhs = None 
            if  settings.DO_CACHE :
                rhs = djangocache.cache.get(varhash)
            #print("A4")
            if rhs is None :
                #print("prerhs = ", prerhs)
                #print("varsubs = ", varsubs)
                #print("prerhs =  line 232 ", prerhs )
                rhs = prerhs.subs(varsubs).doit()
                #print("RHS =  line 234 ", rhs )
                #print("VARHASH = ", varhash )
                try:
                    djangocache.cache.set(varhash, rhs , 30 )
                except Exception as e:
                    djangocache.cache.set(varhash, None, 30 )
                    #print(" CACHE EXCEPTION ", type(e), str(e) )
            #print("A5")
            #print("POSITION 3.7", 1000 * ( time.time() - time_start ) );
        except Exception as e:
            if '@' in str(e):
                explanation = "The character @ appears in author expression; check for macros with missing semicolon separator or missing :=  in macro definition"
            else:
                explanation = ""
            response = dict(error=_("ERROR IN AUTHOR EXPRESSION. " + explanation),
                            warning=("%s %s %s" % ( type(e), str(e), traceback.format_exc() )) )
            return response
        #print("POSITION 4", 1000 * ( time.time() - time_start ) );
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
        if isinstance(prelhs, sympy.Basic) or isinstance(prelhs, sympy.MatrixBase):
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
                if special[0] in blacklist and (special[0] in str(student_answer)):
                    return {"error": _("(E) Forbidden token: ") + special[0]}
            atoms = prelhs.atoms(sympy.Symbol, sympy.MatrixSymbol, sympy.Function)
            for atom in atoms:
                strrep = str(atom)
                funcstr = str(atom.func)
                if strrep in blacklist:
                    return {"error": _("(F) Forbidden token: ") + strrep}
                if funcstr in blacklist:
                    return {"error": _("(G) Forbidden token: ") + funcstr}
            #print("POSITION 5", 1000 * ( time.time() - time_start ) );
        
    except SympifyError as e:
        logger.error(traceback.format_exc())
        logger.error([str(e), str(student_answer), str(correct)])
        response = dict(error=_("Failed to evaluate expression."))
        return response
    except ShapeError as e:
        logger.error(traceback.format_exc())
        response = dict(
            error=_("There seems to be a vector or matrix operation with incompatible dimensions.")
        )
        return response
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error([str(e), str(student_answer_orig), str(correct)])
        response = dict(error=_("Unknown error, check your expression."))
        return response

    #print("BEFORE CHECK_EQUALTITY", 1000 * ( time.time() - time_start ) );
    #print("LHS = ", lhs )
    #print("RHS = ", rhs)
    #print("RHS = ", sample_variables)
    ret = linear_algebra_check_equality( precision, lhs, rhs, sample_variables, check_units=check_units)
    #print("POSITION6")
    try:
        ret['mathematica'] = "Math Expression: {%s , %s }" % (  mathematica_form(student_answer), mathematica_form( correct_answer) )
    except:
        ret['mathematica' ] = "Cannot parse mathematica: [%s,%s]" % ( student_answer, correct_answer)
    #ret['mathematica'] =  str( mathematica_form(correct_answer)  )
    #print("RET = ", ret )
    #time_beg = time.time()
    #with WolframLanguageSession() as wl_session:
    #    res = wl_session.evaluate(wlexpr( mathematica_form( student_answer ) ) )
    #print("RES = ", res )
    #print("TIME = ", ( time.time() - time_beg ) * 1000 )
    djangocache.cache.set(compare_hash, ret , 600 )
    return ret



def linear_algebra_check_equality(precision, lhs, rhs, sample_variables, check_units=True):  # {{{
    #print("CHECK EQUALITY ", lhs, rhs )
    if rhs == 0 :
        rhs = 0 * lhs
        #print("RHS = 0", rhs )
    if lhs == 0 :
        lhs = 0 * rhs
        #print("LHS == 0 ", lhs )
    number_of_points = 5
    response = {}
    # response['ABC'] = 'ABC';
    time_start = time.time()
    #print("LHS, RHS = ", lhs, rhs )
    inner = 'BEGIN: '
    try:
        random.seed(1)
        sympy1_units = lhs
        sympy2_units = rhs
        sympy1 = sympy1_units.subs(baseunits)
        sympy2 = sympy2_units.subs(baseunits)
        #print("SYMPY1,2 = ", sympy1, sympy2)
        subs_neighbours = []
        inner = inner + 'a'
        for i in range(0, number_of_points):
            subs_neighbour = []
            for var in sample_variables:
                sample_point_values = []
                for sample_point in var['around']:
                    var_value = float(sample_point.subs(baseunits))
                    sample_point_values.append(
                        (var['symbol'], var_value + random.random() * var_value * 0.1 + 0j)
                    )
                subs_neighbour.append(sample_point_values)
            for combination in itertools.product(*subs_neighbour):
                subs_neighbours.append(combination)
                # if log
                #    varvals = list(map(lambda x: str(x[0]) + ':' + str(x[1]), combination))
                #    logger.debug('Neighbour point: ' + str(varvals))

        one_point = list(
            map(lambda item: (item['symbol'], item['around'][0].subs(baseunits)), sample_variables)
        )
        undefined_variables = sympy1.subs(one_point).free_symbols - set(
            [kg, second, meter, ampere, kelvin, mole, candela, sympy.I, sympy.E]
        )
        inner = inner + 'g'
        if len(undefined_variables) > 0:
            unrecognised = ', '.join(list(map(str, undefined_variables)))
            response['error'] = unrecognised + _(' are not valid variables.')
            return response
        eval_point = subs_neighbours[0] if subs_neighbours else []
        inner = inner + 'h'
        if len(subs_neighbours) <= 1:
            inside = sympy1.subs(eval_point).doit() - sympy2.subs(eval_point).doit()
            #print("INSIDE = ", inside )
            test_evaluation = numpy.linalg.norm(
                sympy.lambdify(
                    [],
                    (sympy1.subs(eval_point).doit() - sympy2.subs(eval_point).doit()),
                    modules=lambdifymodules,
                )()
            )
            if numpy.absolute(test_evaluation) < precision:
                response['correct'] = True
            else:
                response['correct'] = False
                # response['warning'] = "NO SAMPLING"
            return response
        #print("DELTA T = ", 1000 * ( time.time() - time_start ) );
        time_start = time.time()
        #print("SYMPYT1 again is ", sympy1 )
        #print("SYMPYT2 again is ", sympy1 )
        
        inner = inner + "i"
        #print("sympy2 = ", sympy2)
        nsympy2 = sympy.lambdify([], sympy2, modules=lambdifymodules)()
        inner = inner + "j"
        #print("sympy1 = ", sympy1)
        try :
            nsympy1 = sympy.lambdify([], sympy1, modules=lambdifymodules)()
        except :
            pass
        inner = inner + "k"
        #nsympy1 = sympy1.subs(eval_point).doit()
        #nsympy2 = sympy2.subs(eval_point).doit()
        #print( "LAMBDIFY = ", sympy.lambdify([], nsympy2, modules=lambdifymodules)()) 
        #print("nsympy1 = ", nsympy1)
        #print("nsympy2 = ", nsympy2)
        try: 
            #nnsympy2 = numpy.linalg.norm(sympy.lambdify([], nsympy2, modules=lambdifymodules)())
            #nnsympy1 = numpy.linalg.norm(sympy.lambdify([], nsympy1, modules=lambdifymodules)())
            if check_units:
                if nsympy2 == 0 or abs( nsympy2 ) < 1e-12:
                    check_units = False
        except:
            check_units = False
            pass
        #print("A1 check-units = ", check_units)
        #test_evaluation = numpy.linalg.norm(
        #    sympy.lambdify([], nsympy1 - nsympy2, modules=lambdifymodules)()
        #)
        inner = inner + "A"
        if check_units:
            try:
                inner = inner + '+1'
                #print("call check_units_new")
                check_units_new(sympy1_units, sympy2_units, sample_variables)
                #print("returned from check_units_new")
                inner = inner + 'B'
            except LinearAlgebraUnitError as e:
                response['warning'] = ' ' + str(e) + ' ' 
                return response

        diffs = []
        inner = inner + 'h'
        #print("A2",inner)
        #vale = numpy.linalg.norm(
        #    sympy.lambdify([], nexpression.subs(allvalues).doit(), modules=lambdifymodules)()
        #)
        for sample_point in subs_neighbours:
            inner = inner + 'C'
            nsympy1 = sympy1.subs(sample_point).doit()
            nsympy2 = sympy2.subs(sample_point).doit()
            allval =  [('meter', 1), ('second', 1), ('kg', 1), ('ampere', 1), ('kelvin', 1), ('mole', 1), ('candela', 1)]
            inner = inner + 'D'
            inner = inner + 'E'
            nsympy1 = sympy.sympify( str( nsympy1  ) ).subs(allval)
            nsympy2 = sympy.sympify( str( nsympy2 )  ).subs(allval)
            #print("NSYMPY1 = ", nsympy1 ,inner)
            #print("NSYMPY2 = ", nsympy2 ,inner )
            #print("DIF1 = ",  sympy.lambdify( [], nsympy1.subs(allval), modules=lambdifymodules,)())
            #print("DIF2 = ",  sympy.lambdify( [], nsympy2.subs(allval) , modules=lambdifymodules,)())

            try:
                ndiff = abs(
                    sympy.lambdify(
                        [],
                        (nsympy1.subs(sample_point).doit() - nsympy2.subs(sample_point).doit()),
                        modules=lambdifymodules,
                    )()
                )
            except Exception as e:
                response['error'] = "Error 454: " + inner + ' '  + str(e) + 'NSYMPY1' + str(nsympy1) + 'NSYMPY2 ' + str( nsympy2) 
                response['correct'] = False
                return response
                break
            inner = inner + 'F'
            #print("TRY CORRECT")
            correct = numpy.all(ndiff < precision)
            #print("CORRECT = ", correct )
            inner = inner + 'G'
            diffs.append(correct)
            inner = inner + 'H'
        if diffs.count(True) >= len(subs_neighbours) * 0.9:
            #print("DIFFS =  ", diffs)
            response['correct'] = True
        else:
            inner = inner + 'J'
            response['debug'] = inner
            response['correct'] = False
    except SympifyError as e:
        inner = ''
        logger.error([str(e), str(lhs), str(rhs)])
        response['error'] = _("Failed to evaluate expression." + inner)
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
        response['error'] = _("Unknown error, check your expression." + inner)
    #print("DELTA T2  = ", 1000 * ( time.time() - time_start ) );
    #print("RESPONSE = ", response )
    time_start = time.time()
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
