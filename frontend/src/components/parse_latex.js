// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import { all, create } from 'mathjs';
const math = create(all);




export function mul(node, options) {
  // console.log("NODE = ", node )
  if ('mul' === node.name) {
    var order = node.args.length;
    var largs = node.args.map((item) => item.toTex(options));
    //console.log("largs = ", largs )
    var i = 0;
    var texstring = '(' + largs.join('\\bullet') + ')';
    return texstring;
  }
}


export function com(node, options) {
  // console.log("NODE = ", node )
  if ('com' === node.name) {
    var order = node.args.length;
    var largs = node.args.map((item) => item.toTex(options));
    //console.log("largs = ", largs )
    var i = 0;
    var texstring = '[ \\, ' + largs.join('\\,,') + ' \\, ]';
    return texstring;
  }
}

export function fail(node, option) {
  if (node.name === 'fail' && !options.ignore_undefined) {
    this.mathjserror = true;
    this.mathjswarning += ' : error1';
    return '\\color{red}{' + node.args[0].value + '}';
  }
}

export function prime(node, options) {
  if (node.op == "'") {
    //console.log("QUOTE OPERATOR NODE")
    if (node.type === 'OperatorNode') {
      var child = node.args[0];
      if (child.type == 'SymbolNode') {
        if (this.validSymbols.indexOf(child.name) < 0) {
          this.validSymbols.push(child.name);
        }
      }
      return '{' + child.toTex(options) + '^{\\prime} }';
    }
    return '{' + node.args[0].name.toTex(options) + '}^{\\prime}';
  }
}

export function smalltext(node, options) {
  if (node.name === 'smalltext') {
    this.mathjserror = true;
    this.mathjswarning += ' : error2';

    return '\\color{red}{\\text{\\small ' + node.args[0].value + '}}';
  }
  // Will not generate any output but is later used to find unmatched parenthesis
}
export function unclosed(node, options) {
  if (node.name === 'unclosed') {
    this.mathjserror = true;
    this.mathjswarning += ' : unclosed left paren';
    return '';
  }
}
export function empty(node, options) {
  if (node.name === 'empty') {
    return '';
  }
}

export function Braket(node, options) {
  if (node.name === 'Braket') {
    var tex0 = node.args[0].toTex(options);
    var tex1 = node.args[1].toTex(options);
    if (node.args.length == 2) {
      return '\\langle  \\,' + tex0 + '  \\,|  \\,' + tex1 + '  \\,\\rangle';
    } else {
      var tex2 = node.args[2].toTex(options);
      return '\\langle \\, ' + tex0 + ' \\ |  \\,' + tex1 + ' \\,| \\,' + tex2 + ' \\, \\rangle';
    }
  }
}

export function braket(node, options) {
  if (node.name === 'braket') {
    var tex0 = node.args[0].toTex(options);
    var tex1 = node.args[1].toTex(options);
    if (node.args.length == 2) {
      return '\\langle  \\,' + tex0 + '  \\,|  \\,' + tex1 + '  \\,\\rangle';
    } else {
      var tex2 = node.args[2].toTex(options);
      return '\\langle \\, ' + tex0 + ' \\ |  \\,' + tex1 + ' \\,| \\,' + tex2 + ' \\, \\rangle';
    }
  }
}


export function ket(node, options) {
  if (node.name === 'ket') {
    var tex0 = node.args[0].toTex(options);
      return '  \\,|  \\,' + tex0 + '  \\,\\rangle';
    }
  }

export function bra(node, options) {
  if (node.name === 'bra') {
    var tex0 = node.args[0].toTex(options);
      return '  \\, \\langle  \\,' + tex0 + '  \\,|';
    }
  }


