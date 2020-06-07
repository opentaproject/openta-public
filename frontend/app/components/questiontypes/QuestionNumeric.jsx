/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { Component } from 'react'; // React specific import
import PropTypes from 'prop-types';

import { registerQuestionType } from './question_type_dispatch.js' // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import SafeMathAlert from '../SafeMathAlert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from '../Badge.jsx'; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import MathSpan from '../MathSpan.jsx';
import HelpNumeric from './HelpNumeric.jsx';
import T from '../Translation.jsx';
import t from '../../translations.js';
import { renderText  } from "./render_text.js"
import mathjs from 'mathjs';
import latex from './latex.js';
import immutable, { List } from 'immutable';
import { enforceList } from '../../immutablehelpers.js';
import { throttle } from 'lodash'
import { parseBlacklist, uniquecat, parseVariableString , parseVariables , AvailableVariables} from './mathexpressionparser.js';
import {units} from './units.js';



//Returns a new string where the character at pos in str is replaced with newstring
function replaceAt(str, pos, newString) {
  return str.slice(0,pos) + newString + str.slice(pos+1);
}

function insertAfter(str, pos, newString) {
  if(pos + 1 < str.length-1)
    return str.slice(0,pos+1) + newString + str.slice(pos+1);
  else
    return str + newString;
}

function insertBefore(str, pos, newString) {
  return str.slice(0,pos) + newString + str.slice(pos);
}

//Parse Bra,Ket,BraKet and KetBra expressions for QM.
var braketify = (sstr) => {
  var snew = sstr.replace(/\<([^<|]+)\|([^|>]+)\>/g, 'Braket($1, $2)');
  var snew = snew.replace(/\<([^<|]+)\|([^|]+)\|([^|>]+)\>/g, 'Braket($1, $2,$3)');
  var snew = snew.replace(/\|([^>]+)\>([\S^\<]+)\<([^|]+)\|/g,'KetBra($1,$2,$3)');
  var snew = snew.replace(/\|([^>]+)\>\S*<([^|]+)\|/g,'KetBra($1,$2)');
  return snew;
}

//An alpha character followed by a number should be rendered in subscript
const insertImplicitSubscript = (asciitext) => {
  var re = /([a-zA-Z]+)([0-9]+)/g;
  return asciitext.replace(re,'$1_$2');
}

