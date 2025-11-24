// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
'use strict'; // It is recommended to use strict javascript for easier debugging
import React, { Component } from 'react'; // React specific import
import ChatIcon from '../ChatIcon.jsx'
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import * as p from '../parse_latex.js';
import { external_renderAsciiMath } from './renderAsciiMath';
import Cookies from 'universal-cookie';
import { getcookie } from '../../cookies.js';
import { external_parseVariableString, external_parseVariables, external_parseBlacklist } from './parseVariables';
import { newcustomLatex } from './customLatex';

import { registerQuestionType } from './question_type_dispatch.jsx'; // Register function used at the bottom of this file to let the system know of the question type
import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import MathJaxSpan from '../MathJaxSpan.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Spinner from '../Spinner.jsx';
import SafeMathAlert from '../SafeMathAlert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
import Badge from '../Badge.jsx'; // Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpDevLinearAlgebra from './HelpDevLinearAlgebra.jsx';
import MathSpan from '../MathSpan.jsx';
import { ParsedBox } from './ParsedBox.jsx';
import T from '../Translation.jsx';
import t from '../../translations.js';
//import latex from './latex.js';
import immutable from 'immutable';
import { enforceList } from '../../immutablehelpers.js';
import { throttle } from 'lodash';
import { create, all } from 'mathjs';
const math = create(all);

var unstableKey = 93;
const nextUnstableKey = () => unstableKey++;

import { uniquecat } from './mathexpressionparser.jsx';
import { insertImplicitSubscript } from '../mathrender/string_parse.js';

class Timer extends React.Component {
  state = { seconds: 0 };
  intervalId = null;

  componentDidMount() {
    this.intervalId = setInterval(() => {
      this.setState((prev) => ({ seconds: prev.seconds + 1 }));
    }, 1000);
  }

  componentWillUnmount() {
    clearInterval(this.intervalId);
  }

  render() {
    return <button className="uk-button-primary"  style={{ margin: '8px 8px' }}>{this.state.seconds}s</button>;
  }
}


class QuestionDevLinearAlgebra extends Component {
  static propTypes = {
    feedback: PropTypes.bool,
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    //questionPending: PropTypes.oneOfType([PropTypes.bool,PropTypes.string]), // Indicates when we are waiting for a server response
    questionPending: PropTypes.bool,
    answerPending: PropTypes.string,
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool, //Indicates if user is allowed to see solution.
    questionkey: PropTypes.string,
    isSuperUser: PropTypes.bool,
  };

