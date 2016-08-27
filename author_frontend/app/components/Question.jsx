"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import immutable from 'immutable';
import QuestionCompareNumeric from './QuestionCompareNumeric.jsx';
import { checkQuestion } from '../fetchers.js'

const questionDispatch = {
  'compareNumeric': QuestionCompareNumeric,
  'none': 'div'
};

const BaseQuestion = ({exerciseKey, questionKey, exerciseState, onQuestionSubmit}) => {
  var json = exerciseState.get('json', immutable.Map({}));
  var question = json.getIn(['exercise','question',questionKey], immutable.Map({}));
  var questionType = question.get('@type', undefined);
  if(questionType) {
    var questionDOM = React.createElement(questionDispatch[questionType], { questionData: question, submitFunction: (data) => onQuestionSubmit(exerciseKey, questionKey, data)}); 
    return questionDOM;
  } 
  else {
    return (<div>Invalid question</div>);
  }
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return (
  {
    exerciseState: activeExerciseState
  })
};

const mapDispatchToProps = dispatch => ({
    onQuestionSubmit: (exerciseKey, questionKey, data) => dispatch(checkQuestion(exerciseKey, questionKey, data))
    //onQuestionSubmit: (exerciseKey, questionKey, data) => console.log(data) 
  });

export default connect(mapStateToProps, mapDispatchToProps)(BaseQuestion)
