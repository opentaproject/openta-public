/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { PropTypes, Component } from 'react'; // React specific import

import { registerQuestionType } from './question_type_dispatch.js' // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import SafeMathAlert from '../SafeMathAlert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from '../Badge.jsx'; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpCompareNumeric from './HelpCompareNumeric.jsx';
import mathjs from 'mathjs';
import immutable, { List } from 'immutable';
import { enforceList } from '../../immutablehelpers.js';
import { throttle } from 'lodash'

//Returns a new string where the character at pos in str is replaced with newstring
function replaceAt(str, pos, newString) {
  return str.slice(0,pos) + newString + str.slice(pos+1);
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

var insertImplicitMultiply = (asciitext) => {
  //
  // first token[space]token ; then [space]integers[paren] ; then [blanks][numbers][token] ; then )[space*](
  // The reason for the complexity is that mathjs is even more lenient with implicit multiplies; 3x is treated as 3*x
  // That is a nuisance which makes the parsing more difficult to comply with
  //
  var re, implicitmultiplies = [
    /([0-9]+)\s+([0-9]+)/g,    // [int] [int] => [int]*[int]
    /(\w+)\s+(\w+)/g,    // [token] [token] => [token]*[token]
    /(\s+[0-9]+)([(])/g, 	// [space][integers]( => [integer] * ( 
    /(\W+[0-9]+)([A-Za-z]+)/g, // [nonword][integers][token] => [nonword][integers] * token
    /(\w+)\s+([(])/g,           // [token][space]( => [token] * (
    /([)])\s*(\w+)/g, 	    // )[space][token] => ) * [token]
    /([)])\s*([(])/g ];         // )[space*]( => ) * (
    var nasciitext = ' '+asciitext + ' ';
    for(re of implicitmultiplies){
      nasciitext = nasciitext.replace(re, '$1 * $2').replace(re,'$1 * $2');
    };
    return nasciitext;
}

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

export default class QuestionCompareNumeric extends Component {
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
      cursor: 0,
    };
    this.lastParsable = '';
    this.varProps = {};
    this.varsList = [];
    this.blacklist = [];
    if(this.props.canViewSolution)
      this.state.value = this.props.questionData.getIn(['expression','$'], '').replace(/;/g,'');
  }

  handleChange = (event) => {
    this.setState({value: event.target.value});
  }

  updateCursor = throttle( (pos) => {
    this.setState({cursor: pos});
  }, 1000);

  handleSelect = (event) => {
      this.updateCursor(event.target.selectionStart);
  }

  componentWillReceiveProps = (newProps) => {
    //this.setState({ value: newProps.questionState.getIn(['answer'],'') });
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
      else if(node.name === 'cursor') {
        return '\\color{purple}';
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
    }
    // Render green if allowed variable otherwise red
    else if(node.type === 'SymbolNode') {
      const origVar = node.name.replace(/\_/g, '');
      const texSymbol = this.varProps.hasIn([origVar, 'tex']) ? this.varProps.getIn([origVar, 'tex']) : node._toTex(options);
      if(this.blacklist.indexOf(node.name) !== -1) 
        return '\\color{orange}{' + texSymbol + '}';
      if(this.varsList.indexOf(node.name) !== -1)
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
    else if(node.type === 'OperatorNode') {
      if(node.fn === 'bitNot') {
        return '\\underline{' + node.args[0].toTex(options) + '}';
      }
    }
  }

  renderAsciiMath = (asciitext) => {
      
      var cursorComplete = false;
      var cursorPos = this.state.cursor;
      while(cursorPos > 0 && cursorPos >= asciitext.length)cursorPos--;
      while(!cursorComplete) {
        if(cursorPos <= 0) 
          cursorComplete = true;
        else if(!asciitext[cursorPos-1].match(/[a-zA-Z0-9\)\]]/g))
          cursorComplete = true;
        else
          cursorPos--;
      }
      asciitext = asciitext.substr(0, cursorPos) + " ~" + asciitext.substr(cursorPos);
      var parsed = insertImplicitMultiply(asciitext);
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
        return {out: this.lastParsable, warnings: delimitersFixed.warnings}
      }
  }

  //Parse the shorthand semicolor separated variable string
  parseVariableString = (variableString) => {
    var vars = variableString.trim()
      .split(';')
      .filter(str => str !== "")
      .map( str => str.split('=') )
      .map( entry => insertImplicitSubscript(entry[0].trim()) );
      return vars;
  }

  //Parse variables and their optional properties
  parseVariables = () => {
    this.varsList = this.parseVariableString(this.props.questionData.getIn(['global','$'], ''));
    // Create a map keyed by the variable token containing all its other child elements as a submap for easy indexing
    var varPropsList = enforceList(this.props.questionData.getIn(['global', 'var'], List([])));
    for(let v of varPropsList) {
      if(v.has('token') && this.varsList.indexOf(v.getIn(['token','$'])) == -1) {
        this.varsList.push(insertImplicitSubscript(v.getIn(['token','$'])));
      }
    }
    this.varProps = varPropsList.map( item => ({
      //The token is the key, the other items that are not the token or the special $children$ are added as a map.
      [item.getIn(['token', '$'], '')]: item.filterNot( (val, key) => key === 'token' || key === '$children$').map( val => val.get('$') )
    }) )
    .reduce( (prev, next) => prev.merge(next), immutable.Map({}));
  }

  parseBlacklist = () => {
    var blacklistObject =  this.props.questionData.getIn(['global','blacklist','token']);
    if( blacklistObject ){
      var blacklistList = enforceList(blacklistObject);
      this.blacklist = blacklistObject.map( item => insertImplicitSubscript(item.get('$','').trim()) ).toJS();
    }
  }

  /* render gets called every time the question is shown on screen */
  render() {  
  // Some convenience definitions
  var question = this.props.questionData;
  var state = this.props.questionState;
  var submit = this.props.submitFunction;
  var pending = this.props.questionPending;
  
  /* Both the questionData and questionState are of type Map from immutable.js. They are nested dictionaries that are accessed via the get and getIn functions. For example question.get('text') retrieves <question> <text> * </text> </question>. Deeper structures can be accessed with getIn, for example question.getIn(['tag1', 'tag2']) would retrieve <question> <tag1> <tag2> * </tag2> </tag1> </question>. */

  // System state data
  var lastAnswer = state.getIn(['answer'], ''); // Last saved answer in database, same format as passed to the submitFunction
  var correct = state.getIn(['response','correct'], false) || state.getIn(['correct'], false); // Boolean indicating if the grader reported correct answer

  // Custom state data
  var latex = state.getIn(['response','latex'], ''); // Custom field containing the latex code obtained from SymPy.
  var error = state.getIn(['response','error']); // Custom field containing error information
  var author_error = state.getIn(['response','author_error']); // Custom field containing error information
  var warning = state.getIn(['response','warning']); // Custom field containing error information
  var status = state.getIn(['response','status'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
  if(state.getIn(['response','detail']))
    error = "Du är inte inloggad, tryck på logga ut eller ladda om sidan.";

  this.parseBlacklist();
  this.parseVariables();

  var mathjsEvalVars = {}
  var availableVariables = "";
  if(this.varsList) {
    this.varsList.map( v => {mathjsEvalVars[v] = 1;} );
    availableVariables = this.varsList.length ? "(i termer av " + this.varsList.filter(v => typeof v === 'string').map( v => v.replace(/\_/g,'')).join(", ") + ")" : "";
  }
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.
  var graderResponse = null;
  var input = this.state.value.trim();
  var hasChanged = input !== lastAnswer;
  var nonEmpty = input !== "";
  var renderedResult = this.renderAsciiMath(this.state.value);
  var renderedMath = renderedResult.out;
  if(input === lastAnswer && lastAnswer !== '' && !error) {
    if(correct)
       graderResponse = (<Alert message={"$" + renderedMath + "$" + " är korrekt."} type="success" key="input" hasMath={true}/>);
    else
      graderResponse = (<Alert message={"$" + renderedMath + "$" + " är inte korrekt."} type="warning" key="input" hasMath={true}/>);
  } else if(input !== ''){
    graderResponse = (<SafeMathAlert message={ renderedMath } key="input"/>);
  }
  var mathjsError = false;
  try {
    var mathjsParse = mathjs.eval(insertImplicitSubscript(input), mathjsEvalVars);
  }
  catch(e) {
    if(e instanceof Error && !(e instanceof TypeError))
      mathjsError = e.toString();//(<Alert type="warning" message={ e.toString() }/>);
    if(e instanceof TypeError)
      mathjsError = e.toString();//(<Alert type="warning" message="Expression unfinished"/>);
  }
  return (
        <div className="">
          <label className="uk-form-row uk-display-inline-block">{question.getIn(['text','$'],'')} <span className="uk-text-small uk-text-primary">{availableVariables}</span><HelpCompareNumeric/></label>
{ hasChanged && lastAnswer !== '' && (<Badge message={"föregående: " + lastAnswer} hasMath={false} className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"/>)}
          <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
          <div className="uk-width-1-1">
            <textarea className={"uk-width-1-1 "} value={this.state.value} onSelect={this.handleSelect} onChange={this.handleChange} ></textarea>
          </div>
          </div>
          <div className="uk-width-1-6">
            <a onClick={(event) => submit(input)} className={ "uk-width-1-1 uk-button uk-padding-remove " + (nonEmpty && hasChanged && !mathjsError ? "uk-button-success" : "")}>
              { pending && <i className="uk-icon-cog uk-icon-spin"/> }
              { !pending && <i className="uk-icon uk-icon-send"/> }
            </a>
            </div>
          </div>
          { error && !hasChanged && <Alert message={error} type="error" key="err"/> }
          { author_error && this.props.isAuthor && <Alert message={author_error} type="error" key="author_error"/> }
        { warning && !hasChanged && <Alert message={warning} type="warning" key="warning"/> }
        { graderResponse }
        { /*mathjsError*/ }
        { renderedResult.warnings.length > 0 && <Alert message={renderedResult.warnings.join(', ')} type="warning" key="renderWarning"/>}
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('compareNumeric', QuestionCompareNumeric);