//Uses a number of regexp rules to insert implicit multiplication.
var insertImplicitMultiply = (asciitext) => {//{{{
  //
  // first token[space]token ; then [space]integers[paren] ; then [blanks][numbers][token] ; then )[space*](
  // The reason for the complexity is that mathjs is even more lenient with implicit multiplies; 3x is treated as 3*x
  // That is a nuisance which makes the parsing more difficult to comply with
  //
  var re, implicitmultiplies = [
    /([0-9]+)\s+([0-9]+)/g,    // [int] [int] => [int]*[int]
    /([\w~]+)\s+([\w~]+)/g,    // [token] [token] => [token]*[token]
    /([0-9]+)\s+([0-9]+)/g,    // [int] [int] => [int]*[int]
    /([\w~]+)\s+([\w~]+)/g,    // [token] [token] => [token]*[token]
    /(\s+[0-9]+)([(])/g, 	// [space][integers]( => [integer] * (
    /(\W+[0-9]+)([A-Za-z]+)/g, // [nonword][integers][token] => [nonword][integers] * token
    /(\w+)\s+([\[(])/g,           // [token][space]( => [token] * (
    /([)\]])\s*([\w~]+)/g, 	    // )[space][token] => ) * [token]
    /([)\]])\s*([(\[])/g ];         // )[space*]( => ) * (
    var nasciitext = ' '+asciitext + ' ';
    for(re of implicitmultiplies){
      nasciitext = nasciitext.replace(re, '$1 * $2');
    };
    return nasciitext;
}//}}}

// Finds unmatched delimiters and inserts metainformation for the MathJS rendering as custom functions
function fixDelimiters(str) {//{{{
  var starts = ['(', '['];
  var ends = [')', ']'];
  var stack = [];
  var i = 0;
  var warnings = [];
  // Traverse the string one char at a time
  while(i < str.length) {
    // Loop through all delimiters
    for(var j = 0; j < starts.length; j++) {
      // Push on stack if open
      if(str[i] == starts[j])stack.push({delim: j, pos: i});
      // Is the char a closing delimiter?
      if(str[i] == ends[j]) {
        // Compare ending delimiter with the last opened on the stack
        if(stack.length > 0) {
          var {delim, pos} = stack.pop();
          if(delim != j) {
            str = replaceAt(str, pos, ' fail("' + starts[delim] + '") ')
            i = i + 10;
            str = replaceAt(str, i, ' fail("' + ends[j] + '") ')
            i = i + 10;
          }
        }
        // If there was nothing on the stack then there is no corresponding open delimiter
        else {
          str = replaceAt(str, i, ' fail("' + ends[j] + '") ')
          i = i + 10;
        }
      }
    }
    i++;
  }
  // If there are any remaining items in the stack this means there are unmatched opened delimiters. Fix them in reverse so that the position of subsequent items is still valid after the string update
  for(let open of stack.reverse()) {
    if(starts[open.delim] === '(')
      str = str + ' unclosed() ' + ends[open.delim];
    else {
      str = str + ends[open.delim] /*+ ' smalltext("] fattas") '*/;
      warnings.push("\"]\" fattas")
    }
  }
  return {out: str, warnings: warnings};
}//}}}

// Insert the special "~" (bitNot) operator to handle cursor positioning.
// Strategy: Find the opening parenthesis on the same level, if this is not a function call then return the string with the ~ inserted before.
// Example: 1 + ( a + [cursor here]b) => 1 + ~( a + b )
// If its a function call then place the bitNot before the function.
// Example: 1 + sin( a + [cursor here]b) => 1 + ~sin( a + b)
const insertCursor = (str, pos) => {//{{{
  var left = pos;
  var done = false;
  var depth = 0;
  if(left === 0)return str;
  while(!done && left > 0) {
    left--;
    if(left === 0 && depth > 0)
      return str
    if(str[left] === ')')depth++;
    if(str[left] === '(' ) {
      if(depth === 0) {
        while(left > 0 && str[left-1].match(/[a-zA-Z0-9]/g))
          left--;
        return insertBefore(str, left, ' ~');
      }
      depth--;
    }
  }
  return str;
}//}}}

export default class QuestionNumeric extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool, //Indicates if user is allowed to see solution.
  }

  constructor(props) {
    super(props);
    this.state = {
      value: this.props.questionState.getIn(['answer'], ''),
      mathSize: 'medium',
      cursor: 0,
    };
    this.lastParsable = '';
    this.varProps = {}
    this.varsList = [];
    this.validSymbols = ['pi','meter'];
    this.blacklist = [];
    if(this.props.canViewSolution)
      this.state.value = this.props.questionData.getIn(['expression','$'], '').replace(/;/g,'');
  }

  handleChange = (event) => {
    this.setState({value: event.target.value});
  }

  updateCursor = throttle( (pos) => {
    this.setState({cursor: pos});
  }, 500);

  handleSelect = (event) => {
      this.updateCursor(event.target.selectionStart);
  }

  setMathSize = (sizeStr) => {
    this.setState({mathSize: sizeStr});
  }

  componentWillReceiveProps = (newProps) => {
  }

  componentWillMount = () => {
    mathjs.import({ln: mathjs.log});
  }

  customLatex = (node, options) => {
    if(node.type === 'FunctionNode') {
      // Will print in red
      if(node.name === 'fail') {
        return '\\color{red}{' + node.args[0].value + '}';
      }
      // Will print in small red text
      else if(node.name === 'smalltext') {
        return '\\color{red}{\\text{\\small ' + node.args[0].value + '}}';
      }
      // Will not generate any output but is later used to find unmatched parenthesis
      else if(node.name === 'unclosed') {
        return '';
      }
      else if(node.name === 'empty') {
        return '';
      }
      else if(this.blacklist.indexOf(node.name) !== -1) {
        return '\\color{orange}{' + node._toTex(options) + '}';
      }
      else if( node.name === 'Braket'  ){
        var tex0 = node.args[0].toTex(options);
        var tex1 = node.args[1].toTex(options);
        if( node.args.length == 2 ){
          return "\\langle  \\,"+ tex0 +"  \\,|  \\," + tex1 + "  \\,\\rangle"
        }
        else {
          var tex2 = node.args[2].toTex(options);
          return "\\langle \\, "+ tex0 +" \\ |  \\," + tex1 + " \\,| \\," + tex2 + " \\, \\rangle"
        }
      }
      else if( node.name === 'dot'  ){
        if( node.args.length == 1 ){
          var tex0 = node.args[0].toTex(options);
          return "\\left(" + tex0 + "\\right)\\cdot";
        }
        if( node.args.length == 2 ){
          var tex0 = node.args[0].toTex(options);
          var tex1 = node.args[1].toTex(options);
          return "\\left(" + tex0 + "\\right)\\cdot\\left(" + tex1 + "\\right)";
        }
      }
      else if( node.name === 'KetBra'  ){
        var tex0 = node.args[0].toTex(options);
        var tex1 = node.args[1].toTex(options);
        if( node.args.length == 2 ){
          return '|\\,' + tex0 +" \\, \\rangle \\langle \\," + tex1 + " \\,|"
        }
        else {
          var tex2 = node.args[2].toTex(options);
          return '|\\,' + tex0 +" \\, \\rangle \\, " + tex1 + "\\, \\langle \\," + tex2 + " \\,|"
        }
      }
      else {
        var isUnclosed = false;
        node.traverse( (node, path, parent) => {
          if(node.type === 'FunctionNode' && node.name === 'unclosed')isUnclosed = true;
        });
        if(isUnclosed)
          return '\\color{orange}{' + node._toTex(options) + '}';
        else
          return node._toTex(options);
      }
    }
    // Render green if allowed variable otherwise red
    else if(node.type === 'SymbolNode') {
      const origVar = node.name.replace(/\_/g, '');
      const texSymbol = this.varProps.hasIn([origVar, 'tex']) ? this.varProps.getIn([origVar, 'tex']) : latex.toSymbol(node.name,false);//node._toTex(options);
      if(this.blacklist.indexOf(node.name) !== -1)
        return '\\color{orange}{' + texSymbol + '}';
      if(this.varsList.indexOf(node.name) !== -1 || this.validSymbols.indexOf(node.name) !== -1  || this.varProps.hasIn([origVar]) )
        return '\\color{green}{' + texSymbol + '}';
      else
        return '\\color{red}{' + texSymbol + '}';
    }
    // Special handling for unmatched parenthesis, otherwise render normally
    else if(node.type === 'ParenthesisNode') {
      var isUnclosed = false;
      node.traverse( (node, path, parent) => {
        if(node.type === 'FunctionNode' && node.name === 'unclosed')isUnclosed = true;
      });
      if(isUnclosed) {
        return '\\color{red}{(} ' + node.content.toTex(options) + '';
      }
      else
        return node._toTex(options);
    }
    // Cursor handling by hooking into the bitwise not operator that has a very high precedence.
    else if(node.type === 'OperatorNode') {
      if(node.fn === 'bitNot') {
        if(node.args[0].type === 'ParenthesisNode') {
          var isUnclosed = false;
          node.args[0].traverse( (node, path, parent) => {
            if(node.type === 'FunctionNode' && node.name === 'unclosed')isUnclosed = true;
          });
          if(isUnclosed)
            return '\\color{red}{\\left(\\large{\\color{#0f0}{\\underline{\\color{#2d7091}{' + node.args[0].content.toTex(options) + '}}}}\\right.}';
          else
            return '\\left(\\large{\\color{#0f0}{\\underline{\\color{#2d7091}{' + node.args[0].content.toTex(options) + '}}}}\\right)';
        }
        return '\\large{\\color{#0f0}{\\underline{\\color{#2d7091}{' + node.args[0].toTex(options) + '}}}}';
      }
    }
  }


  renderAsciiMath = (asciitext) => {
      var cursorComplete = false;
      var cursorPos = this.state.cursor;
      if(cursorPos > asciitext.length)cursorPos = asciitext.length;
      var parsed = insertCursor(asciitext, cursorPos);
      parsed = insertImplicitMultiply(parsed);
      parsed = insertImplicitSubscript(parsed);
      parsed = braketify(parsed);
      var delimitersFixed = fixDelimiters(parsed);
      parsed = delimitersFixed.out;
      parsed = parsed + ' empty()';
      try {
        var mParsed = mathjs.parse(parsed).toTex({
          parenthesis: 'keep', // The keep options keeps parenthesis from input expression, seems to work best.
          handler: this.customLatex, // Custom latex node handler
        });
        if(typeof mParsed === 'string' && mParsed !== 'undefined') {
          this.lastParsable = mParsed.replace(/\\\\end{bmatrix}/g,'end{bmatrix}'); // MathJS outputs an extra \\ which KaTeX interprets as a new line
        }
        return {out: this.lastParsable, warnings: delimitersFixed.warnings}
      }
      catch(e) {
        return {out: this.lastParsable, warnings: delimitersFixed.warnings, error: "MathJS parse/toTex error"}
      }
  }

  //Parse the shorthand semicolor separated variable string
