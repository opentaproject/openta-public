"use strict";
import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import Spinner from './Spinner.jsx';
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
    var pendingState = this.props.pendingState;
    var onQuestionSubmit = this.props.onQuestionSubmit;
    var json = exerciseState.get('json', immutable.Map({})) || immutable.Map({});
    var question = json.getIn(['exercise','question'], immutable.List([])).find( q => q.getIn(['@attr','key']) == questionKey, this, immutable.Map({}));
    var questionType = question.getIn(['@attr','type'], undefined);
    var questionState = exerciseState.getIn(['question', questionKey], immutable.Map({}))
    if(questionType && questionType in questionDispatch) {
      var globals = json.getIn(['exercise','global'], immutable.List([])).find( q => {
        return q.getIn(['@attr','type']) === questionType || (!q.hasIn(['@attr', 'type']));
      });
      if(globals)question = question.set('global', globals);
      var questionDOM = React.createElement(questionDispatch[questionType], { 
        key: questionKey,
        exerciseKey: exerciseKey,
        questionData: question, 
        questionState: questionState, 
        questionPending: pendingState.getIn(['exercises', exerciseKey, 'questions', question.getIn(['@attr','key']), 'waiting'], false),
        isAuthor: this.props.author, 
        canViewSolution: this.props.view,
        submitFunction: (data) => onQuestionSubmit(exerciseKey, questionKey, data),
          ref: (ref) => this.questionref = ref
      }); 
      var alerts = [];
      if(question.getIn(['@attr','key'], undefined) == undefined && this.props.admin) {
       alerts.push( (<Alert key={"alertkey"} message="No question key, please add an attribute key=..." type="error"/>));
      }
      var topDOM = React.createElement('div', {
        className: "uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top",
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
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if(node !== null)
      renderMathInElement(node, {
        delimiters: [{left: "$", right: "$", display: false}]
      });
  }
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return (
  {
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
    view: state.getIn(['login', 'groups'],immutable.List([])).includes('View'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState')
  })
};

const mapDispatchToProps = dispatch => ({
    onQuestionSubmit: (exerciseKey, questionKey, data) => dispatch(checkQuestion(exerciseKey, questionKey, data))
  });

export default connect(mapStateToProps, mapDispatchToProps)(BaseQuestion)