  constructor(props) {
    super(props);
    math.import({ ln: math.log });
    this.state = {
      value: this.props.canViewSolution ?  
	    ( this.props.questionData.getIn(['expression', '$'], '').replace(/;/g, '').trim()  ) : 
	    ( this.props.questionState.getIn(['answer'], '') ),
      cursor: 0,
      nrenders: 0,
      last_input : '',
      mathSize: 'medium',
      question: this.props.questionData ,
      response: 'RESPONSE',
      nresponse: 0,
      nclicks: 0,

    };
    this.unClosed = true;
    this.lastParsable = '';
    this.mathjserror = false;
    this.mathjswarning = '';
    this.varProps = {};
    this.varsList = undefined;
    this.validSymbols = ['pi', 'I', 'e', 'xhat', 'yhat', 'zhat', 't', 'x', 'y', 'z'];
    this.blacklist = [];
    this.parse_dispatch = {
      "'": p.prime
    };
    for (var item in p) {
      this.parse_dispatch[item.toString()] = p[item.toString()];
    }
  }
  handleChange = (event) => {
    if (!event.target.value.match(/^[0-9a-zA-Z \?\n\*\\^\[\]\)\(,\.=\-\+\/\'\!\|\b]*$/)) {
      //alert("illegal character in " + event.target.value )
      this.setState({ value: this.state.value + '?' });
    } else {
      this.setState({ value: event.target.value });
    }
  };
  handleIncrement= (event) => {
	  this.setState({nclicks: this.state.nclicks + 1 })
    var n = this.state.nresponse + 1
    if ( n >=  event ){
    	    n = event  - 1 
    }
    if ( n < 0 ){ n = 0 ; }
    this.setState({ nresponse: n });
  };

  handleDecrement= (event) => {
    this.setState({nclicks: this.state.nclicks + 1 })
    var n = this.state.nresponse - 1
    if ( n < 0 ) { n = 0 }
    this.setState({ nresponse: n  })
  };



  updateCursor = (pos) =>
    throttle((pos) => {
      this.setState({ cursor: pos });
    }, 500);

  tupdateCursor = (pos) =>//
    throttle((pos) => {
      this.setState({ cursor: pos });
    }, 500);

  handleSelect = (event) => {
    this.updateCursor(event.target.selectionStart);
  };

  setMathSize = (sizeStr) => {
    this.setState({ mathSize: sizeStr });
    var cookies = new Cookies();
    cookies.set('mathSize', sizeStr, { path: '/', secure: true , sameSite: 'none', }); // LEGACY and forces a redraw
  };

  customLatex = (node, options) => {
    return newcustomLatex(node, options, this);
  };
  parseVariableString = (variableString) => {
    return external_parseVariableString(variableString, this);
  };
  parseVariables = () => {
    return external_parseVariables(this);
  };
  parseBlacklist = () => {
    return external_parseBlacklist(this);
  };

  // newrenderAsciiMath = throttle( (asciitext,ignore_undefined=false ) => this.oldrenderAsciiMath( asciitext,ignore_undefined), 500 )
  //renderAsciiMath =  (asciitext,ignore_undefined=false ) => this.oldrenderAsciiMath( asciitext,ignore_undefined)

  /* render gets called every time the question is shown on screen */
  render() {
    var questionkey = this.props.questionkey;
    var question = this.state.question
    var answerbox = question.getIn(['@attr', 'answerbox'], true);
    var notanswerbox = false;
    this.state.nrenders = this.state.nrenders + 1 
    if (answerbox == 'false' || answerbox == 'False') {
      answerbox = false;
      notanswerbox = true;
    } else {
      answerbox = true;
      notanswerbox = false;
    }

    if ( querypath != null ){
	    querypath = querypath.replace(/ /g, "");
    		}

    var precision = question.getIn(['@attr', 'precision'], 0);
    var state = this.props.questionState;
    var querypath = state.getIn(['response', 'querypath','$'], question.getIn(['querypath','$'], null));
    if ( querypath != null ){
	    querypath = querypath.replace(/ /g, "");
    		}
    var exerciseKey = this.props.exerciseState.getIn(['exercise_key'],null) 
    var questionKey = state.getIn(['response', '@attr','key'], question.getIn(['@attr','key'], null));
    if ( querypath ){
    	    querypath = querypath + '/' + this.props.exerciseKey.substring(0,7) + questionKey
    	    querypath = "./django_ragamuffin/query/" + querypath
     }
    var submit = this.props.submitFunction;
    var locked = this.props.locked;
    var pending = this.props.questionPending;
    var answerPending = this.props.answerPending;
    var pendingData = this.props.answerPending;
    var proposed_input = this.props.questionState.getIn(['answer'], '');
    if (this.props.canViewSolution && this.state.nrenders < 4) {
      proposed_input = this.props.questionData.getIn(['expression', '$'], '').replace(/;/g, '').trim();
    }
    if ( pending ){
	    proposed_input =  answerPending + '   ... waiting'
    }

    this.state.renders = this.state.nrenders + 1
    var lastAnswer = state.getIn(['answer'], ''); 
    var correct = state.getIn(['response', 'correct'], null) || state.getIn(['correct'], null); 
    var n_attempts = state.getIn(['response', 'n_attempts'], question.getIn(['n_attempts'], 0));
    var used_variable_list = question.getIn(['used_variable_list'], []);
    var previous_answers = state.getIn(
      ['response', 'previous_answers'],
      question.getIn(['previous_answers'], immutable.Map({}))
    );
    var feedback = this.props.feedback;
    var previous_filtered  = previous_answers.filter( item => item.grader_response != "null" )
    var previousList =  previous_filtered
      .map((item) => (
        <tr key={'prev-' + nextUnstableKey()}>
          <td> {item.getIn(['correct']) == null ? 'null' : item.getIn(['correct']).toString()} </td>
          <td> {item.getIn(['answer']).toString()} </td>
        </tr>
      ))
      .toList();
    var nprevious = previous_filtered.size
    var allow_ai = this.props.exerciseState.getIn(['meta','allow_ai']) || this.props.isAuthor
    var latex = state.getIn(['response', 'latex'], ''); // Custom field containing the latex code obtained from SymPy.
    var student_error = state.getIn(['response', 'error'], null); // Custom field containing error information
    var deltat = state.getIn(['response','deltat'], state.getIn(['deltat'], null)  )
    var author_error = state.getIn(['response', 'author_error'], null); // Custom field containing error information
    var warning = state.getIn(['response', 'warning'], null); // Custom field containing error information
    var default_warning = correct ? t("python returns correct") : t("python return incorrect")
    if ( notanswerbox ){
	 var warning = state.getIn(['response', 'warning'], default_warning ); // Custom field containing error information
    }
	  

    var status = state.getIn(['response', 'status'], 'none'); // Custom field containing the overall status of the answer, corresponds to the css class map inputClass above
    var backend_comment = state.getIn(['response', 'comment'], '');
    if (warning) {
      var myarr = warning.split('info:'); // FIXME
      var comment = myarr[0];
      if (myarr.length > 1) {
        var warning = myarr[1];
      } else {
        var warning = null;
      }
    }
    var tdict = state.getIn(['response', 'dict'], '');
    if (state.getIn(['response', 'detail'])) {
      student_error =
        'An error occur. Perhaps you are not logged in. If this persists, contact admin';
    }

    this.parseBlacklist();
    this.parseVariables();
    var mathjsEvalVars = {};
    if (used_variable_list) {
      try {
        this.varsList = uniquecat(used_variable_list, this.varsList); // .map( n => n.replace('_','') )
      } catch (error) {
      }
    }

    var availableVariables = [];
    var varsListMissing = undefined === this.varsList;
    var comma = '';
    if (!varsListMissing && this.varsList.size > 0 ) {
      this.varsList.map((v) => {
        mathjsEvalVars[v] = 1;
      });
      var filteredVars = used_variable_list
        .filter((v) => typeof v === 'string' && this.blacklist.indexOf(v) == -1)
        .map((v) => v.replace(/\_/g, ''));
      availableVariables.push(
        <span  className={"termsof"}key={'s' + questionkey}>
          (<T>in terms of</T>{' '}
        </span>
      );
      for (const [i, v] of filteredVars.entries()) {
        availableVariables.push(
          <span key={'s1' + i + questionkey}>
            <span key={'s2' + i + questionkey}>{comma}</span>
            <span key={'v' + i + questionkey} className={"termsof"}>
              {v}
            </span>
          </span>
        );
        comma = ',';
        if (this.varProps.hasIn([v, 'tex'])) {
          availableVariables.push(
            <span key={'tex' + i + questionkey}>
              {' '}
              (<MathSpan message={'$' + this.varProps.getIn([v, 'tex']) + '$'}></MathSpan>)
            </span>
          );
        }
        //if(i < filteredVars.length - 1)
        // availableVariables.push((<span key={"c"+i}>, </span>));
      }
      availableVariables.push(<span key={'e' + questionkey}>)</span>);
    }
    if( ! answerbox || question.getIn(['used_variable_list'],[]) == [] ){
      availableVariables = '';
    }


    var graderResponse = null;
    var nresponse = this.state.nresponse
    var nprevious = previous_filtered.size
  
    var untrimmed_input = this.props.questionState.getIn(['answer'], '');
    var input = untrimmed_input.trim();
    var proposed_input = input
    if ( pending ){
	    proposed_input =  answerPending + '   ... waiting'
    }
    this.state.last_input = input
    lastAnswer = lastAnswer.trim();
    var firstChar = lastAnswer[0]
    var nomath = ( firstChar == '?' && allow_ai )
    var domath = ! nomath ;

    var hasChanged = input !== lastAnswer;
    var p = previous_filtered.toJS() 
    var nonEmpty = input !== '';
    var stype = 'success'

    var old_correct = ''
    if ( typeof nprevious == 'undefined' ){
            var nprevious = 0
    }
//console.log("NRESPONSE = ", nresponse )
//console.log("NPREVIOUS = ", nprevious )
//console.log("hasChanged = ", hasChanged)
//console.log("input = ", input )    //var renderedResult = this.renderAsciiMath(input);
//console.log("old_correct = ", old_correct)
var danger = 'error'
 var isai = false
 if (   nprevious > 0  && ! hasChanged ) {
	    console.log("INNER LOOP")
            stype = danger
	    var comment  = comment ?? '';
            old_correct = ''
            warning = null;
            student_error = null
            var g = JSON.parse(p[nresponse].grader_response);
	    console.log("G = ", g )
            proposed_input = p[nresponse].answer
            input = proposed_input
            try {
		  warning =  g.warning 
	      }  catch ( err ) {
                warning = ''
            }
           var isai =  /^\w*\?/.test( input )
           if ( 'correct' in g ){ correct = g.correct 
           } else if ( 'correct'  in p[nresponse] ){
                correct = p[nresponse].correct
                }
	    console.log("CORRECT1", correct , "OLD_CORRECT = ",old_correct)
            if ( correct ){
                    old_correct = '\\text{  is correct }'
                    stype = 'success'
            } else if ( nresponse > 0 ) {
                    old_correct = '\\text{  is not correct}'
                    stype = danger
            }
	    console.log("CORRECT2", correct , "OLD_CORRECT = ",old_correct)

            if ( isai ) {
                comment = g.comment;
                 }
            if ( comment.trim() == '<p></p>' ){
                    comment = '' 
            }
	    console.log(nresponse, "CORRECT3", correct , "OLD_CORRECT = ",old_correct)
            if ( 'error' in g ){
                    student_error = g.error
                    stype = danger
            }
            if ( 'error' in p[nresponse] ){
                    student_error = p[nresponse].error
                    stype = danger
            }

	if ( g.type == 'pythonic' && warning != ''  ){
		comment =  warning;
		warning = null
		}
	    //comment = g.comment
	    //if ( ! comment  ) {
		//    var comment = 'comment = no comment' + 'warning = ' + String( warning  )
	    // }
            //console.log("WARNING = ", warning)
            //console.log("COMMENT = ", comment)
            //console.log("CORRECT = ", correct)
            //if ( warning ) {
        //          comment = ''
          //  }
//
            //console.log("INPUT = ", input )
            var firstChar = input[0]
            var nomath = ( firstChar == '?')
            var domath = ! nomath ;
 }
if ( warning  && domath ){
 var [head, tail] = warning.split("::");
 //console.log("HEAD = ", head, "TAIL = ", tail )
 var [ subhead, subtail] = head.split("info");
 subhead = t( subhead);
 head = subhead + ' info:' + subtail
 //console.log("TRANSLATED HEAD = ", head )
 if ( tail ){
 warning = head + " " + tail;
 }
}
//console.log("STUDENT_ERROR", student_error)
//console.log("WARNING ", warning )
//console.log("COMMENT", comment )
//console.log("G nklicks ", this.state.nclicks)
//console.log("G proposed_input", proposed_input)
//console.log("G NRESPONS = ", nresponse)
//console.log("G CORRECT = ", correct )
//console.log("G WARNING = ", warning )
//console.log("G COMMENT = ", comment )
//console.log("G OLD_CORRECT = ", old_correct)
//console.log("G STYPE = ", stype)
//console.log("G STUDENT_ERROR " , student_error )
//console.log("G DOMATH" , domath)
//console.log("G NOMATH", nomath )
//console.log("G INPUT ", input )
if( comment ){
comment = comment.replace(/\\iff/g, "\\Leftrightarrow"); 
comment = comment.replace(/\\\[/g,'<p style="text-align: center;">$$');
comment = comment.replace(/\\\]/g,'$$</p>' );
comment = comment.replace(/\\operatorname\{([^}]*)\}/g, "\\textstyle{$1}");
comment = comment.replace(/\\boldsymbol/g, "\\mathbf");  
  }




  nprevious = Math.max(nprevious,1)    
  var renderedResult = external_renderAsciiMath(input, this);
    var renderedMath = renderedResult.out;
    renderedMath  = renderedMath + String( old_correct )
    //console.log("RENDERED MATH = ", renderedMath )
    var syntaxerror = renderedResult.syntaxerror;
    var unchecked = '(' + t('unchecked') + ')';
    var iscorrect = t('   is correct. ');
    var firsttime = t(' CORRECT FIRST TIME. !');
    if ( domath && backend_comment ){
            iscorrect = t( backend_comment );
            firsttime = t( backend_comment ) + t(" FIRST TIME!")
    }

    if ( nomath && backend_comment ){
            iscorrect = backend_comment ;
            firsttime = backend_comment + t(" FIRST TIME!")
    }

    if ( answerbox && comment) {
      iscorrect = t(' is mathematically correct but see comment above.');
      stype = 'warning';
      firsttime = t(' is mathematically correct but see comment above.');
    } ;

   if ( ! answerbox ){
      iscorrect = '';
      stype = correct ? 'success' : danger;
      firsttime = '';
         }
   if (domath ){
    if ( ! answerbox || ( input === lastAnswer && lastAnswer !== '' && !student_error) ) {
      if (feedback) {
        if (correct) {
          graderResponse = (
            <Alert
              id={'id1'}
              className="uk-margin-small-top uk-margin-small-bottom yescorrect "
              message={'$' + renderedMath + '$  ' + iscorrect}
              type={stype}
              key={'input1' + questionkey}
              hasMath={true}
            />
          );
          if (n_attempts < 2) {
            graderResponse = (
              <Alert
                id={'id2'}
                className="uk-margin-small-top uk-margin-small-bottom firstcorrect yescorrect"
                message={'$' + renderedMath + '$' + firsttime}
                type={stype}
                key={'input2' + questionkey}
                hasMath={true}
              />
            );
          }
        } else if (correct === null) {
          graderResponse = (
            <Alert
              id={'id3'}
              className="uk-margin-small-top uk-margin-small-bottom isunchecked "
              message={'$' + renderedMath + '$ ' + ' ' + t('unchecked')}
              key={'input3' + questionkey}
              hasMath={true}
            />
          );
        } else {
          graderResponse = (
            <Alert
              id={'id4'}
              className="uk-alert-danger uk-margin-small-top uk-margin-small-bottom nocorrect"
              message={'$' + renderedMath + '$' + ' ' + t(' is not correct.')}
              type="error"
              key={'input5' + questionkey}
              hasMath={true}
            />
          );
          if (n_attempts > 6 && n_attempts % 2 == 0) {
            graderResponse = (
              <Alert
                id={'id5'}
                className="uk-alert-danger uk-margin-small-top uk-margin-small-bottom nocorrect"
                message={'$' + renderedMath + '$' + ' ' + t(' is still not correct.')}
                type="error"
                key={'input6' + questionkey}
                hasMath={true}
              />
            );
          }
        }
      } else {
        graderResponse = (
          <Alert
            id={'id6'}
            className="uk-margin-small-top uk-margin-small-bottom isunchecked "
            message={'$' + renderedMath + '$' + unchecked}
            type="text"
            key={'input7' + questionkey}
            hasMath={true}
          />
        );
      }
    } else if (input !== '') {
      graderResponse = (
        <SafeMathAlert
          className="uk-margin-small-top uk-margin-small-bottom hassyntaxerror"
          message={ renderedMath}
          type={stype}
          key={'input8' + questionkey}
        />
      );
    }
  } else {

      graderResponse = (
        <Alert
          className="uk-margin-small-top uk-margin-small-bottom hassyntaxerror"
          message={input }
          key={'input9' + questionkey}
        />
      );
    }
    var mathSizeClass = 'uk-text-medium';
    var sizeActive = 'uk-text-bold';
    var mathSize = getcookie('mathSize');
    if (mathSize.length == 0) {
      mathSize = ['medium'];
    }

    mathSize = mathSize[0];
    switch (mathSize) {
      case 'small':
        mathSizeClass = 'uk-text-small';
        break;
      case 'medium':
        mathSizeClass = 'uk-text-medium';
        break;
      case 'large':
        mathSizeClass = 'uk-text-large';
        break;
    }
    var pcorrect = state.getIn(['response', 'correct'], null) || state.getIn(['correct'], null); 
    var alerttype = correct ? "success" : "error"
    var qt = question.getIn(['text'])
    var questiontext = this.props.renderText(qt);
    var questionkey = question.getIn(['@attr', 'key']);
    var msg1 = t('This question is of a type where vectors and matrices can be used.');
    var questionkey = question.getIn(['@attr', 'key']);
    var msg = '';
    if ( renderedResult ){
    if (renderedResult.error) {
      this.mathjswarning = ' : Unparsable ' + this.mathjswarning;
      this.mathjserror = true;
    }}
    if (hasChanged) {
      msg = this.mathjserror ? this.mathjswarning : 'Syntax OK';
    }
    var showinstructions = input == '';
    var keyDOM = 'tab-' + nextUnstableKey(); 
    var previousDOM = (
      <table key={keyDOM}>
        <tbody>{previousList}</tbody>
      </table>
    );
    this.mathSizeClass = mathSizeClass;

    if (precision == 0) {
      var precision_string = '';
    } else {
      var precision_string = "precision = " + precision
    }
    var sendicon = 'uk-icon uk-icon-send sendicon uk-text-success'
    var resultkey = correct ? "yescorrect" : ""
    return (
  
      <div key={'devv' + questionkey + nextUnstableKey()} className="uk">
	{ allow_ai && answerbox && querypath && allow_ai && ( 
	    <ChatIcon title="If you want to ask question about your submission, start a query with a questionmark. It knows about your previous answer attempts. "/>
	    )}
      { this.props.isAuthor && querypath && ( 
	    <span> <a href={querypath}> Edit aibased data </a></span>
	    )} 

        <MathSpan> {questiontext}</MathSpan>
        <span className="uk-text-small uk-text-primary">
          {availableVariables} {precision_string}{' '}
        </span>
        {n_attempts > 0 && (
          <span className="uk-text-small uk-text-primary">
            {' '}
            [ {n_attempts} <T>attempts</T> ]{' '}
          </span>
        )}
        { this.props.isSuperUser && deltat  && (
          <span className="uk-text-small uk-text-primary">
            [ {deltat} {' ms'}  ]
          </span>
        )}

        {/*  showinstructions &&  ( <HelpDevLinearAlgebra msg={previousDOM} />   ) */}
        { previous_filtered.size > 0  && (
                <HelpDevLinearAlgebra msg={previousDOM} />)
          }
        <span data-uk-tooltip title={msg1}></span>
        { !pending && hasChanged && lastAnswer  && (
          <Badge
            message={t('previous') + '  ' + lastAnswer}
            hasMath={false}
            className="uk-text-small uk-margin-small-left uk-margin-bottom-remove"
          />
        )}
        {this.props.canViewSolution && <span className="uk-display-inline uk-button"> {this.state.value} </span>}
        <div className="uk-grid uk-grid-small">
          <div className="uk-width-1-1">
            {!locked && answerbox && (
              <div className="uk-width-1-1">
                    {nprevious - nresponse - 1 }
                            { nprevious > 0 && (
            <div key={'buttons' + nresponse} className="uk-button-group">
            <button onClick={(event) => {this.handleIncrement(nprevious) } } className={ 'uk-button'  } >
              <i className="uk-icon uk-icon-arrow-up" /> </button>
            </div> )} 

                <ParsedBox
                  questionkey={questionkey}
                  pending={pending}
                  locked={locked}
                  submit={submit}
                  thiss={this}
                  input={proposed_input}
		  allow_ai={allow_ai}
                /> {nprevious - nresponse - 1 }
                  { nprevious > 0 && (
            <button onClick={(event) => {this.handleDecrement(nprevious)} } className={ 'uk-button'  } >
              <i className="uk-icon uk-icon-arrow-down" /> </button>
             )}

              </div>
            )}
          { ! answerbox && (
              <div className="uk-text-left uk-width-1-1">
            <a onClick={(event) => submit(" ")} className={'uk-button click-send'}>
              <i qkey={questionkey} className={sendicon} />
            </a>
		  

          </div>
          )
        }

          </div>
        </div>
        {author_error && this.props.isAuthor && (
          <Alert id={'ide2'} message={  author_error} type="danger" key={'author_error' + questionkey} />
        )}
        {comment && !hasChanged && isai  && (
	<MathJaxSpan id={'ide3'} html={comment} />
        )}
	{comment && !hasChanged && ! isai  &&  (

          <Alert
            id={'ide3'}
            className={'uk-padding-remove uk-text ' + this.mathSizeClass + ' ' + resultkey }
            message={  comment}
            type={stype}
            key={'comment' + questionkey}
          />
		
        )}
        {warning && !hasChanged && (
          <Alert
            id={'ide4'}
            className={'uk-padding-remove uk-text ' + this.mathSizeClass}
            message={ warning}
            type="warning"
            key={'warning' + questionkey}
          />
        )}
        { ( ! pending && lastAnswer ) && (
          <div className="uk-flex">
            <span qkey={'ready-' + questionkey} className={'uk-width-1-1 ' + mathSizeClass}>
              {' '}
              {graderResponse}{' '}
            </span>
          </div>
        )}

        { (  pending ) && (
          <div className="uk-flex">
            <span qkey={'ready-' + questionkey} className={'uk-width-1-1 ' + mathSizeClass}>
                <Timer/>
                <Spinner msg={'wait up to 4 minutes:' + answerPending.replace(/^\w*\?/,'') } size='uk-icon-small' />
            </span>
          </div>
        )}


        <div className="uk-float-right uk-flex">
          <div className={'uk-text-small uk-margin-small-left ' + (mathSize === 'small' ? sizeActive : '')}>
            <a onClick={() => this.setMathSize('small')}>A</a>
          </div>
          <div className={'uk-margin-small-left ' + (mathSize === 'medium' ? sizeActive : '')}>
            <a onClick={() => this.setMathSize('medium')}>A</a>
          </div>
          <div className={'uk-text-large uk-margin-small-left ' + (mathSize === 'large' ? sizeActive : '')}>
            <a onClick={() => this.setMathSize('large')}>A</a>
          </div>
        </div>
        {!varsListMissing && syntaxerror && !this.isUnclosed && renderedResult.error && (
          <span className="uk-text-danger"> DevLin {t('check syntax')} </span>
        )}
        {/*mathjsError*/}
        {student_error && !hasChanged && (
          <Alert id={'ide1'} hasMath={false} message={student_error} type="error" key={'err' + questionkey} />
        )}
        { renderedResult && renderedResult.warnings.length > 0 && (
          <Alert
            id={'ide5'}
            message={ renderedResult.warnings.join(', ')}
            type="warning"
            key={'renderWarning' + questionkey}
          />
        )}
        {/*this.props.isAuthor && ( <div> <span className="uk-display-inline uk-button" > key={questionkey} </span>  
                <ParsedBox thiss={this} input={input}  />  </div>) */}
      </div>
    );
  }
}

/* const mapStateToProps = (state) => {
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return {

    superuser: state.getIn(['login', 'groups'], immutable.List([])).includes('SuperUser'),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    lang: state.get('lang', state.getIn(['course', 'languages', 0], 'en'))
  };
};
*/

registerQuestionType('devLinearAlgebra', QuestionDevLinearAlgebra);
registerQuestionType('mathematica', QuestionDevLinearAlgebra);
registerQuestionType('linearAlgebra', QuestionDevLinearAlgebra);
registerQuestionType('compareNumeric', QuestionDevLinearAlgebra);
registerQuestionType('symbolic', QuestionDevLinearAlgebra);
registerQuestionType('Numeric', QuestionDevLinearAlgebra);
registerQuestionType('pythonic', QuestionDevLinearAlgebra);
registerQuestionType('demo', QuestionDevLinearAlgebra);
registerQuestionType('qm', QuestionDevLinearAlgebra);
registerQuestionType('wlanguage', QuestionDevLinearAlgebra);
registerQuestionType('basic', QuestionDevLinearAlgebra);
registerQuestionType('default', QuestionDevLinearAlgebra);
registerQuestionType('matrix', QuestionDevLinearAlgebra);
registerQuestionType('core', QuestionDevLinearAlgebra);

export default connect(null, null)(QuestionDevLinearAlgebra);
