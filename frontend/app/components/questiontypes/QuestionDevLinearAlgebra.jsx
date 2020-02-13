/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
"use strict"; // It is recommended to use strict javascript for easier debugging
import React, { Component } from 'react'; // React specific import
import PropTypes from 'prop-types';
import { applyshortcuts } from './shortcuts.js'

import { registerQuestionType } from './question_type_dispatch.js' // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import SafeMathAlert from '../SafeMathAlert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from '../Badge.jsx'; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpDevLinearAlgebra from './HelpDevLinearAlgebra.jsx';
import MathSpan from '../MathSpan.jsx';
// import BaseLang from '../BaseLang.jsx';
// import {alttextfunc} from '../BaseLang.jsx';
// import { alttext, translations ,_} from '../alttext.js';
import T from '../Translation.jsx';
import t from '../../translations.js';
import mathjs from 'mathjs';
import latex from './latex.js';
import immutable, { List } from 'immutable';
import { enforceList } from '../../immutablehelpers.js';
import { throttle } from 'lodash'
// import { usethesevariables, parseBlacklist, uniquecat, parseVariableString ,  AvailableVariables} from './mathexpressionparser.js'
import {  uniquecat } from './mathexpressionparser.js'
import { asciiMathToMathJS, insertCursor, braketify, absify, insertImplicitMultiply, insertImplicitSubscript, fixDelimiters } from '../mathrender/string_parse.js'

export default class QuestionDevLinearAlgebra extends Component {
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
    this.unClosed = true;
    this.lastParsable = '';
    this.mathjserror = false;
    this.mathjswarning = '';
    this.varProps = {};
    this.varsList = [];
    this.validSymbols = ['pi', 'I', 'e','xhat','yhat','zhat','t','x','y','z'];
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
    if( node.op == '\''){
      //console.log("QUOTE OPERATOR NODE")
      if ( node.type === 'OperatorNode' ) {
        var child = node.args[0]
        if( child.type == 'SymbolNode'  ){
            if ( this.validSymbols.indexOf( child.name ) < 0  ){
                this.validSymbols.push( child.name )
                }
            }
        return  '{' + child.toTex(options) + '^{\\prime} }'
        }
      return '{' + ( node.args[0].name ).toTex(options)+ '}^{\\prime}';
      }
        
