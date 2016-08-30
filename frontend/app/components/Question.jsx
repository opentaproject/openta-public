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
      var alerts = [];
      if(question.get('@key', undefined) == undefined && this.props.admin) {
       alerts.push( (<Alert message="No question key, please add an attribute key=..." type="error"/>));
      }
      var topDOM = React.createElement('div', {
        className: "uk-panel uk-panel-box uk-margin-bottom",
        key: questionKey
      }, [ 
        alerts,
        questionDOM]);
      return topDOM;
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
    admin: state.getIn(['login', 'admin']),
    exerciseState: activeExerciseState
  })
};

const mapDispatchToProps = dispatch => ({
    onQuestionSubmit: (exerciseKey, questionKey, data) => dispatch(checkQuestion(exerciseKey, questionKey, data))
    //onQuestionSubmit: (exerciseKey, questionKey, data) => console.log(data) 
  });

export default connect(mapStateToProps, mapDispatchToProps)(BaseQuestion)
