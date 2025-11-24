// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
'use strict'; // It is recommended to use strict javascript for easier debugging
import React, { Component } from 'react'; // React specific import
import { lazy } from 'react';
import PropTypes from 'prop-types';
import MathJaxSpan from '../MathJaxSpan.jsx';
import MathSpan from '../MathSpan.jsx';
import ChatIcon from '../ChatIcon.jsx'



import { registerQuestionType } from './question_type_dispatch.jsx'; // Register function used at the bottom of this file to let the system know of the question type
const CKEditor = lazy(() => import('@ckeditor/ckeditor5-react'));
const ClassicEditor = lazy(() => import('@ckeditor/ckeditor5-build-classic'));
//import { CKEditor } from '@ckeditor/ckeditor5-react';
//import { ClassicEditor } from '@ckeditor/ckeditor5-build-classic';
const XMLEditor = lazy(() => import('../XMLEditor.jsx'));
import TextareaEditor from '../TextareaEditor.jsx';
var unstableKey = 93;
const nextUnstableKey = () => unstableKey++;

import Alert from '../Alert.jsx'; // Another component useful for showing alerts in the form of colored boxes. See below for examples.
// Another component useful for showing badges in the form of small colored boxes. See below for examples.
import HelpAIBased from './HelpAIBased.jsx';
import T from '../Translation.jsx';
import t from '../../translations.js';
import { throttle } from 'lodash';

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

export default class QuestionAIBased extends Component {
  static propTypes = {
    questionData: PropTypes.object, 
    questionState: PropTypes.object, 
    submitFunction: PropTypes.func, 
    questionPending: PropTypes.bool, 
    isAuthor: PropTypes.bool, 
    canViewSolution: PropTypes.bool ,
    exerciseKey: PropTypes.string,
  };

  constructor(props) {
    super(props);
    this.state = {
      value: this.props.questionState.getIn(['answer'], ''),
      response : this.props.questionState.getIn(['response','comment'], ''),
      nresponse :  0,
      mathSize: 'medium',
      cursor: 0
    };
    this.lastParsable = '';
  }

  handleChange = (event) => {
    this.setState({ value: event.target.value });
  };

  handleSubmit= (value) => {
    this.setState({ value: value });
    this.setState({ nresponse : 0 });
    return this.props.submitFunction( value );
  };


  handleIncrement= (event) => {
    var n = this.state.nresponse + 1
    if ( n >=  event ){
    	    n = event  - 1 
    }
    if ( n < 0 ){ n = 0 ; }
    this.setState({ nresponse: n });
  };

  handleDecrement= (event) => {
    var n = this.state.nresponse - 1
    if ( n < 0 ) { n = 0 }
    this.setState({ nresponse: n  })
  };

  //handleCKChange = (event, editor) => {
  //  const data = editor.getData();
  //  this.setState({ value: data });
  //};

  updateCursor = throttle((pos) => {
    this.setState({ cursor: pos });
  }, 500);

  handleSelect = (event) => {
    this.updateCursor(event.target.selectionStart);
  };

  setMathSize = (sizeStr) => {
    this.setState({ mathSize: sizeStr });
  };

  // UNSAFE_componentWillReceiveProps = newProps => {};

  valueUpdate = (value) => {
    this.setState({ value: value });
  };

  createMarkup = (value) => {
    return { __html: value };
  };

