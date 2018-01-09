"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import MathSpan from './MathSpan.jsx';
import mathjs from 'mathjs';
import latex from './questiontypes/latex.js';
import immutable from 'immutable';
import { asciiMathToMathJS } from './mathrender/string_parse.js'

var customLatex = (node, options) => {
    if(node.type === 'SymbolNode') {
      const texSymbol = latex.toSymbol(node.name, false);
      return texSymbol;
    } else {
      return node._toTex(options);
    }
}

export default class AsciiMath extends Component {
  render() {
    var jsmath = asciiMathToMathJS(this.props.children);
    try {
      var mParsed = mathjs.parse(jsmath.out).toTex({
        handler: customLatex,
        parenthesis: 'keep' // The keep options keeps parenthesis from input expression, seems to work best.
      });
      return (<MathSpan message={"$" + mParsed + "$"}/>);
    }
    catch(e) {
      return (<span/>);
    }
  }
}
