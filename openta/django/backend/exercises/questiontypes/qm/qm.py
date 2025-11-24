# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

# from sympy.abc import _clash1, _clash2, _clash # dont impport clashes
import logging
import re as resub
import random
from lxml import etree
from exercises.questiontypes.basic import BasicQuestionOps
#from exercises.questiontypes.basic.basic import  scope # NEEDED WHEN PARSING EXPRESSIONS PASSED FROM BASIC
from .fockspace import FiniteBosonFockSpace;
from exercises.questiontypes.basic.basic import scope


try :
   from exercises.questiontypes.safe_run import safe_run
except:
    pass
try :
    from exercises.utils.unithelpers  import unitbaseunits;
except :
    unitbaseunits = {"meter": 1, "second": 1, "kg": 1, "ampere": 1, "kelvin": 1, "mole": 1, "candela": 1}
import sympy
from sympy import *
from sympy.core.sympify import SympifyError
from sympy.physics.quantum.operatorordering import normal_ordered_form 
from sympy.physics.quantum.boson import BosonOp, BosonFockKet, BosonFockBra ;
from sympy.physics.quantum import TensorProduct
from sympy.physics.quantum import Dagger, qapply 
from exercises.questiontypes.qm.fockspace import *
from exercises.questiontypes.qm.fockspace import FiniteBosonFockSpace
logger = logging.getLogger(__name__)



logger = logging.getLogger(__name__)


class com(sympy.Function):
    nargs = 2
    @classmethod
    def eval(cls, x, y ):
        return x*y - y*x

#def random_fraction():
#    return random.randint(4,20)/random.randint(4,20);


#
# Future-protect source by hiding connection to sympy.quantum
#
qmscope  = {
        "FiniteBosonFockSpace" : FiniteBosonFockSpace,
        "tp" : TensorProduct,   
        "qapply": qapply,
        "bket" : BosonFockKet,
        "bbra" : BosonFockBra,
        "boson" : BosonOp,
        "dboson" : lambda x: Dagger( BosonOp(x) ),
        "var" : Symbol,
        "dagger" : Dagger,
        "com": com,
        "op" : lambda x : Symbol(x, commutative=False),
        #"zeta": zeta,
        #"N": N,
        #"Q": Q,
        #"beta": beta,
        #"S": S,
        #"Matrix": sympy.Matrix,
        #"gamma": gamma,
        #"ff": Symbol("ff"),
        #"FF": Symbol("FF"),
    }
#ns = qmscope
#qmscope = ns;

class QuantumQuestionOps( BasicQuestionOps):

    scope = qmscope

    def __init__(self):
        super().__init__()
        self.name = "quantum_class";
        self.scope_update( qmscope) # IS ESSENTIAL

    #def scope_update(self, nss ) :
    #    super().scope_update(nss);
    #    return self.scope 

    #def validate_question(self, question_json, question_xmltree, global_xmltree):
    #    print(f"QM_VALIDATE_RUN")
    #    ret = super().validate_question( question_json, question_xmltree, global_xmltree)
    #    return ret



    #def compare_expressions(self, expression1, expression2,global_text_raw, preamble="" , precision_string="0", skip_syntax_check=False):
    #    print(f"COMPARE RUN")
    #    self.scope_update({'FiniteBosonFockSpace' : FiniteBosonFockSpace })
    #    ret = super().compare_expressions( expression1, expression2,global_text_raw, preamble="" , precision_string="0", skip_syntax_check=False)
    #    return ret


    def reduce_using_defs(self, expression, global_text, preamble, units , use_wedgerules=True ):
        sexpression = super().reduce_using_defs(expression,global_text, preamble, units, use_wedgerules, docache=False);
        ps = [ item.strip()  for item in global_text.split(";") ]
        fockspacedef =  [ i for i in ps  if "FiniteBosonFockSpace" in i ];
        if len( fockspacedef) >  0 :
            fockspacelabel = ( fockspacedef[0].split('=')[0] ).strip();
            if fockspacelabel in self.scope :
                f = self.scope[fockspacelabel]
            res = qapply(  sympify(sexpression, self.scope) ) 
            if  f :
                res = f.reduce_to_canonical(  res * f.bra() );
            return res
        return sexpression

    def add(self, *x):
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








lambdifymodules = ["numpy", {"cot": lambda x: 1.0 / numpy.tan(x)}]


#def asciiToSympy(expression):
#    return BasicQuestionOps.asciiToSympy(BasicQuestionOps,  expression)




def b(s) :
    return BosonOp(s);

def bd(s) :
    return Dagger( BosonOp( s) )





