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
import HelpLinearAlgebra from './HelpDevLinearAlgebra.jsx';
import MathSpan from '../MathSpan.jsx';
import mathjs from 'mathjs';
import latex from './latex.js';
import immutable, { List } from 'immutable';
import { enforceList } from '../../immutablehelpers.js';
import { throttle } from 'lodash'
import { asciiMathToMathJS, insertCursor, braketify, absify, insertImplicitMultiply, insertImplicitSubscript, fixDelimiters } from '../mathrender/string_parse.js'

export default class QuestionLinearAlgebra extends Component {
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
    this.varProps = {};
    this.varsList = [];
    this.validSymbols = ['pi', 'I', 'e'];
    this.blacklist = [];
    if(this.props.canViewSolution)
      this.state.value = this.props.questionData.getIn(['expression','$'], '').replace(/;/g,'').trim();
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
      if(this.varsList.indexOf(node.name) !== -1 || this.validSymbols.indexOf(node.name) !== -1)
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
      var preParsed = asciiMathToMathJS(insertCursor(asciitext, cursorPos));
      // parsed = insertImplicitMultiply(parsed);
      // parsed = insertImplicitSubscript(parsed);
      // parsed = braketify(parsed);
      // var delimitersFixed = fixDelimiters(parsed);*/
      var parsed = preParsed.out;
      parsed = parsed + ' empty()';
      try {
        var mParsed = mathjs.parse(parsed).toTex({
          parenthesis: 'keep', // The keep options keeps parenthesis from input expression, seems to work best.
          handler: this.customLatex, // Custom latex node handler
        });
        if(typeof mParsed === 'string' && mParsed !== 'undefined') {
          this.lastParsable = mParsed.replace(/\\\\end{bmatrix}/g,'end{bmatrix}'); // MathJS outputs an extra \\ which KaTeX interprets as a new line
        }
        return {out: this.lastParsable, warnings: preParsed.warnings}
      }
      catch(e) {
        return {out: this.lastParsable, warnings: preParsed.warnings, error: "MathJS parse/toTex error"}
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
 
  uniquecat = (a,b) => {
	var c = a.concat(b.filter(function (item) {
    		return a.indexOf(item) < 0;
	})) 
    return c
     };

  //Parse variables and their optional properties
  parseVariables = () => {
    this.varsList = this.parseVariableString(this.props.questionData.getIn(['global','$'], ''));
    var varsListGlobal1 = this.parseVariableString(this.props.questionData.getIn(['global','$'], ''));
    console.log("DEV varsListGlobal=", varsListGlobal1 )
    var varsListGlobal2 =   enforceList( this.props.questionData.getIn(['global','var'], List([]))  ).map(
	item =>  ( item.getIn(['token','$']).trim() ) ).toJS()
    console.log("DEV varsListGlobal2=", varsListGlobal2 )
    var varsListLocal1 = this.parseVariableString(this.props.questionData.getIn(['variables','$'], ''));
    console.log("DEV varsListLocal1=", varsListLocal1)
    var varsListLocal2 = enforceList( this.props.questionData.getIn(['var','token','$'], List([]))).map(
	item => item.trim() ).toJS();
    console.log("DEV varsListLocal2=", varsListLocal2)
    var  varsListUsed = this.props.questionData.get('usedvariablelist',List([])).toJS() ;
    if( varsListUsed.length == 0 ){
	console.log("Length is zero ");
	var correct_answer =  question.getIn(['expression','$'], '').replace(/;/g,'').trim();
 	var caretless = correct_answer;
	console.log("correct_answer = ", correct_answer )
    	caretless = caretless.replace(/[A-Z,a-z,0-9]+\(/g,'(' )
 	console.log("caretless = ", caretless )
	var rx = new RegExp("([A-Z,a-z]+\w*)","g")
	var lis = [];
	var match ;
	while((match = rx.exec(caretless)) !== null){
    		lis.push(match[0] );
		}
	console.log("lis = ", lis )
	varsListUsed = lis;
   	}	
    console.log("DEV varsListUsed =", varsListUsed)
    var varPropsList = enforceList(this.props.questionData.getIn(['global', 'var'], List([])));
    var localVars = enforceList(this.props.questionData.get('var', List([])));
    var allVars = localVars.concat(varPropsList);
    var usethese = this.uniquecat( this.uniquecat( varsListUsed, varsListLocal1 ), varsListLocal2 )
    console.log("usethese = ", usethese )
    this.varsList = usethese;
    for(let v of allVars) {
      if(v.hasIn('token','$')) {
        var parsedVar = insertImplicitSubscript(v.getIn(['token','$'],'').trim()); 
        if( this.varsList.indexOf(parsedVar) == -1) {
          this.varsList.push(parsedVar);
        }
      }
    }
    console.log("this.varsList = ", this.varsList );
    this.varProps = allVars.map( item => ({
      //The token is the key, the other items that are not the token or the special $children$ are added as a map.
      [item.getIn(['token', '$'], '').trim()]: item.filterNot( (val, key) => key === 'token' || key === '$children$' || key === '$').map( val => val.get('$') )
    }) )
    .reduce( (prev, next) => prev.merge(next), immutable.Map({}));
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
    error = "Ett fel uppstod. (Detta kan bero på att du inte är inloggad, om problem kvarstår var vänlig hör av dig.)";

  this.parseBlacklist();
  this.parseVariables();
  var  varsListUsed = this.props.questionData.get('usedvariablelist',List([])).toJS() ;
  var  exposeglobals =  this.props.questionData.get('exposeglobals');
  var localVars = this.parseVariableString(this.props.questionData.getIn(['variables','$'], ''));
  console.log("QUESTION DEV localVars = ", localVars )
  console.log("QUESTION DEV exposeglobals = ", exposeglobals )
  console.log("QUESTION_DEF varsListUsed: ", varsListUsed );
  console.log("QUESTION_DEF this.varsList : ", this.varsList);
  var mathjsEvalVars = {}
  var availableVariables = [];
 if( exposeglobals ){
  	var usethesevars = this.varsList; // THIS WAS THE ORIGINAL; ALL VARIABLE NAMES ARE EXPOSED UNLESS BLACKLISTED
 	} else {
  	usethesevars = varsListUsed.concat( localVars);	    // THIS EXPOSES ONLY VARIABLES IN EXPRESSION
	usethesevars = varsListUsed.concat( localVars.filter( function( item ) {
		return varsListUsed.indexOf( item ) < 0 ; } ) ) // THIS EXPOSES ONLY LOCAL VARIABLES AND THOSE USED
								// EXPLICITLY IN THE variales TAG FOR THE QUESTION
 	}
   if(usethesevars) {
          usethesevars.map( v => {mathjsEvalVars[v] = 1;} );
          availableVariables.push( (<span key="s">(i termer av </span>) );
              var filteredVars = usethesevars.filter(v => typeof v === 'string' && this.blacklist.indexOf(v) == -1).map( v => v.replace(/\_/g,''));
              for(const [i, v] of filteredVars.entries()) {
                  availableVariables.push((<span key={"v"+i}>{v}</span>));
                  if(this.varProps.hasIn([v, 'tex']))
                      availableVariables.push((<span key={"tex"+i}> (<MathSpan message={"$" + this.varProps.getIn([v,'tex']) + "$"}></MathSpan>)</span>));
                  if(i < filteredVars.length - 1)
                      availableVariables.push((<span key={"c"+i}>, </span>));
              }
              availableVariables.push((<span key={"e"}>)</span>));
          //availableVariables = this.varsList.length ? "(i termer av " + this.varsList.filter(v => typeof v === 'string' && this.blacklist.indexOf(v) == -1).map( v => v.replace(/\_/g,'')).join(", ") + ")" : "";
      }
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.
  console.log("availableVariables = ", availableVariables )
  var graderResponse = null;
  var input = this.state.value.trim();
  var hasChanged = input !== lastAnswer;
  var nonEmpty = input !== "";
  var renderedResult = this.renderAsciiMath(this.state.value);
  var renderedMath = renderedResult.out;
  if(input === lastAnswer && lastAnswer !== '' && !error) {
    if(correct)
       graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + " är korrekt."} type="success" key="input" hasMath={true}/>);
    else
      graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + " är inte korrekt."} type="warning" key="input" hasMath={true}/>);
  } else if(input !== ''){
    graderResponse = (<SafeMathAlert className="uk-margin-small-top uk-margin-small-bottom" message={ renderedMath } key="input"/>);
  }
  var mathSizeClass = 'large';
  var sizeActive = 'uk-text-bold';
  switch(this.state.mathSize) {
    case 'small':
      mathSizeClass = 'uk-text-small'; break;
    case 'medium':
      mathSizeClass = ''; break;
    case 'large':
      mathSizeClass = 'uk-text-large'; break;
  }
  return (
        <div className="">
          <label className="uk-form-row uk-display-inline-block">{question.getIn(['text','$'],'')} <span className="uk-text-small uk-text-primary">{availableVariables}</span>
          <span data-uk-tooltip title="Denna fråga är av en ny typ där bland annat vektorer och matriser kan användas. Hör gärna av er om ni stöter på problem."></span>
          <HelpLinearAlgebra/>
          </label>
{ hasChanged && lastAnswer !== '' && (<Badge message={"föregående: " + lastAnswer} hasMath={false} className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"/>)}
          <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
          <div className="uk-width-1-1">
            <textarea className={"uk-width-1-1 "} value={this.state.value} onSelect={this.handleSelect} onChange={this.handleChange} ></textarea>
          </div>
          </div>
          <div className="uk-width-1-6">
            <a onClick={(event) => submit(input)} className={ "uk-width-1-1 uk-button uk-padding-remove " + (nonEmpty && hasChanged && !renderedResult.error ? "uk-button-success" : "")}>
              { pending && <i className="uk-icon-cog uk-icon-spin"/> }
              { !pending && <i className="uk-icon uk-icon-send"/> }
            </a>
            </div>
          </div>
          { error && !hasChanged && <Alert message={error} type="error" key="err"/> }
          { author_error && this.props.isAuthor && <Alert message={author_error} type="error" key="author_error"/> }
        { warning && !hasChanged && <Alert message={warning} type="warning" key="warning"/> }
        <div className="uk-flex">
        <span className={"uk-width-1-1 " + mathSizeClass}>{ graderResponse }</span>
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
        { renderedResult.error && <span className="uk-text-danger">Kontrollera syntax. (Visar senaste fungerande ovan.)</span>}
        { /*mathjsError*/ }
        { renderedResult.warnings.length > 0 && <Alert message={renderedResult.warnings.join(', ')} type="warning" key="renderWarning"/>}
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('linearAlgebra', QuestionLinearAlgebra);

export {absify}
