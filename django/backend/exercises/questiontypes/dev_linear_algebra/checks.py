from sympy import *

# from sympy.abc import _clash1, _clash2, _clash
from sympy.core.sympify import SympifyError
from django.utils.translation import ugettext as _
import traceback
import random
import re as reg
import itertools
from sympy.core import S
from .unithelpers import units, sympy_units, baseunits
from .sympify_with_custom import sympify_with_custom
from exercises.util import index_of_matching_left_paren, index_of_matching_right_paren


from .variableparser import getallvariables, get_used_variable_list
from exercises.questiontypes.safe_run import safe_run
import logging
import traceback
from .string_formatting import (
    absify,
    insert_implicit_multiply,
    ascii_to_sympy,
    matrixify,
    braketify,
    declash,
    replace_sample_funcs
)
from .unithelpers import *
from .parsers import *
from .functions import *
from numpy import tan, logical_or, equal, cross,dot,inf,complex
import numpy.linalg

def mysqrt(x) :
    x = x + numpy.complex(0,0)
    if  numpy.isscalar(x) :
        return numpy.sqrt(x )
    else :
        #print("Trying to take sqrt( %s ) type= %s " % ( str(x), type(x)  ) )
        return 0
        #raise ValueError("Trying to take sqrt( %s ) type= %s " % ( str(x), type(x)  ) )


lambdifymodules = [
    {
        'cot': lambda x: 1.0 / numpy.tan(x),
        'exp': lambda x:  numpy.exp(x),
        'sqrt': lambda x: mysqrt(x),
        'real': lambda x: numpy.real(x),
        'norm': lambda x: numpy.linalg.norm(x),
        'logicaland': numpy.logical_and,
        'logicalor': numpy.logical_or,
        'eq': numpy.equal,
        'Norm': lambda x:  numpy.linalg.norm(x) ,
        'abs':  lambda x:  numpy.linalg.norm(x) ,
        'cross': lambda x, y: numpy.cross(x, y, axis=0),
        'crossfunc': lambda x, y: numpy.cross(x, y, axis=0),
        'dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
        'Dot': lambda x, y: numpy.dot(numpy.transpose(x), y),
        'zoo': numpy.inf,
        'I': numpy.complex(0, 1),
    },
    "numpy",
]

import re


