// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

/*
 * This is the presentational part of a question. It contains the javascript and html code that is shown in the front-end to the user.
 * It consists of a React component (see documentation on github for more details).
 */
'use strict'; // It is recommended to use strict javascript for easier debugging
import React, { Component } from 'react'; // React specific import
//import ReactDOMServer from 'react-dom/server';
import { lazy } from 'react';
import PropTypes from 'prop-types';

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
import HelpTextbased from './HelpTextbased.jsx';
import T from '../Translation.jsx';
import t from '../../translations.js';
import { throttle } from 'lodash';

export default class QuestionTextbased extends Component {
  static propTypes = {
    questionData: PropTypes.object, // Data from exercise XML file, i.e. whats inside the <question> tag
    questionState: PropTypes.object, // Current question state together with response data from server
    submitFunction: PropTypes.func, // Call this function to submit an answer to the server. The only parameter is the answer data which is unconstrained: It could be a simple string as below or a dictionary of values if more information needs to be conveyed.
    questionPending: PropTypes.bool, // Indicates when we are waiting for a server response
    isAuthor: PropTypes.bool, //Indicates if user is an author/content creator.
    canViewSolution: PropTypes.bool //Indicates if user is allowed to see solution.
  };

  constructor(props) {
    super(props);
    this.state = {
      value: this.props.questionState.getIn(['answer'], ''),
      mathSize: 'medium',
      cursor: 0
    };
    this.lastParsable = '';
    //if (this.props.canViewSolution)
    //  this.state.value = this.props.questionData
    //    .getIn(["expression", "$"], "")
    //    .replace(/;/g, "")
    //    .trim();
  }

  handleChange = (event) => {
    this.setState({ value: event.target.value });
  };

  handleCKChange = (event, editor) => {
    const data = editor.getData();
    this.setState({ value: data });
  };

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

    // System state data
    var lastAnswer = state.getIn(['answer'], ''); // Last saved answer in database, same format as passed to the submitFunction
    var correct = state.getIn(['response', 'correct'], null); // || state.getIn(["correct"], null); // Boolean indicating if the grader reported correct answer
    //var correct = state.getIn(["response", "correct"], false) || state.getIn(["correct"], false); // Boolean indicating if the grader reported correct answer
    var n_attempts = state.getIn(['response', 'n_attempts'], question.getIn(['n_attempts'], 0));
    var previous_answers = state.getIn(['response', 'previous_answers'], question.getIn(['previous_answers'], []));
    var editor_type = state.getIn(['response', 'editor'], question.getIn(['editor'], 'default'));
    // override default true xml of feedback with options
    if (state.getIn(['correct'], null) == null) {
      var feedback = false;
    } else {
      var feedback = true;
    }

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
    var input = this.state.value;
    if ('' == input) {
      var p = previous_answers;
      if (p.length > 0) {
        input = p[0].answer;
      }
    }
    if (notanswerbox) {
      input = ' '; // MAKE THIS A BLANK SO AS NOT TO TRIGGER A NOOP in fetchers.js/questionCheck
    }

