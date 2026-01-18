# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

def ar( expr,level=0):
    print(f" DO AR = { expr } " )
    if not expr.args :
        return expr;
    if not 'MyArray' in str(expr):
        return expr;
    
    print(f"CONTINUE WITH {expr}")
    
    if expr.args   :
        arglist = [ ar( i, level + 1 ) for i in expr.args ] ;
        print(f" ARGLIST = {arglist}")
        if len( arglist ) == 1  and arglist[0].func.__name__ == 'MyArray' :
            f = expr.func;
            arglist  = arglist[0].args
            ex = ar( MyArray( *[ f(x) for x in arglist ]) );
            return ex;
        else :
            fnames = [ x.func.__name__ for x in arglist if x.args];
            print(f"FNAMES = {fnames}");
            if 'MyArray' in fnames and not expr.func.__name__ == 'MyArray':
                print("MyArray FOUND");
                f = expr.func ;
                print(f"FUNC IS {f.__name__}")
                myarrays = [ x for x in arglist if x.func.__name__ == 'MyArray']
                myarray = myarrays[0];
                print(f"myarrayexample = {myarray} {myarray.args} ");
                jm = len(myarray.args);
                print(f" JM = {jm}") ;
                nargs = [];
                for j in range(0, jm ):
                    a = [ x.args[j]  if x.args else  x   for x in arglist ];
                    r = f( *a );
                    print(f"R = {r} , A = ", a );
                    nargs.append( ar( r, level + 1 )  );
                print(f"NARGS = {nargs}")
                arglist = nargs;
                
                if len( myarrays ) > 1 and f.__name__ == 'Mul' :
                    print(f"FOUND PRODUCT OF MYARRYS");
                    ex = ar( Add( * arglist ) )
                else :
                    ex = MyArray( *arglist ) ;
                print(f" EX = {ex}")
                       
            else :
                ex =expr.func( * arglist )
            return ex
