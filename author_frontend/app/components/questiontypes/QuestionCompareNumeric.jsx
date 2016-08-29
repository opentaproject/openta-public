"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from '../Alert.jsx';
import immutable from 'immutable';
import { registerQuestionType } from './question_type_dispatch.js'

var inputClass = {
  error: 'uk-form-danger',
  correct: 'uk-form-success',
  incorrect: '',
  none: ''
};

export default class QuestionCompareNumeric extends Component {
  static propTypes = {
    questionData: PropTypes.object,
    responseData: PropTypes.object,
    submitFunction: PropTypes.func,
  }
  render() {  
  var question = this.props.questionData;
  var response = this.props.responseData;
  var submit = this.props.submitFunction;
  var error = response.getIn(['error']);
  var correct = response.getIn(['correct'], false);
  var latex = response.getIn(['latex'], '');
  return (
    <div>
      <div className="uk-panel uk-panel-box uk-margin-top" key={question.get('@key')}>
        <div className="uk-container">
          <label className="uk-form-row">{question.get('text','')}</label>
          <div className="uk-form-icon uk-width-1-1">
            <i className="uk-icon-pencil"/>
            <input className={"uk-width-1-1 "} type="text" onKeyUp={(event) => { if(event.keyCode === 13)submit(event.target.value) } }></input>
          </div>
        { error && <Alert message={error} type="error" key="err"/> }
        { !correct && <Alert message="Incorrect" type="warning" key="incorrect"/> }
        { correct && <Alert message={"$" + latex + "$" + " is correct!"} type="success" key="correct"/> }
        </div>
      </div>
    </div>
  );
}
}

registerQuestionType('compareNumeric', QuestionCompareNumeric);

console.log('CompareNumeric registered!');