    var hasChanged = input !== lastAnswer;
    var nonEmpty = input !== '';
    var unchecked = '(' + t('unchecked') + ')';
    if (notanswerbox || (input === lastAnswer && lastAnswer !== '' && !error)) {
      if (feedback) {
        if (correct) {
          graderResponse = (
            <Alert
              className="uk-margin-small-top uk-margin-small-bottom"
              message={t('Correct') + t(comment, tdict)}
              type="success"
              key="input1"
            />
          );
          if (n_attempts < 2) {
            graderResponse = (
              <Alert
                className="uk-margin-small-top uk-margin-small-bottom"
                message={t('Correct first time!') + t(comment, tdict)}
                type="success"
                key="input2"
              />
            );
          }
        } else if (correct === null) {
          graderResponse = (
            <Alert className="uk-margin-small-top uk-margin-small-bottom" message={t('Submitted')} key="input3" />
          );
        } else {
          graderResponse = (
            <Alert
              className="uk-margin-small-top uk-margin-small-bottom"
              message={t('Not correct.') + t(comment, tdict)}
              type="warning"
              key="input4"
            />
          );
          if (n_attempts > 4 && n_attempts % 2 == 0) {
            graderResponse = (
              <Alert
                className="uk-margin-small-top uk-margin-small-bottom"
                message={t('Is not correct.') + t(comment, tdict)}
                type="warning"
                key="input5"
              />
            );
          }
        }
      } else {
        graderResponse = (
          <Alert
            className="uk-margin-small-top uk-margin-small-bottom"
            message={unchecked + t(comment, tdict)}
            type="text"
            key="input6"
            hasMath={false}
          />
        );
      }
    }
    var itemjson = question.getIn(['text'], undefined);
    var questiontext = this.props.renderText(itemjson);
    var questionkey = question.getIn(['@attr', 'key']);
    var msg1 = 'QuestionType QuestionTextbased';
    var id = 'ABC';
    return (
      <div key={'textbased'} className="">
        {questiontext}
        <span key={'an992' + nextUnstableKey()} className="uk-text-small uk-text-primary">
          {' '}
          [ {feedback} {n_attempts} <T>submissions </T> ]{' '}
        </span>

        <HelpTextbased />
        <span data-uk-tooltip title={msg1} />
        {hasChanged && lastAnswer !== '' && (
          <span>
            <a className="uk-text" data-uk-toggle={"{target:'#" + id + "'}"}>
              {' '}
              Previous text{' '}
            </a>
            <div id={id} className="uk-hidden">
              {' '}
              {lastAnswer}{' '}
            </div>
          </span>
        )}
        <div className="uk-grid uk-width-1-1">
          {editor_type == 'code' && (
            <div className="uk-width-5-6">
              <XMLEditor
                suppresstools={true}
                xmlCode={this.state.value}
                onChange={(editor, data, value) => this.valueUpdate(value)}
              />
              <div className="uk-width-1-1">
                <textarea
                  id={questionkey}
                  className={'uk-width-1-1 '}
                  value={this.state.value}
                  onSelect={this.handleSelect}
                  onChange={this.handleChange}
                />
              </div>
            </div>
          )}

          {editor_type == 'html' && (
            <div className="uk-width-5-6">
              <CKEditor editor={ClassicEditor} data={input} onChange={this.handleCKChange} />

              <div dangerouslySetInnerHTML={this.createMarkup(input)} />

              <div className="uk-hidden uk-width-1-1">
                <textarea
                  id={questionkey}
                  className={'uk-width-1-1 '}
                  value={this.state.value}
                  onSelect={this.handleSelect}
                  onChange={this.handleChange}
                />
              </div>
            </div>
          )}
          {'default' == editor_type && (
            <div className="uk-width-1-1">
              <TextareaEditor suppresstools={false} value={input} onChange={(value) => this.valueUpdate(value)} />
              <div className="uk-width-1-1 uk-hidden">
                <textarea
                  id={questionkey}
                  className={'uk-width-1-1'}
                  value={input}
                  onSelect={this.handleSelect}
                  onChange={this.handleChange}
                />
              </div>
            </div>
          )}

          <div className="uk-width-1-6">
            <a
              onClick={(event) => submit(input)}
              className={
                'uk-width-1-1 uk-button uk-padding-remove ' + (nonEmpty && hasChanged ? 'uk-button-success' : '')
              }
            >
              {pending && <i className="uk-icon-cog uk-icon-spin" />}
              {!pending && <i className="uk-icon uk-icon-send" />}
            </a>
          </div>
        </div>
        {error && !hasChanged && <Alert message={error} type="error" key="err" />}
        {author_error && this.props.isAuthor && <Alert message={author_error} type="error" key="author_error" />}
        {warning && (!hasChanged || notanswerbox) && <Alert message={warning} type="warning" key="warning" />}
        {hint && <Alert message={hint} type="primary" key="renderhint" />}
        <div className="uk-flex">
          <span className={'uk-width-1-1 '}>{graderResponse}</span>
        </div>
      </div>
    );
  }
}

//Register the question component with the system
registerQuestionType('textbased', QuestionTextbased);