export function dot(node, options) {
  if (node.name === 'dot') {
    if (node.args.length == 1) {
      var tex0 = node.args[0].toTex(options);
      var child = node.args[0];
      if (child.type == 'SymbolNode') {
        return '\\dot{' + tex0 + '}';
      } else {
        return '\\frac{d}{dt} ' + tex0;
      }
    }
  }
}
export function KetBra(node, options) {
  if (node.name === 'KetBra') {
    var tex0 = node.args[0].toTex(options);
    var tex1 = node.args[1].toTex(options);
    if (node.args.length == 2) {
      return '|\\,' + tex0 + ' \\, \\rangle \\langle \\,' + tex1 + ' \\,|';
    } else {
      var tex2 = node.args[2].toTex(options);
      return '|\\,' + tex0 + ' \\, \\rangle \\, ' + tex1 + '\\, \\langle \\,' + tex2 + ' \\,|';
    }
  }
}
export function curl(node, options) {
  if (node.name === 'curl') {
    var tex0 = node.args[0].toTex(options);
    var child = node.args[0];
    if (child.type == 'SymbolNode') {
      return '\\nabla \\times ' + tex0 + '';
    } else {
      return '\\nabla \\times (' + tex0 + ')';
    }
  }
}
export function cross(node, options) {
  if (node.name === 'cross') {
    var tex0 = node.args[0].toTex(options);
    var tex1 = node.args[1].toTex(options);

    var child = node.args[0];
    if (child.type == 'SymbolNode') {
      return '(' + tex0 + ' \\times ' + tex1 + ')';
    } else {
      return '(' + tex0 + ' \\times ' + tex1 + ')';
    }
  }
}

export function div(node, options) {
  if (node.name === 'div') {
    var child = node.args[0];
    var tex0 = child.toTex(options);
    if (child.type == 'SymbolNode') {
      return '\\nabla \\circ ' + tex0 + '';
    } else {
      return '\\nabla \\circ(' + tex0 + ')';
    }
  }
}

export function partial(node, options) {
  if (node.name === 'partial') {
    if (node.args.length == 2) {
      var tex0 = node.args[0].toTex(options);
      var tex1 = node.args[1].toTex(options);
      return '\\frac{ \\partial ' + tex0 + '}{ \\partial ' + tex1 + '}';
    } else if (node.args.length > 2) {
      var tex0 = node.args[0].toTex(options);
      node.args.shift();
      var order = node.args.length;
      var largs = node.args.map((item) => item.toTex(options));
      var i = 0;
      var texstring = '';
      var supercript = 1;
      while (i < order - 1) {
        if (largs[i] == largs[i + 1]) {
          supercript = supercript + 1;
        } else {
          texstring =
            supercript == 1
              ? texstring + '\\partial ' + largs[i]
              : texstring + '\\partial^{' + supercript.toString() + '}' + largs[i];
          supercript = 1;
        }
        i = i + 1;
      }
      texstring =
        supercript == 1
          ? texstring + '\\partial ' + largs[i]
          : texstring + '\\partial^{' + supercript.toString() + '}' + largs[i];
      return '\\frac{ {\\partial}^{' + order + '}' + tex0 + '}{' + texstring + '}';
    }
  }
}
export function grad(node, options) {
  if (node.name === 'grad') {
    var tex0 = node.args[0].toTex(options);
    var child = node.args[0];
    if (child.type == 'SymbolNode') {
      return '\\nabla ' + tex0 + '';
    } else {
      return '\\nabla  (' + tex0 + ')';
    }
  }
}

export function del_2(node, options) {
  if (node.name === 'del_2') {
    var tex0 = node.args[0].toTex(options);
    var child = node.args[0];
    if (child.type == 'SymbolNode') {
      return '\\nabla^2 ' + tex0 + '';
    } else {
      return '\\nabla^2  (' + tex0 + ')';
    }
  }
}

function func(node, options) {
 var tex0 = node.args[0].toTex(options);
 return '\\text{' + node.name + '}({' + tex0 + '})';
}


export function sin(node, options) {
  return func( node, options)
}

export function cos(node, options) {
  return func( node, options)
}

export function sinh(node, options) {
  return func( node, options)
}

export function cosh(node, options) {
  return func( node, options)
}

export function tan(node, options) {
  return func( node, options)
}

export function tanh(node, options) {
  return func( node, options)
}

export function log(node, options) {
  return func( node, options)
}

export function ln(node, options) {
  return func( node, options)
}



export function sqrt(node, options) {
  if (node.name === 'sqrt') {
    var tex0 = node.args[0].toTex(options);
    return '\\sqrt{' + tex0 + '}';
  }
}

export function parse(node, options) {
  if (node.name === 'parse') {
    return math.parse( ( node.args[0].evaluate() ).toString() ).toTex(options)
  }
}

export function Matrix(node, options) {
  if (node.name === 'Matrix') {
    var v = node.args[0];
    return  node.args[0].toTex(options)
  }
}



export function erf(node, options) {
  if (node.name == 'erf') {
    ret = ret.replace(/^erf/, '\\mathrm{erf}');
  }
  return ret;
}

// export {parse_mul, parse_fail, parse_prime, smalltext, unclosed, empty }