class LinearAlgebraUnitError(Exception):
    """
    Can be raised from check_units_new
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


def dprint(*args) :
    return

def check_units_new(expression, correct, sample_variables):
    nvarsubs = {}
    nsubs_values = []

    def perturb(value):
        return value + value * random.random() * 0.1

    #print("a")
    for item in sample_variables:
        #print("b")
        nvarsubs[item['symbol']] = item['symbol'] * item['around'][0]
        value = float(item['around'][0].subs(baseunits))
        sampled_value = value + random.random() * value * 0.1
        nsubs_values.append((item['symbol'], sampled_value))
    #print("c")
    nexpression = expression.subs(nvarsubs).doit()
    #print("NEXPRESSION = ", nexpression)
    #print("d")
    ncorrect = correct.subs(nvarsubs).doit()
    #print("e")

    checks = [
        [1, 1, 1, 1, 1, 1, 1],
        [perturb(2), 1, 1, 1, 1, 1, 1],
        [1, perturb(2), 1, 1, 1, 1, 1],
        [1, 1, perturb(2), 1, 1, 1, 1],
        [1, 1, 1, perturb(2), 1, 1, 1],
        [1, 1, 1, 1, perturb(2), 1, 1],
        [1, 1, 1, 1, 1, perturb(2), 1],
        [1, 1, 1, 1, 1, 1, perturb(2)],
    ]
    results = []
    for check in checks:
        #print("f")
        unit_values = list(map(lambda item: (item[1], item[0]), zip(check, sympy_units)))
        #print("1")
        allvalues = nsubs_values + unit_values
        #print("x")
        #print( nexpression.subs(allvalues) )
        #print("X")
        #print(" lambdifymodules= ",  lambdifymodules)
        #print(" allvalues = ",  allvalues )
        #print("Y")
        #try :
        tres = ( sympy.lambdify([], nexpression.subs(allvalues), modules=lambdifymodules)() )
        #except Exception as e :
        #    #print(traceback.format_exception(None, # <- type(e) by docs, but ignored 
        #                             e, e.__traceback__), file=sys.stderr, flush=True)
        #print("Z")
        #print("NEXPRESSION BEF = ", srepr( nexpression) )
        nexpression = sympy.sympify( str( nexpression)  ) # THIS MUST BE A BUG IN SYMPY THIS EXPRESSION SHOULD BE A NOOP
        #print("NEXPRESSION NOW = ", srepr( nexpression) )
        #print("nexpression = ", nexpression)
        allval =  [('meter', 1), ('second', 1), ('kg', 1), ('ampere', 1), ('kelvin', 1), ('mole', 1), ('candela', 1)]
        further =  nexpression.subs(allval) 
        #further = sympy.lambdify([], further.subs(allvalues), modules=lambdifymodules)() 
        #print("NEXPRESSION FURTHER ",  further)
        vale = numpy.linalg.norm(
            sympy.lambdify([], nexpression.subs(allvalues).doit(), modules=lambdifymodules)()
        )
        #print("3 vale = ", vale )
        ncorrect = sympy.sympify( str( ncorrect) )
        valc = numpy.linalg.norm(
            sympy.lambdify([], ncorrect.subs(allvalues).doit(), modules=lambdifymodules)()
        )
        #print("4 valc" , valc)
        if valc != 0:
            results.append(vale / valc)
        else:
            results.append(vale)
    #print("g")
    for res in results:
        if numpy.absolute(res - results[0]) > 10e-5:
            #print("g")
            raise LinearAlgebraUnitError(_("Incorrect units"))

def parens_are_balanced(expression):
    level = 1
    ind = 0
    while level > 0 and ind < len(expression):
        if expression[ind] == ')':
            level = level - 1
        elif expression[ind] == '(':
            level = level + 1
        ind = ind + 1
    return ( level == 1 ) and ( ind == len(expression) )



def check_for_legal_answer(
    precision, variables, student_answer, expression, check_units=True, blacklist=[], extra_tokens=[]
):
    response = {}
    #### INVALID STRINGS 
    invalid_strings = ['_', '#', '@', '&', '?', '"',':','..',';']
    for i in invalid_strings:
        if i in student_answer:
            return {'error': _('Answer contains invalid character ') + i}


    illegal = reg.findall(r'(\^|\.)([0-9]+[a-zA-Z]+)(\^|\.)', student_answer)
    if len(illegal) >  0 :
        s = ",".join( [ "".join(item) for item in illegal])
        return dict(error= _('Illegal pattern %s in %s ' % (s, student_answer)  ) ) 
 
    ##### INVALID PATTERNS 
    invalid_patterns= { "\)[\w]" : 'implicit multiply needs a space; right parenthesis cannot be followed by letter or number',
                        #"[0-9\.]+\(" : 'implicit multiply with a number needs a space' ,
                        "[^=]=[^=]"  : 'equal sign is illegal',
                        "(\^|\s|\(|\+|\/|\*|-)[0-9\.]+[A-Za-z]" : 'illegal implicit multiply',
                        "(^|\s|\+|-|\*|\/)[0-9]+[A-Za-z]+" : 'illegal implicit multiply with a number',
                        "\^\s" : 'exponential cannot be followed by space',
                        "\s\^" : 'exponential cannot be preceded by space',
                        }

    for i in invalid_patterns.keys() :
        if not None == re.search(r'%s' % i  , student_answer)  :
            return {'error': _('%s' %  invalid_patterns[i] ) }

    ########## UNBALANCED PARENS
    if not parens_are_balanced(student_answer) :
        return {'error' : _("Unbalanced parenthesis") }

    #print("VARIABLES1 = ", variables)
    variables = [ replace_sample_funcs( item) for item in variables ]
    #print("VARIABLES2 = ", variables)
    student_answer = replace_sample_funcs(declash( student_answer) )
    #print("STUDENT ANSWER CHECK", student_answer, flush=True)
 
    ######### CHECK THAT VARIABLES ARE NOT USED AS FUNCTIONS ######
    for variable in variables:
        if re.search(r'(^|\W)%s\(' % variable['name'] , student_answer):
            # MAKE EXCEPTION FOR FUNCTION
            if not '(' in variable['value'] :
                return dict(error='Variable %s cannot be used as a function; check implicit multiply.' % variable['name'])


    ###########  MAKE SURE NO BLACKLISTED VARIABLES ARE USED
    studentatoms = get_used_variable_list(student_answer)
    okatoms = [ item['name'] for item in variables ] + ['kg','meter','second']
    #print("okatoms = ", okatoms )
    #print("STUDENTATOMS = ", studentatoms)
    for atom in studentatoms:
        strrep = str(atom)
        # funcstr = str(atom.func)
        if strrep in blacklist or ( strrep not in okatoms ) :
            if strrep not in extra_tokens:
                return {'error': _('(A) Forbidden token: ') + reg.sub(r'variable','',strrep) }

    unparsedstudentanswer = student_answer
    #student_answer = insert_implicit_multiply( student_answer )
    #student_answer = declash(student_answer)


    expression = replace_sample_funcs(expression)
    if '==' in expression and not '$$' in expression:
        if not '==' in student_answer:
            return {'error': _('answer in terms of an equality using == ')}
    if '==' in student_answer:
        if not '==' in expression or '$$' in expression:
            return {'error': _('an equality is not permitted as answer')}
        #else:
        #    equality = student_answer.split('==')
        #    student_answer = equality[0] + '-' + equality[1]


    #varsubs, varsubs_sympify, sample_variables = parse_sample_variables(variables)
    m = re.search(r'(atan|arctan|acos|arccos|acos|arcos|asin|arcsin)', student_answer)
    if m:
        return {'error': _('inverse trig function') + m.group(1) + _(' is forbidden')}
    m = re.search(r'(print|sum)', student_answer)
    if m:
        return {'error': _('forbidden function') + m.group(1)}
    return None



def check_answer_structure( student_answer, correct , varsubs_sympify):
    response = None
    prelhs = None
    tbeg = time.time()
    try:
       # REPLACE SAMPLES WITH SINGLE SHOT TO CHECK STRUCTURE OF ANSWER
       tstudent_answer = replace_sample_funcs( student_answer)
       #print("      TSTUDENTANSWER = ", tstudent_answer)
       #print("      TYPE VARSUBS_SUMPFIY = ", type( varsubs_sympify) )
       tvarsubs_sympify = {}
       for key in varsubs_sympify.keys() :
            #print("     KEY = ", key )
            tvarsubs_sympify[key] = sympy.sympify( replace_sample_funcs( str( varsubs_sympify[key]  ) ) )
       #dprint("      TVARSUBS_SYMPIFY = ", tvarsubs_sympify)
       prelhs = sympify_with_custom( tstudent_answer, tvarsubs_sympify, {}, 'check-answer-structure-linear_algebra_compare_expressions')

    except AttributeError as e:
        if 'uple' in str(e) :
            response = dict(
                error = _( 'use square brackets for vectors and matrices')
                )
        else :
            response = dict(
                error=_( 'Attribute error 279' ),
                debug="Error 279: " +  str(e) + traceback.format_exc()
                )

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
    except ValueError as e:
        illegalchars = ['$','%']
        explain = ''
        msg = str(e)
        illegalpresent = list( filter( lambda x: x in student_answer, illegalchars) )
        if "mismatched" in str(e) :
            msg = ''
            explain = 'Probably missing mul(A,B) in matrix x matrix or matrix x vector'
        elif "EOL" in str(e) :
            msg = ''
            explain = 'Probably a quote character in the expression'
        
        elif len( illegalpresent ) > 0 :
            msg = ''
            explain = 'illegal character: ' + ','.join( illegalpresent)
            
        response = dict(
            error=_("%s \n %s %s" % ("Error 158", explain,  msg ) )
                )
    except Exception as e:
        response = dict(
            error=_(
                str( type(e)  )
                + " Error 213: Unidentified Error\n "
                + str(student_answer)
                + "\n"
                 + str(e) ),
            warning=_("%s %s %s" % ( type(e), str(e), traceback.format_exc() ))  
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
            "error": _("Error 182 incorrect dimensions")
            + ": your expression %s is a matrix or vector; a scalar answer is required." % str( lhs )
        }
    if hasattr(rhs, 'shape') and not hasattr(lhs, 'shape') and ( not lhs == 0 ) :
        return {
            "error": _("Error 188 incorrect dimensions")
            + ": your expression %s is is not a proper  vector or matrix " % str(lhs) 
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



    
def check_for_undefined_variables_and_functions( student_answer, used_variables ):
    response = []
    student_answer_unparsed = student_answer
    studentatoms = get_used_variable_list(student_answer)
    okatoms =  used_variables + ['kg','meter','second']
    diff = list( set(studentatoms).difference( set( okatoms) ) )
    if len( diff) > 0  :
           #print( " DIFF = ", diff, "LEN ", len(diff) )
           return {'error': "(H) Forbidden token: %s " % ",".join( diff)    ,
                   'correct': False }
    okatoms =  used_variables + ['kg','meter','second']
    funcs = reg.findall(r'([A-Za-z][A-Za-z0-9]*)\(', student_answer_unparsed)  
    badfuncs = list( filter( lambda fname : not hasattr(sympy, fname) , funcs) )
    if len( badfuncs ) > 0 :
        opentafuncs = list( openta_scope.keys() )  + ['sample']
        badfuncs = list( set( badfuncs).difference( set( opentafuncs) )  )
        if len( badfuncs)  > 0  :
            response = {'error': "(H) Forbidden function : %s " % ",".join( badfuncs)    , 'correct': False }
            #print("RESPONSE TO BADFUNCS = ", response)
            return response
    return [] 

