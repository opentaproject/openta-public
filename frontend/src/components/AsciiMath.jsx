// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

'use strict';
import React, { Component } from 'react';
import MathSpan from './MathSpan.jsx';
import { parse } from 'mathjs';
import { toSymbol } from './questiontypes/latex.js';
import { asciiMathToMathJS } from './mathrender/string_parse.js';

var customLatex = (node, options) => {
  if (node.type === 'SymbolNode') {
    const texSymbol = toSymbol(node.name, false);
    return texSymbol;
  } else {
    if ( node.name == 'parse'  ){
	    console.log("PARSER FOUND", node.args[0] )
	    var v = ( node.args[0].evaluate() ).toString();
            console.log("V = " , v )
	    var ve = parse( v)._toTex(options)
	    return ve
    }
    return node._toTex(options);
  }
};

export default class AsciiMath extends Component {
  render() {
    var jsmath = asciiMathToMathJS(this.props.children);
    try {
      var mParsed = parse(jsmath.out).toTex({
        handler: customLatex,
        parenthesis: 'keep' // The keep options keeps parenthesis from input expression, seems to work best.
      });
      return <MathSpan message={'$' + mParsed + '$'} />;
    } catch (e) {
      return <span />;
    }
  }
}
