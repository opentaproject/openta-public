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
import immutable from 'immutable';

//Returns a new string where the character at pos in str is replaced with newstring
function replaceAt(str, pos, newString) {
  return str.slice(0,pos) + newString + str.slice(pos+1);
}

//An alpha character followed by a number should be rendered in subscript
const insertImplicitSubscript = (asciitext) => {
  var re, implicitsubscripts = [/([a-zA-Z]+)([0-9]+)/g ] ;
  var nasciitext = asciitext;
  for(re of implicitsubscripts){
    nasciitext = nasciitext.replace(re,'$1_$2');
  };
  return nasciitext;
}

// Finds unmatched delimiters and inserts metainformation for the MathJS rendering as custom functions
function fixDelimiters(str) {//{{{
  var starts = ['(', '['];
  var ends = [')', ']'];
  var stack = [];
  var i = 0;
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
    else
      str = str + ends[open.delim] /*+ ' smalltext("] fattas") '*/;
  }
  return str;
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
    };
    this.lastParsable = '';
    this.varsList = [];
    this.blacklist = [];
    if(this.props.canViewSolution)
      this.state.value = this.props.questionData.getIn(['expression','$'], '').replace(/;/g,'');
  }

  handleChange = (event) => {
    this.setState({value: event.target.value});
  }

  componentWillReceiveProps = (newProps) => {
    //this.setState({ value: newProps.questionState.getIn(['answer'],'') });
  }

  componentWillMount = () => {
    //var vars = this.parseVariables(this.props.questionData.getIn(['global','$'], ''));
    //this.vars = vars.slice();
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
    }
    // Render green if allowed variable otherwise red
    else if(node.type === 'SymbolNode') {
      if(this.blacklist.indexOf(node.name) !== -1) 
        return '\\color{orange}{' + node._toTex(options) + '}';
      if(this.varsList.indexOf(node.name) !== -1)
        return '\\color{green}{' + node._toTex(options) + '}';
      else 
        return '\\color{red}{' + node._toTex(options) + '}';
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
    mathjs.import({ln: mathjs.log});
  }

  renderAsciiMath = (asciitext) => {
      //Some initial parsing of commonly used patterns
      var re = /([a-zA-Z]+)([0-9]+)/g;
      var re2 = /([a-zA-Z0-9)])\s+([(a-zA-Z0-9])/g;
      var re3 = /([a-zA-Z0-9]+)\s+([a-zA-Z0-9]+)/g;
      var parsed = asciitext.replace(re, '$1_$2');
      var parsed = parsed.replace(re2,'$1 * $2');
      parsed = parsed.replace(re3,'$1 * $2');
      //parsed = insertImplicitSubscript(parsed);
      parsed = fixDelimiters(parsed);
      parsed = parsed + ' empty()';
      try {
        var mParsed = mathjs.parse(parsed).toTex({
          parenthesis: 'keep', // The keep options keeps parenthesis from input expression, seems to work best.
          handler: this.customLatex, // Custom latex node handler
        });
        if(mParsed !== 'undefined') {
          this.lastParsable = insertImplicitSubscript(mParsed.replace(/\\\\end{bmatrix}/g,'end{bmatrix}')); // MathJS outputs an extra \\ which KaTeX interprets as a new line
        }
        return this.lastParsable;
      }
      catch(e) {
        return this.lastParsable;
      }
  }

  parseVariables = (variableString) => {
    var vars = variableString.trim()
      .split(';')
      .filter(str => str !== "")
      .map( str => str.split('=') )
      .map( entry => insertImplicitSubscript(entry[0].trim()) );
      return vars;
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
  var blacklistObject =  this.props.questionData.getIn(['global','blacklist','token']);
  if( blacklistObject ){
    if(!immutable.List.isList(blacklistObject))blacklistObject = immutable.List([blacklistObject]);
    this.blacklist = blacklistObject.map( item => insertImplicitSubscript(item.get('$','').trim()) ).toJS();
  }
  this.varsList = this.parseVariables(this.props.questionData.getIn(['global','$'], ''));
  var mathjsEvalVars = {}
  if(this.varsList) {
    this.varsList.map( v => {mathjsEvalVars[v] = 1;} );
  }
  var availableVariables = this.varsList.length ? "(i termer av " + this.varsList.join(", ") + ")" : "";
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.
  var graderResponse = null;
  var input = this.state.value.trim();
  var hasChanged = input !== lastAnswer;
  var nonEmpty = input !== "";
  if(input === lastAnswer && lastAnswer !== '' && !error) {
    if(correct)
       graderResponse = (<Alert message={"$" + this.renderAsciiMath(input) + "$" + " är korrekt."} type="success" key="input" hasMath={true}/>);
    else
      graderResponse = (<Alert message={"$" + this.renderAsciiMath(input) + "$" + " är inte korrekt."} type="warning" key="input" hasMath={true}/>);
  } else if(input !== ''){
    graderResponse = (<SafeMathAlert message={this.renderAsciiMath(input)} key="input"/>);
  }
  var mathjsError = null;
  try {
    var mathjsParse = mathjs.eval(input, mathjsEvalVars);
  }
  catch(e) {
    if(e instanceof Error && !(e instanceof TypeError))
      mathjsError = (<Alert type="warning" message={ e.toString() }/>);
    if(e instanceof TypeError)
      mathjsError = (<Alert type="warning" message="Expression unfinished"/>);
  }
  return (
        <div className="">
          <label className="uk-form-row uk-display-inline-block">{question.getIn(['text','$'],'')} <span className="uk-text-small uk-text-primary">{availableVariables}</span><HelpCompareNumeric/></label>
{ hasChanged && lastAnswer !== '' && (<Badge message={"föregående: " + lastAnswer} hasMath={false} className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"/>)}
          <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
          <div className="uk-form-icon uk-width-1-1">
          { !pending && <i className="uk-icon-pencil"/> }
          { pending && <i className="uk-icon-cog uk-icon-spin"/> }
            <input className={"uk-width-1-1 "} type="text" value={this.state.value} onChange={this.handleChange} ></input>
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
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('compareNumeric', QuestionCompareNumeric);