    if(node.type === 'FunctionNode') {
      if ( node.op == '\''){
        //console.log("FUNCTION NODE .. ", node.args[0])
        }
      // Will print in red
      if(node.name === 'fail') {
        this.mathjserror = true;
        this.mathjswarning += " : error1";
        return '\\color{red}{' + node.args[0].value + '}';
      }
      // Will print in small red text
      else if(node.name === 'smalltext') {
        this.mathjserror = true;
        this.mathjswarning += " : error2";
        
        return '\\color{red}{\\text{\\small ' + node.args[0].value + '}}';
      }
      // Will not generate any output but is later used to find unmatched parenthesis
      else if(node.name === 'unclosed') {
        this.mathjserror = true;
        this.mathjswarning += " : unclosed left paren";
        return '';
      }
      else if(node.name === 'empty') {
        return '';
      }
      else if(this.blacklist.indexOf(node.name) !== -1) {
        this.mathjswarning += " : error5";
        this.mathjserror = true;
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
          return "\\left(" + tex0 + "\\right)\\circ";
        }
        if( node.args.length == 2 ){
          var tex0 = node.args[0].toTex(options);
          var tex1 = node.args[1].toTex(options);
          return "\\left(" + tex0 + "\\right)\\circ\\left(" + tex1 + "\\right)";
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
      else if( node.name === 'curl'  ){
        var tex0 = node.args[0].toTex(options);
        var child = node.args[0]
         if ( child.type ==  'SymbolNode' ){
            return '\\nabla \\times ' + tex0 + ''
            }
         else {
            return '\\nabla \\times (' + tex0 + ')'
            }
            
        }
      else if( node.name === 'div'  ){
         var child = node.args[0]
         var tex0 = child.toTex(options);
         if ( child.type ==  'SymbolNode' ){
            return '\\nabla \\circ ' + tex0 + ''
            }
         else {
            return '\\nabla \\circ(' + tex0 + ')'
            }
            
        }
      else if( node.name === 'partial'  ){
        if ( node.args.length == 2  ){
          var tex0 = node.args[0].toTex(options);
          var tex1 = node.args[1].toTex(options);
          return '\\frac{ \\partial ' + tex0 + '}{ \\partial ' + tex1 + '}'
          }
        else if ( node.args.length > 2  ){
          var tex0 = node.args[0].toTex(options);
          node.args.shift()
          var order = node.args.length
          var largs = node.args.map( item => item.toTex(options) )
          var targ = largs.join('\\,\\partial ')
          return '\\frac{ {\\partial}^{' + order + '} '  + tex0 + '}{ \\partial '  + targ + '}'
          }
        }
      
      
      else if( node.name === 'grad'  ){
        var tex0 = node.args[0].toTex(options);
        var child = node.args[0]
         if ( child.type ==  'SymbolNode' ){
            return '\\nabla ' + tex0 + ''
            }
         else {
            return '\\nabla  (' + tex0 + ')'
        }
        //console.log("UNIDENTIFIED FUNCTION NODE ", node.name )
        var ret =  node._toTex(options);
        if( node.name == 'erf'){
            ret = ret.replace(/^erf/,'\\mathrm{erf}') 
            }
        this.isUnclosed = false;
        node.traverse( (node, path, parent) => {
          if(node.type === 'FunctionNode' && node.name === 'unclosed'){
            this.isUnclosed = true;
            // this.mathjswarning += " : unclosed FunctionNode";
            this.mathjserror = true;
            }
        });
        if(this.isUnclosed) {
          this.mathjserror = true;
          this.mathjswarning += " : unclosed function "+ node.name;
          return '\\color{orange}{' +  ret + '}';
          }
        else
          var origVar = node.name
          const texSymbol = this.varProps.hasIn([origVar, 'tex']) ? this.varProps.getIn([origVar, 'tex']) : 
			latex.toSymbol( insertImplicitSubscript( origVar),false);//node._toTex(options);
          return '{' + texSymbol  + '}(  ' +  node.args[0].toTex(options) + ')'
      }
    }
    // Render green if allowed variable otherwise red
    else if(node.type === 'SymbolNode') {
      const origVar = node.name.replace(/\_/g, '');
      // console.log("origVar = ", origVar );
      const texSymbol = this.varProps.hasIn([origVar, 'tex']) ? this.varProps.getIn([origVar, 'tex']) : 
			latex.toSymbol( insertImplicitSubscript( origVar),false);//node._toTex(options);
      // console.log("texSymbol = ", texSymbol , insertImplicitSubscript( origVar )  );
      if(this.blacklist.indexOf(origVar) !== -1) {
        this.mathjswarning += " : disallowed variable";
        this.mathjserror = true;
        return '\\color{orange}{' + texSymbol + '}';
          }
      if(this.varsList.indexOf(origVar) !== -1 || this.validSymbols.indexOf(origVar) !== -1)
        return '\\color{green}{' + texSymbol + '}';
      else 
        this.mathjserror = true;
        this.mathjswarning += " : undefined variable \'" + node.name + "\'";
        return '\\color{red}{' + texSymbol + '}';
    }
    // Special handling for unmatched parenthesis, otherwise render normally
    else if(node.type === 'ParenthesisNode') {
      this.isUnclosed = false;
      node.traverse( (node, path, parent) => {
        if(node.type === 'FunctionNode' && node.name === 'unclosed')
            this.isUnclosed = true;
      });
      if(this.isUnclosed) {
        this.mathjswarning += " : unclosed right paren";
        this.mathjserror = true;
        return '\\color{red}{(} ' + node.content.toTex(options) + '';
      }
      else 
        return ' '+node._toTex(options);
    }
    // Cursor handling by hooking into the bitwise not operator that has a very high precedence.
    else if(node.type === 'OperatorNode') {
      if(node.fn === 'bitNot') {
        if(node.args[0].type === 'ParenthesisNode') {
          this.isUnclosed = false;
          node.args[0].traverse( (node, path, parent) => {
            if(node.type === 'FunctionNode' && node.name === 'unclosed')
              this.isUnclosed = true;
          });
          if(this.isUnclosed) {
            this.mathjswarning += " : unclosed parenthesis of operator ";
            this.mathjserror = true;
            return '\\color{red}{\\left(\\large{\\color{#0f0}{\\underline{\\color{#2d7091}{' + node.args[0].content.toTex(options) + '}}}}\\right.}';
            }
          else
            return '\\left(\\large{\\color{#0f0}{\\underline{\\color{#2d7091}{' + node.args[0].content.toTex(options) + '}}}}\\right)';
        }
        return '\\large{\\color{#0f0}{\\underline{\\color{#2d7091}{' + node.args[0].toTex(options) + '}}}}';
      }
    }
  }

