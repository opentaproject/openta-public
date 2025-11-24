from sympy import *;
from sympy.core.sympify import SympifyError
from sympy.physics.quantum.operatorordering import normal_ordered_form 
from sympy.physics.quantum.boson import BosonOp, BosonFockKet, BosonFockBra ;
from sympy.physics.quantum import TensorProduct, IdentityOperator
from sympy import Symbol, expand, srepr;
from sympy.physics.quantum import Dagger, qapply ;
import logging;
logger = logging.getLogger(__name__)

def doapply(ex0) :
    ex1 = qapply( ex0, independent=True );
    while ( ex1 != ex0 ):
        ex0 = ex1;
        ex1 =  qapply( ex0 , independent=True);
    return ex1;

#def no(x):
#    xnew = normal_ordered_form( expand( qapply( x ) ), independent=True );
#    while not xnew == x :
#       x = xnew ;
#       xnew = normal_ordered_form( expand( qapply(  x ) ) , independent=True );
#    print(f"APPLYING NO");
#    return xnew



class FiniteBosonFockSpace(Expr) :

    def __init__(self,labels ):
        self.name = f"FiniteBosonFockSpace({labels})";
        self.labels = labels;
        
        if isinstance( labels , list ) :
            self.ketlabels = [ Symbol( 'n' + i, positive=True)  for i in self.labels ];
            self.bralabels = [ Symbol( 'm' + i, positive=True) for i in self.labels ];
            self.B = {} ;
            self.Bd = {};
            for label in labels :
                p = TensorProduct( *  [ ( BosonOp( Symbol(i) ) if i == label else IdentityOperator() ) for i in labels ] ) ;              
                print("P = ", p );
                self.B[label] = p; 
                self.Bd[label] = Dagger(p);
            self.id = TensorProduct( * [ IdentityOperator() for i in labels ] )
        else :
            self.ketlabels = 'n' + labels;
            self.bralabels = 'm' + labels;
            self.B = BosonOp( Symbol( labels ) )
            self.Bd = Dagger( BosonOp( Symbol( labels)));
            self.id = IdentityOperator();
    def tp( self, *x ) :
        s = tuple( [ self.no(i) for i in x ]);
        return TensorProduct(*s);
    def no(self, x):
        xnew = normal_ordered_form(  qapply( x  ).expand( force=True, power_expand=False), independent=True );
        while not xnew == x :
            x = xnew ;
            xnew = normal_ordered_form( ( qapply(  x ) ).expand( force=True, power_expand=False) , independent=True );
        xnew = xnew.replace( TensorProduct, self.tp );
        return xnew

        

    def ket( self, x = None ):
        if x == None :
            x =  self.ketlabels;
        if isinstance( self.labels, list ):
            p = TensorProduct( * [ BosonFockKet(i) for i in x ] )
            return  p;
        else :
            return BosonFockKet(x);

    def bra( self, x = None ) :
        if x == None :
            x = self.bralabels;
        if isinstance( self.labels, list ):
            p = TensorProduct( * [ BosonFockBra(i) for i in x ] )
            return p;
        else :
            return  BosonFockBra(x) ;
            

    def id( self ):
        keys = self.labels;
        if x == None :
            x = ['n' + i for i in keys ];
        if isinstance( self.labels, list ):
            p = TensorProduct( * [ IdentityOperator() for i in x ] )
            return p;
        else :
            return IdentityOperator()

    def one( self ):
        keys = self.labels;
        if isinstance( self.labels, list ):
            x = ['n' + i for i in keys ];
            p = TensorProduct( * [  1 for i in x ] )
            return p;
        else :
            return 1

    def reduce_to_canonical( self, ex ):
        res = ex;
        res = self.no(res);
        res = simplify( doapply( res ).doit() );
        if isinstance( self.labels, list ):
            res = res.subs( self.one(), 1 );
        return res;
