import { insertImplicitSubscript } from '../mathrender/string_parse.js';
import { parse } from 'mathjs';

import { toSymbol } from './latex';

export const newcustomLatex = (node, options, thiss) => {
  var sym = {};
  sym['cross'] = '\\times';
  sym['dot'] = '\\cdot';
  if ( node.type== 'FunctionNode' && node.name == 'subs' ){
    var lstring =  node.fn._toTex(options);
    var rstring =  node.args[0]._toTex(options);
    var s = node.fn._toTex(options) +  "{" + node.args[0]._toTex(options) + "}" 
    s = s.replace(/\\\\\\end/,'\\end')
    return s
    }
  if ( node.type == 'ArrayNode'  ){
    var types =  node.items.map( (item) => item.type );
    var has_constant = ( node.items.filter( (item) => item.type == 'ConstantNode') ).length > 0 
    var is_pure_array = ( node.items.filter( (item) => item.type != 'ArrayNode') ).length ==  0 
    var  nodetypes = node.items.map( (item) => item.type)
    var largs = node.items.map((item) => item.toTex(options)   );
    if (  ! is_pure_array   ){
      if ( ! has_constant ){
        // var s =  "\\begin{bmatrix} " + ( largs.join('\\\\') ).rstrip('\\')  + "\\end{bmatrix}";
        var s =  "\\begin{bmatrix} " + largs.join(', &')   + "\\end{bmatrix}";
        return s
      }
      else { 
        var s =  "\\begin{bmatrix} " + largs.join(', &')   + "\\end{bmatrix}";
        return s
      }
    } 
    return s

  }
  var varsListMissing = undefined === thiss.varsList;
  if ( node.type == "AccessorNode" ){
    //var rp = {'I' : "-1", "A" : "\\dagger" , "C" : "*","T": "T","." : "."}
    //var p = rp[ node.name]
    p = node.name
    if ( node.index ){
      s = node.object._toTex(options) + newcustomlatex( node.index, options, thiss)
      return s
      }
    if ( node.object.type == 'ArrayNode'  ){
      s = "{" + node.object._toTex(options) + "}^{" + p + "}"
      return s
    } else {
    var rp = {'I' : "-1", "A" : "\\dagger" , "C" : "*","T": "T",".":","}
    var p = rp[ node.name]
    // var s = parse( '' + node.object.toString() + '^' + p + ''   )._toTex(options) ;
    //thiss.parse_dispatch[node.op](node, options);
    var sexp =  node.object.toString() 
    var n =  newcustomLatex( parse( sexp ), options, thiss )
    if (p ){
      var s = '(' + n   + ')^{\\bold{ '  +  p  +  ' }}'  ;
      } else {
      var s = '(' + n   + ').' + node.name
      }
    return s
    }
    
  }

  if (node.name === 'cross' || node.name === 'dot' ) {
    var largs = node.args.map((item) => item.toTex(options));
    var arg0 = node.args[0];
    var arg1 = node.args[1];
    var t0 = arg0.toTex(options)
    if ( "SymbolNode" !== arg0.type  ){
      t0 = '(' + t0 + ')'
    }
    var t1 = arg1.toTex(options)
    if ( 'SymbolNode' !== arg1.type  ){
      t1 = '(' + t1 + ')'
    }
    return t0  +  sym[node.name]  + t1
  }


  if (node.op == "'") {
    if (node.type === 'OperatorNode') {
      var child = node.args[0];
      if (child.type == 'SymbolNode') {
        if (thiss.validSymbols.indexOf(child.name) < 0) {
          thiss.validSymbols.push(child.name);
        }
      }
      return '{' + child._toTex(options) + '^{\\prime} }';
    }

    return '{' + node.args[0].name._toTex(options) + '}^{\\prime}';
  }



  if (node.op in thiss.parse_dispatch) {
    return thiss.parse_dispatch[node.op](node, options);
  }
  if (node.name in thiss.parse_dispatch) {
    return thiss.parse_dispatch[node.name](node, options);
  }

  if (node.type === 'FunctionNode') {

    if ( node.name == 'abs'  ){
      var largs = node.args.map((item) => item.toTex(options));
      var texstring = '\\lceil' + largs.join(',') + '\\rfloor';
      return  texstring;
    }

    if ( node.name == 'subs'  ){
      var largs = node.args.map((item) => item.toTex(options));
      var texstring = '\\lceil' + largs.join(',') + '\\rfloor';
      return  texstring;
    }


    if (thiss.blacklist.indexOf(node.name) !== -1) {
      thiss.mathjswarning += ' : error5';
      thiss.mathjserror = true;
      return '\\color{orange}{' + node._toTex(options) + '}';
    } else {
      var ret = node._toTex(options);
      thiss.isUnclosed = false;
      node.traverse((node, path, parent) => {
        if (node.type === 'FunctionNode' && node.name === 'unclosed') {
          thiss.isUnclosed = true;
          thiss.mathjserror = true;
        }
      });
      if (thiss.isUnclosed) {
        thiss.mathjserror = true;
        thiss.mathjswarning += ' : unclosed function ' + node.name;
        return '\\color{orange}{' + ret + '}';
      } else {
        var origVar = node.name;
      }
      var largs = node.args.map((item) => item._toTex(options));
      const texSymbol = thiss.varProps.hasIn([origVar, 'tex'])
        ? thiss.varProps.getIn([origVar, 'tex'])
        : toSymbol(insertImplicitSubscript(origVar), false); //node._toTex(options);

      var pieces = texSymbol.split('*');
      if (pieces.length == 1) {
        var texstring = '(' + largs.join(',') + ')';
        return '{' + texSymbol + '} ' + texstring + '';
      } else {
        var texstring = '';
        for (var i = 0; i < pieces.length - 1; i++) {
          texstring = texstring + pieces[i] + largs[i];
        }
        return texstring + pieces[i];
      }
    }
  } else if (node.type === 'SymbolNode') {
    if (options.ignore_undefined) {
    }
    const origVar = node.name.replace(/\_/g, '');
    const texSymbol = thiss.varProps.hasIn([origVar, 'tex'])
      ? thiss.varProps.getIn([origVar, 'tex'])
      : toSymbol(insertImplicitSubscript(origVar), false); //node._toTex(options);
    var comment = '';
    if (node.comment) {
      var comment = 'comment'; // node.comment
    }
    if (thiss.blacklist.indexOf(origVar) !== -1) {
      thiss.mathjswarning += ' : disallowed variable';
      thiss.mathjserror = true;
      return '\\color{orange}{' + texSymbol + comment + ' }';
    }
    if (thiss.varsList) {
      if (
        thiss.varsList.indexOf(origVar) !== -1 ||
        thiss.validSymbols.indexOf(origVar) !== -1 ||
        options.ignore_undefined
      ) {
        thiss.mathjserror = false;
        return '\\color{green}{' + texSymbol + '}';
      }
    } else {
      thiss.mathjserror = true;
    }
    thiss.mathjswarning += " : undefined variable '" + node.name + "'";
    return '\\color{red}{' + texSymbol + comment + '}';
  } else if (node.type === 'ParenthesisNode') {
    //if ( node.content.type  == 'ArrayNode' ){
    //  var s = node.content._toTex( options)
    //  return s 
   // }
    thiss.isUnclosed = false;
    node.traverse((node, path, parent) => {
      if (node.type === 'FunctionNode' && node.name === 'unclosed') {
        thiss.isUnclosed = true;
      }
    });
    if (thiss.isUnclosed) {
      thiss.mathjswarning += ' : unclosed right paren';
      thiss.mathjserror = false;
      return '\\color{red}{(} ' + node.content._toTex(options) + '';
    } else {
      return ' ' + node._toTex(options);
    }
  } else if (node.type === 'OperatorNode') {
    if ( node.op == '^'  ){
          var args  = node.args
          if ( node.args[1].type == 'ParenthesisNode' ){
              var largs = node.args[1]
              return '{' + node.args[0]._toTex(options) + '}^{' + largs.content._toTex( options)  + ' }'
            }
          if  ( node.args[1].name  == "i" ){
              return '{' + node.args[0]._toTex(options) + '}^{-1}'
          }

          if  ( node.args[1].name  == "t" ){
              return '{' + node.args[0]._toTex(options) + '}^{t}'
          }
    }

    if (node.fn === 'bitNot') {
      if (node.args[0].type === 'ParenthesisNode') {
        thiss.isUnclosed = false;
        node.args[0].traverse((node, path, parent) => {
          if (node.type === 'FunctionNode' && node.name === 'unclosed') {
            thiss.isUnclosed = true;
          }
        });
        if (thiss.isUnclosed) {
          thiss.mathjswarning += ' : unclosed parenthesis of operator ';
          thiss.mathjserror = true;
          return (
            '\\color{red}{\\left(\\large{\\color{#0f00f0}{\\underline{\\color{black}{' +
            node.args[0].content._toTex(options) +
            '}}}}\\right.}'
          );
        } else {
          return (
            '\\left(\\large{\\color{#0f0f0}{\\underline{\\color{black}{' +
            node.args[0].content._toTex(options) +
            '}}}}\\right)'
          );
        }
      }
      return '\\large{\\color{#0f00f0}{\\underline{\\color{black}{' + node.args[0]._toTex(options) + '}}}}';
    }
  }
};