  parseVariableString = (variableString) => {
    var vars = variableString.trim()
      .split(';')
      .filter(str => str !== "")
      .map( str => str.split('=') )
      .map( entry => insertImplicitSubscript(entry[0].trim()) );
      return vars;
  }


  parseVariables = () => {
    this.varsList = this.parseVariableString(this.props.questionData.getIn(['global','$'], ''));
    // Create a map keyed by the variable token containing all its other child elements as a submap for easy indexing
    var varPropsList = enforceList(this.props.questionData.getIn(['global', 'var'], List([])));
    var funcPropsList = enforceList(this.props.questionData.getIn(['global', 'func'], List([])));
    varPropsList = varPropsList.concat( funcPropsList)
    //console.log("varPropsList = ", JSON.stringify( varPropsList) )
    // console.log("funcPropsList = ", JSON.stringify( funcPropsList) )
    var localVars2 = enforceList(this.props.questionData.getIn(['variables','var'], List([])));
    var localVars1 = enforceList(this.props.questionData.getIn(['var'], List([])));
    var localVars = localVars2.concat( localVars1 )
    var allVars = localVars.concat(varPropsList).concat(funcPropsList);
    for(let v of allVars) {
      if(v.hasIn('token','$')) {
        var parsedVar = insertImplicitSubscript(v.getIn(['token','$'],'').trim()); 
        if( this.varsList.indexOf(parsedVar) == -1) {
          this.varsList.push(parsedVar);
        }
      }
    }
    this.varProps = allVars.map( item => ({
      //The token is the key, the other items that are not the token or the special $children$ are added as a map.
      [item.getIn(['token', '$'], '').trim()]: item.filterNot( (val, key) => key === 'token' || key === '$children$' || key === '$').map( val => val.get('$') )
    }) )
    .reduce( (prev, next) => prev.merge(next), immutable.Map({}));
  }



