"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import immutable from 'immutable';
import { checkQuestion } from '../fetchers.js'
import { questionDispatch } from './questiontypes/question_type_dispatch.js'
import * as qt from './questiontypes/question_types.js'

//const BaseQuestion = ({exerciseKey, questionKey, exerciseState, onQuestionSubmit}) => {
class BaseQuestion extends Component {
  render() {
    var questionType = this.props.questionType;
    var questionKey = this.props.questionKey;
    var exerciseKey = this.props.exerciseKey;
    var exerciseState = this.props.exerciseState;
    var onQuestionSubmit = this.props.onQuestionSubmit;
    var json = exerciseState.get('json', immutable.Map({}));
    var question = json.getIn(['exercise','question'], immutable.List([])).find( q => q.get('@key') == questionKey, immutable.Map({}));
    var questionState = exerciseState.getIn(['question', questionKey], immutable.Map({}))
    var questionType = question.get('@type', undefined);
    if(questionType) {
      var questionDOM = React.createElement(questionDispatch[questionType], { 
        questionData: question, 
        questionState: questionState, 
        submitFunction: (data) => onQuestionSubmit(exerciseKey, questionKey, data),
          ref: (ref) => this.questionref = ref
      }); 
      return questionDOM;
    } 
    else {
      return (<div>Invalid question</div>);
    }
  }

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.questionref);
    MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
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
