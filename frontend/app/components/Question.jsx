"use strict";
import React, { Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert.jsx';
import Spinner from './Spinner.jsx';
import immutable from 'immutable';
import { checkQuestion } from '../fetchers.js'
import { questionDispatch } from './questiontypes/question_type_dispatch.js'
import * as qt from './questiontypes/question_types.js'
import { renderText } from './questiontypes/render_text.js'

//const BaseQuestion = ({exerciseKey, questionKey, exerciseState, onQuestionSubmit}) => {
class BaseQuestion extends Component {
  render() {
    var questionType = this.props.questionType;
    var questionKey = this.props.questionKey;
    var exerciseKey = this.props.exerciseKey;
    var exercisemeta = this.props.exercisemeta;
    var locked = this.props.locked && ! this.props.author
    var exerciseState = this.props.exerciseState;
    var pendingState = this.props.pendingState;
    var onQuestionSubmit = this.props.onQuestionSubmit;
    var json = exerciseState.get('json', immutable.Map({})) || immutable.Map({});
    var question = json.getIn(['exercise', 'question'], immutable.List([])).find(q => q.getIn(['@attr', 'key']) == questionKey, this, immutable.Map({}));
    var questionType = question.getIn(['@attr', 'type'], undefined);
    var questionState = exerciseState.getIn(['question', questionKey], immutable.Map({}))
    var okornot = questionState.getIn( ['response','correct'], null )
    var iscorrect = questionState.getIn(['correct'],'undefined')
    // console.log("OKORNOT = ", okornot)
    // console.log("ISCORRECT = ", iscorrect )
    if(questionType && questionType in questionDispatch) {
      var globals = json.getIn(['exercise','global'], immutable.List([])).find( q => {
        return q.getIn(['@attr','type']) === questionType || (!q.hasIn(['@attr', 'type']));
      });
      if (globals) question = question.set('global', globals);
      var questionDOM = React.createElement(questionDispatch[questionType], {
        key: questionKey,
        locked: locked,
        exerciseKey: exerciseKey,
        questionData: question,
        renderText: this.props.renderText || ((itemjson) => renderText(itemjson, null, this.props.lang)),
        questionState: questionState,
        questionPending: pendingState.getIn(['exercises', exerciseKey, 'questions', question.getIn(['@attr', 'key']), 'waiting'], false),
        isAuthor: this.props.author,
        lang: this.props.lang,
        canViewSolution: this.props.view,
        submitFunction: (data) => onQuestionSubmit(exerciseKey, questionKey, data),
        ref: (ref) => this.questionref = ref
      });
      var alerts = [];
      if (question.getIn(['@attr', 'key'], undefined) == undefined && this.props.admin) {
        alerts.push((<Alert key={"alertkey"} message="No question key, please add an attribute key=..." type="error" />));
      }
      var yescorrect = '';
      if (iscorrect) {
        yescorrect = 'yescorrect';
      }
      if (iscorrect == null) {
        yescorrect = 'unchecked';
      }
      var yescorrect = 'undefined'
      var cname = "question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top "
      if( iscorrect == true ){
            yescorrect = 'yescorrect'
            cname = "question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top yescorrect ready"
            }
      if( iscorrect == null ){
            yescorrect = 'unchecked'
            cname = "question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top unchecked ready"
            }
      if( iscorrect == false ){
            cname = "question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top unchecked notcorrect ready"
            yescorrect = 'notcorrect'
            }
      //console.log(exerciseKey + ' ' + questionKey + " okornot , YESCORRECT = " +  okornot + ' ' +   yescorrect  )
      //console.log(exerciseKey + ' ' + questionKey + " cname = " +  cname)
      var topDOM = React.createElement('div', {
        className: cname,
        id: questionKey,
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

  /* shouldComponentUpdate(nextProps) {
        var questionKey = this.props.questionKey
        var questionState = this.props.exerciseState.getIn(['question', questionKey] , null ) 
        if( questionState == null ){
            return false
        }
        var nextQuestionState = nextProps.exerciseState.getIn(['question', questionKey] )
        var wascorrect = questionState.getIn(['correct'],null) 
        var iscorrect = nextQuestionState.getIn(['correct'],null) 
        console.log("WAS AND IS = ", wascorrect, iscorrect)
        //const differentTitle = this.props.title !== nextProps.title;
        //const differentDone = this.props.done !== nextProps.done
        //return differentTitle || differentDone;
        var should = ! ( wascorrect &&  iscorrect )
        console.log("SHOULD = ", should )
        return should
    }
    */

  componentDidUpdate(props,state,root) {
    var node = ReactDOM.findDOMNode(this.questionref);
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if (node !== null)
      renderMathInElement(node, {
        delimiters: [{ left: "$", right: "$", display: false }]
      });
  }
}

const mapStateToProps = state => {
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return (
    {
      admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
      author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
      view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
      exerciseState: activeExerciseState,
      pendingState: state.get('pendingState'),
      lang: state.get('lang', state.getIn(['course', 'languages', 0], 'en'))
    })
};

const mapDispatchToProps = dispatch => ({
  onQuestionSubmit: (exerciseKey, questionKey, data) => dispatch(checkQuestion(exerciseKey, questionKey, data))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseQuestion)