/*
  parseVariableString = (variableString) => {
    var vars = variableString.trim()
      .split(';')
      .filter(str => str !== "")
      .map( str => str.split('=') )
      .map( entry => insertImplicitSubscript(entry[0].trim()) );
      return vars;
  }

*/
  //Parse variables and their optional properties

arrayUnique = (array) =>  {
    var a = array.concat();
    for(var i=0; i<a.length; ++i) {
        for(var j=i+1; j<a.length; ++j) {
            if(a[i] === a[j])
                a.splice(j--, 1);
        }
    }

    return a;
}

  parseBlacklist = () => {
    var blacklist = immutable.List([]);
    var globalBlacklistObject =  this.props.questionData.getIn(['global','blacklist','token']);
    var blacklistObject =  this.props.questionData.getIn(['blacklist','token']);
    if( globalBlacklistObject )blacklist = blacklist.concat(enforceList(globalBlacklistObject));
    if( blacklistObject )blacklist = blacklist.concat(enforceList(blacklistObject));
    this.blacklist = blacklist.map( item => insertImplicitSubscript(item.get('$','').trim()) ).toJS();
  }

  /* render gets called every time the question is shown on screen */
  render() {
    // Some convenience definitions
    var question = this.props.questionData;
    var state = this.props.questionState;
    var submit = this.props.submitFunction;
    var pending = this.props.questionPending;
    var hidevariables = question.getIn(['@attr', 'hidevariables'], false);

    /* Both the questionData and questionState are of type Map from immutable.js. They are nested dictionaries that are accessed via the get and getIn functions. For example question.get('text') retrieves <question> <text> * </text> </question>. Deeper structures can be accessed with getIn, for example question.getIn(['tag1', 'tag2']) would retrieve <question> <tag1> <tag2> * </tag2> </tag1> </question>. */

    // System state data
    var lastAnswer = state.getIn(['answer'], ''); // Last saved answer in database, same format as passed to the submitFunction
    var correct = state.getIn(['response', 'correct'], false) || state.getIn(['correct'], false); // Boolean indicating if the grader reported correct answer
    var unchecked = '(' + t('unchecked') + ')';
    var comment = state.getIn(['response', 'comment'], '');
    var tdict = state.getIn(['response', 'dict'], '');

    // Custom state data
    var latex = state.getIn(['response', 'latex'], ''); // Custom field containing the latex code obtained from SymPy.
    var error = state.getIn(['response', 'error']); // Custom field containing error information
    // console.log("ERROR = ", error )
    var author_error = state.getIn(['response', 'author_error']); // Custom field containing error information
    var warning = state.getIn(['response', 'warning']); // Custom field containing error information
    var status = state.getIn(['response', 'status'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
    // var precision = state.getIn(['response','precision'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
    var varsListUsed = this.props.questionData.get('usedvariablelist', List([])).toJS();

    var precision = question.get('precision', 0)
    if (precision == 0) {
      precision = '\u00B1 ' + ((100 * question.getIn(['@attr', 'precision'], 0))).toString() + '%'
    }

    if (state.getIn(['correct'], null) == null) {
      var feedback = false
    } else {
      var feedback = true
    }

    if (state.getIn(['response', 'detail']))
      error = "Ett fel uppstod. (Detta kan bero på att du inte är inloggad, om problem kvarstår var vänlig hör av dig.)";

    this.parseBlacklist();
    var res = parseVariables(question);
    this.varsList = res['varsList'];
    this.varProps = res['varProps'];
    console.log("varProps = ", (this.varProps).toJS());
    var varsUsed = res['varsUsed'];

    var mathjsEvalVars = {}

    // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
    // The styling classes are from UIKit, see getuikit.com for available elements.
    var availableVariables = AvailableVariables(question, 'sv')
    var graderResponse = null;
    var input = this.state.value.trim();
    var hasChanged = input !== lastAnswer;
    var nonEmpty = input !== "";
    var renderedResult = this.renderAsciiMath(this.state.value);
    var renderedMath = renderedResult.out;
    if (input === lastAnswer && lastAnswer !== '' && !error) {
      if (feedback) {
        if (correct)
          graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + t(' is correct.')} type="success" key="input" hasMath={true} />);
        else
          graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + t(' is not correct.')} type="warning" key="input" hasMath={true} />);
      } else {
        graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + unchecked + t(comment, tdict)} type="text" key="input" hasMath={true} />);
      }
    } else if (input !== '') {
      graderResponse = (<SafeMathAlert className="uk-margin-small-top uk-margin-small-bottom" message={renderedMath} key="input" />);
    }

    var mathjsError = false;
    try {
      var mathjsParse = mathjs.eval(insertImplicitSubscript(input), mathjsEvalVars);
    }
    catch (e) {
      if (e instanceof Error && !(e instanceof TypeError))
        mathjsError = e.toString();//(<Alert type="warning" message={ e.toString() }/>);
      if (e instanceof TypeError)
        mathjsError = e.toString();//(<Alert type="warning" message="Expression unfinished"/>);
    }
    var mathSizeClass = 'large';
    var sizeActive = 'uk-text-bold';
    switch (this.state.mathSize) {
      case 'small':
        mathSizeClass = 'uk-text-small'; break;
      case 'medium':
        mathSizeClass = ''; break;
      case 'large':
        mathSizeClass = 'uk-text-large'; break;
    }
    return (
      <div className="">
        <label className="uk-form-row uk-display-inline-block">{this.props.renderText(question.getIn(['text']))} <span className="uk-text-small uk-text-primary">  {availableVariables} <T>NUMERICAL</T> {precision}</span><HelpNumeric /></label>
        {hasChanged && lastAnswer !== '' && (<Badge message={t('previous') + lastAnswer} hasMath={false} className="uk-text-small uk-margin-small-left uk-margin-bottom-remove" />)}
        <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
            <div className="uk-width-1-1">
              <textarea className={"uk-width-1-1 "} value={this.state.value} onSelect={this.handleSelect} onChange={this.handleChange} ></textarea>
            </div>
          </div>
        { ! this.props.locked && (
          <div className="uk-width-1-6">
            <a onClick={(event) => submit(input)} className={"uk-width-1-1 uk-button uk-padding-remove " + (nonEmpty && hasChanged && !mathjsError ? "uk-button-success" : "")}>
              {pending && <i className="uk-icon-cog uk-icon-spin" />}
              {!pending && <i className="uk-icon uk-icon-send" />}
            </a>
          </div>
        )}
        </div>
        {error && !hasChanged && <Alert message={error} type="error" key="err" />}
        {author_error && this.props.isAuthor && <Alert message={author_error} type="error" key="author_error" />}
        {warning && !hasChanged && <Alert message={warning} type="warning" key="warning" />}
        <div className="uk-flex">
          <span className={"uk-width-1-1 " + mathSizeClass}>{graderResponse}</span>
        </div>
        <div className="uk-float-right uk-flex">
          <div className={"uk-text-small uk-margin-small-left " + (this.state.mathSize === 'small' ? sizeActive : '')}>
            <a onClick={() => this.setMathSize('small')}>A</a>
          </div>
          <div className={"uk-margin-small-left " + (this.state.mathSize === 'medium' ? sizeActive : '')}>
            <a onClick={() => this.setMathSize('medium')}>A</a>
          </div>
          <div className={"uk-text-large uk-margin-small-left " + (this.state.mathSize === 'large' ? sizeActive : '')}>
            <a onClick={() => this.setMathSize('large')}>A</a>
          </div>
        </div>
        {renderedResult.error && <span className="uk-text-danger">Kontrollera syntax. (Visar senaste fungerande ovan.)</span>}
        { /*mathjsError*/}
        {renderedResult.warnings.length > 0 && <Alert message={renderedResult.warnings.join(', ')} type="warning" key="renderWarning" />}
      </div>
    );
  }
}

//Register the question component with the system
registerQuestionType('Numeric', QuestionNumeric);