  /* render gets called every time the question is shown on screen */
  render() {
    // Some convenience definitions
    var question = this.props.questionData;
    var state = this.props.questionState;
    var submit = this.props.submitFunction;
    var pending = this.props.questionPending;
    var answerbox = question.getIn(['@attr', 'answerbox'], true);
    var notanswerbox = false;
    if (answerbox == 'false' || answerbox == 'False') {
      answerbox = false;
      notanswerbox = true;
    } else {
      answerbox = true;
      notanswerbox = false;
    }


    var lastAnswer = state.getIn(['answer'], ''); 
    var n_attempts = state.getIn(['response', 'n_attempts'], question.getIn(['n_attempts'], 0));
    var previous_answers = state.getIn(['response', 'previous_answers'], question.getIn(['previous_answers'], []));
    var querypath = state.getIn(['response', 'querypath','$'], question.getIn(['querypath','$'], null));
    if ( querypath != null ){
	    querypath = querypath.replace(/ /g, "");
    		}
    var questionKey = state.getIn(['response', '@attr','key'], question.getIn(['@attr','key'], null));
    if ( querypath ){
	    querypath = querypath + '/' + this.props.exerciseKey.substring(0,7) + questionKey
	    querypath = "./django_ragamuffin/query/" + querypath
    }
    var isAuthor = this.props.isAuthor

    var correct = state.getIn(['response', 'correct'], null) || state.getIn(['correct'], null); 
    var stype = correct ? 'success' : 'danger';
    var nprevious = previous_answers.size
    var editor_type = state.getIn(['response', 'editor'], question.getIn(['editor'], 'default'));

    var error = state.getIn(['response', 'error']); // Custom field containing error information
    var author_error = state.getIn(['response', 'author_error']); // Custom field containing error information
    var warning = state.getIn(['response', 'warning']); // Custom field containing error information
    var hint = state.getIn(['response', 'hint']); // Custom field containing error information
    var comment = state.getIn(['response', 'comment'], '');
    var tdict = state.getIn(['response', 'dict'], '');
    if (state.getIn(['response', 'detail'])) {
      error =
        'Ett fel uppstod. (Detta kan bero på att du inte är inloggad, om problem kvarstår var vänlig hör av dig.)';
    }

    var graderResponse = null;
    // var input = this.state.value;
    var nresponse = this.state.nresponse
    //console.log("QUESTION =", this.state.value)
    var cv = this.state.value

    // if ('' == input) {
    //   var p = previous_answers;
    //   if (p.length > 0) {
    //     input = p[0].answer;
    //   }
   //  }


    // if (notanswerbox) {
    //   input = ' '; // MAKE THIS A BLANK SO AS NOT TO TRIGGER A NOOP in fetchers.js/questionCheck
   //  }

    var hasChanged = this.state.value !== lastAnswer;
    // var nonEmpty = input !== '';
    var unchecked = '(' + t('unchecked') + ')';

    var itemjson = question.getIn(['text'], undefined);
    var comment = ''
    if ( nprevious > 0 && ! hasChanged ){
	var p =  previous_answers.toJS()[nresponse]
	var lastAnswer =  p.answer
	var comment = JSON.parse( p.grader_response)['comment']
	}
    try {
    comment = comment.replace(/\\operatorname\{([^}]*)\}/g, "\\textstyle{$1}");
    comment = comment.replace(/\\boldsymbol/g, "\\mathbf");  
   } catch( error ) { comment = '' }

   

    // graderResponse = ( <Alert className="uk-margin-small-top uk-margin-small-bottom" message={comment} type={stype} key="input1" />);


    var questiontext = this.props.renderText(itemjson);
    var questionkey = question.getIn(['@attr', 'key']);
    var msg1 = 'QuestionType QuestionAIBased';
    var id = 'questionaibased';
    var n = Math.max( nprevious - nresponse - 1 , 0 )
    if ( pending ){
	    var proposedInput =   '   ... wait for up to 4 minutes to answer the question '   

    } else {
	    var proposedInput = lastAnswer
    }

    //comment = comment.replace(/\\iff/g, "\\Leftrightarrow"); 
    comment = comment.replace(/\\\[/g,'$$')
    comment = comment.replace(/\\\]/g,'$$')
    comment = comment.replace(/\$\s*\n/g, '$');

    return (
      <div key={'aibased' + nresponse } className="">
	    {answerbox && (  <ChatIcon title="Ask a question from openai about this exercise." /> )}
	    { isAuthor && querypath && ( 
	    <span> <a href={querypath}> Edit aibased data </a></span>
	    )} 
	    <div key={'qr' + nextUnstableKey()} > <MathJaxSpan> {questiontext}  </MathJaxSpan> </div>
	    { nprevious > 0 && (
	    <div key={'buttons' + nresponse} className="uk-button-group">
            <button onClick={(event) => {this.handleIncrement(nprevious) } } className={ 'uk-button'  } >
              <i className="uk-icon uk-icon-arrow-up" /> </button>
	    </div> )} 

        <span key={'an992' + nextUnstableKey()} className="uk-text-small uk-text-primary">
          {' '}
          [   {  n } ]{' '}
        </span>

        <span data-uk-tooltip title={msg1} />
        <div key={'textarea' + nresponse} className="uk-grid uk-width-1-1">

              <div className="uk-width-1-1">
                <textarea
                  id={questionkey}
                  className={'uk-width-1-1'}
                  defaultValue={proposedInput}
                  onSelect={this.handleSelect}
                  onChange={this.handleChange}
                />
	    

	    { nprevious > 0 && (
            <button onClick={(event) => {this.handleDecrement(nprevious)} } className={ 'uk-button'  } >
              <i className="uk-icon uk-icon-arrow-down" /> </button>
	    )}
            { pending &&  ( <i className="uk-icon-cog uk-icon-spin" /> ) }
	    { pending &&  (  <Timer/>  ) }
	    { ! pending && ( <a onClick={(event) => this.handleSubmit(this.state.value)} className={ 'uk-button padding-remove ' + ( hasChanged ? 'uk-button-success' : '') } > <i className="uk-icon uk-icon-send" /> </a>)}
	    </div>



        </div>
	{ nprevious > 0 && (
        <div key={'graderResponse' + nresponse} className="uk-flex">
		<MathJaxSpan html={comment} />
        </div> ) } 
      </div>
    );
  }
}

//Register the question component with the system
registerQuestionType('aibased', QuestionAIBased);