  renderAsciiMath = (asciitext) => {
      
      var cursorComplete = false;
      var cursorPos = this.state.cursor;
      this.mathjserror =  (/(\/|\*|\+|-|\^)\W*$/).test(asciitext)
      this.mathjswarning = this.mathjserror ? "unterminated operator on right" :  ''
      if( (/\s\^/).test(asciitext) ){
           this.mathjserror = true;
           this.mathjswarning += " : interior dangling caret"
        }

      if(cursorPos > asciitext.length)cursorPos = asciitext.length;
      var preParsed = asciiMathToMathJS(insertCursor(asciitext, cursorPos));
      if ( preParsed.warnings  ){
            this.mathjswarning += preParsed.warnings;
            }
      // console.log("preParsed = ", preParsed );
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
        mParsed = mParsed.replace(/prime}~ /g,'prime}');
        mParsed = mParsed.replace(/}~ /g,'}');
        mParsed = mParsed.replace(/\\left\(/g,'(')
        mParsed = mParsed.replace(/\\right\)/g,')')
        // console.log("mParsed = ", mParsed )
        if(typeof mParsed === 'string' && mParsed !== 'undefined') {
          this.lastParsable = mParsed.replace(/\\\\end{bmatrix}/g,'end{bmatrix}'); // MathJS outputs an extra \\ which KaTeX interprets as a new line
        }
        return {out: this.lastParsable, warnings: preParsed.warnings}
      }
      catch(e) {
        this.mathjswarning = " : Unparsable  " + ( this.mathswarning ? this.mathjswarning :  '' )
        return {out: this.lastParsable, warnings: preParsed.warnings, error: "MathJS parse/toTex error"}
      }
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
  var question = this.props.questionData;
  var state = this.props.questionState;
  var submit = this.props.submitFunction;
  var pending = this.props.questionPending;
  // var lang = this.props.lang;
  if ( state.getIn(['response','question'] ) ) { question = state.getIn(['response','question']) }

  
  /* Both the questionData and questionState are of type Map from immutable.js. They are nested dictionaries that are accessed via the get and getIn functions. For example question.get('text') retrieves <question> <text> * </text> </question>. Deeper structures can be accessed with getIn, for example question.getIn(['tag1', 'tag2']) would retrieve <question> <tag1> <tag2> * </tag2> </tag1> </question>. */

  // System state data
  var lastAnswer = state.getIn(['answer'], ''); // Last saved answer in database, same format as passed to the submitFunction
  //var correct = state.getIn(['response','correct'], Null) || state.getIn(['correct'], Null); // Boolean indicating if the grader reported correct answer
 var correct = state.getIn(['response','correct'], null ) || state.getIn(['correct'], null ); // Boolean indicating if the grader reported correct answer
 var correct = state.getIn(['response','correct'], false) || state.getIn(['correct'], false); // Boolean indicating if the grader reported correct answer
  var n_attempts = state.getIn(['response','n_attempts'] , question.getIn(['n_attempts']) ) 
  var used_variable_list =   state.getIn(['response','used_variable_list'] , question.getIn(['used_variable_list']) ) 
  var previous_answers = state.getIn(['response','previous_answers'] , question.getIn(['previous_answers']) );
  if( state.getIn(['correct'], null ) == null ){
       var feedback = false
        } else {
       var feedback = true
     }
  // console.log("feedback = ", feedback)

  //console.log("N_ATTEMPTS = ", n_attempts)
  // console.log(" E user ", state.getIn(['user'],"DEF"));
  // console.log(" F question ", state.getIn(['question'],"DEF"));

  var latex = state.getIn(['response','latex'], ''); // Custom field containing the latex code obtained from SymPy.
  var error = state.getIn(['response','error']); // Custom field containing error information
  var author_error = state.getIn(['response','author_error']); // Custom field containing error information
  var warning = state.getIn(['response','warning']); // Custom field containing error information
  var status = state.getIn(['response','status'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
  var comment = state.getIn(['response','comment'],'');
  var tdict = state.getIn(['response','dict'],'');
  // console.log("dict = ", tdict )
  //console.log("COMMENT = ", comment)
    if(state.getIn(['response','detail']))
    error = "Ett fel uppstod. (Detta kan bero på att du inte är inloggad, om problem kvarstår var vänlig hör av dig.)";

  //console.log(" E question  n_attempts = ", question.getIn(['n_attempts'],97) );
  // console.log("usedvariablelist = ", JSON.stringify( question.getIn(['usedvariablelist'] ,[]) ));
  //console.log("F username = ", question.getIn(['username'],'NOUSERSET') )

  this.parseBlacklist();
  this.parseVariables();
  var mathjsEvalVars = {}
  // console.log("this.varsList = ", JSON.stringify( this.varsList))
  this.varsList = uniquecat(used_variable_list, this.varsList)
  this.varsList = used_variable_list
  // console.log("used_variable_list = ", JSON.stringify( used_variable_list))
  var availableVariables = [];
  var comma = ''
    if(this.varsList && this.varsList.size > 0 ) {
      this.varsList.map( v => {mathjsEvalVars[v] = 1;} );
      var filteredVars = this.varsList.filter(v => typeof v === 'string' && this.blacklist.indexOf(v) == -1).map( v => v.replace(/\_/g,''));
      // if(filteredVars.length > 0) { */
      availableVariables.push( (<span key="s">(<T>in terms of</T> </span>) );
      // } */
          for(const [i, v] of filteredVars.entries()) {
            availableVariables.push(<span key={'s1' + i }><span key={'s2' + i } >{comma}</span><span key={"v"+i} className='termsof' >{v}</span></span>);
            comma = ','
            if(this.varProps.hasIn([v, 'tex']))
              availableVariables.push((<span key={"tex"+i}> (<MathSpan message={"$" + this.varProps.getIn([v,'tex']) + "$"}></MathSpan>)</span>));
            if(i < filteredVars.length - 1)
              availableVariables.push((<span key={"c"+i}>, </span>));
          }
        //  if(filteredVars.length > 0)
        availableVariables.push((<span key={"e"}>)</span>));
    }
  // HTML output defined as JSX code: Contains HTML entities with className instead of class and with javascript code within curly braces.
  // The styling classes are from UIKit, see getuikit.com for available elements.






  //this.varsList = res['varsList'];
  //this.varProps = res['varProps'];
  //this.varsList = usethesevariables( question)
  // console.log("QUESTION_DEV this.varsList = ", this.varsList )
  var graderResponse = null;
  var untrimmed_input = this.state.value;
  untrimmed_input = applyshortcuts( untrimmed_input);
  var input = untrimmed_input.trim();
  var hasChanged = input !== lastAnswer;
  var nonEmpty = input !== "";
  var renderedResult = this.renderAsciiMath(input);
  // console.log("renderedResult = ", renderedResult )
  var renderedMath = renderedResult.out;
  var unchecked = '('+t('unchecked')+')';
  if(input === lastAnswer && lastAnswer !== '' && !error) {
   if( feedback ){
    if(correct) {
     //  graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + " är korrekt."} type="success" key="input" hasMath={true}/>);
 graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + 
                t(' is correct.') + t(comment,tdict) } type="success" key="input" hasMath={true}/>);
    if( n_attempts < 2 ){
            graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + 
                t('CORRECT FIRST TIME!')  + t(comment,tdict) } type="success" key="input" hasMath={true}/>);
            }
            
    } 
    else if( correct === null ){
              graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$ " + t("unchecked")} key="input" hasMath={true}/>);
        }
    else {
      // graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + " är inte korrekt."} type="warning" key="input" hasMath={true}/>);
    graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + t(' is not correct.') + t(comment,tdict) } type="warning" key="input" hasMath={true}/>);
    if( n_attempts > 4  && ( n_attempts % 2 ) == 0 ){
        graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$" + t(' is not correct.') + t(comment,tdict)  + t(' STOP GUESSING!') } type="warning" key="input" hasMath={true}/>);
        
        }
            
       }
     } else {
        graderResponse = (<Alert className="uk-margin-small-top uk-margin-small-bottom" message={"$" + renderedMath + "$"  + unchecked + t(comment,tdict) } type="text" key="input" hasMath={true} /> );

     
    }


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
  var questiontext = this.props.renderText(question.getIn(['text']));
  var questionkey = question.getIn(['@attr', 'key']);
  var msg1 = "Denna fråga är av en ny typ där bland annat vektorer och matriser kan användas. Hör gärna av er om ni stöter på problem."
  var questionkey = question.getIn(['@attr','key'])
  // console.log("mathjserror = ", this.mathjserror)
  // console.log("hasChanged = ",  hasChanged )
  var msg = ''
  if( renderedResult.error ){
        this.mathjswarning = " : Unparsable " + this.mathjswarning;
        this.mathjserror = true;
        }
  if( hasChanged  ) {
        msg = this.mathjserror ? this.mathjswarning :  'Syntax OK'
    }
  var showinstructions = ( input == '' )
  return (
        <div className="">
        <MathSpan>{questiontext}</MathSpan>
		<span className="uk-text-small uk-text-primary">{availableVariables}</span>
  	  <span className="uk-text-small uk-text-primary"> [  {feedback} {n_attempts } <T>attempts</T> ]  </span>
          { ! showinstructions && <HelpDevLinearAlgebra msg={msg}/>  }
          {  showinstructions &&  <HelpDevLinearAlgebra /> }
	   <span data-uk-tooltip title={msg1}></span>
{ hasChanged && lastAnswer !== '' && (<Badge message={t('previous') + '  '  + lastAnswer} hasMath={false} className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"/>)}
          <div className="uk-grid uk-grid-small">
          <div className="uk-width-5-6">
          <div className="uk-width-1-1">
            <textarea id={questionkey} className={"uk-width-1-1 "} value={this.state.value} onSelect={this.handleSelect} onChange={this.handleChange} ></textarea>
          </div>
          </div>
          <div className="uk-width-1-6">
            <a onClick={(event) => submit(input)} className={ "uk-width-1-1 uk-button uk-padding-remove " + (nonEmpty && hasChanged && !renderedResult.error  && ! this.mathjserror ? "uk-button-success" : "")}>
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
         { ! this.isUnclosed && renderedResult.error && <span className="uk-text-danger"> {t('check syntax') } </span> }
        { /*mathjsError*/ }
        { renderedResult.warnings.length > 0 && <Alert message={renderedResult.warnings.join(', ')} type="warning" key="renderWarning"/>}
        </div>
  );
}
}

//Register the question component with the system
registerQuestionType('devLinearAlgebra', QuestionDevLinearAlgebra);
registerQuestionType('symbolic', QuestionDevLinearAlgebra);

export {absify}
