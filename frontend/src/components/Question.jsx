'use strict';
import React, { Component } from 'react';
import { connect } from 'react-redux';
import ReactDOM from 'react-dom';
import Alert from './Alert';
import immutable from 'immutable';
import { use_chatgpt } from '../settings.js';
import { checkQuestion } from '../fetchers';
import { questionDispatch } from './questiontypes/question_type_dispatch';
import './questiontypes/question_types.jsx';
import { renderText } from './questiontypes/render_text';
var unstableKey = 29811;
const nextUnstableKey = () => unstableKey++;

//const BaseQuestion = ({exerciseKey, questionKey, exerciseState, onQuestionSubmit}) => {
class BaseQuestion extends Component {
   constructor(props) {
    super(props);
    this.questionRef = React.createRef();
  }
  render() {
    var questionType = this.props.questionType;
    var questionKey = this.props.questionKey;
    var exerciseKey = this.props.exerciseKey;
    var locked = this.props.locked && !this.props.author;
    var exerciseState = this.props.exerciseState;
    var exercisestate = this.props.exerciseState.toJS();
    var feedback = exerciseState.getIn(['meta', 'feedback'], false);
    var pendingState = this.props.pendingState;
    var onQuestionSubmit = this.props.onQuestionSubmit;
    var json = exerciseState.get('json', immutable.Map({})) || immutable.Map({});
    var question = json
      .getIn(['exercise', 'question'], immutable.List([]))
      .find((q) => q.getIn(['@attr', 'key']) == questionKey, this, immutable.Map({}));
    var dtype =  question.getIn(['choice'],'') ? 'multipleChoice' : 'default' // Parse questionType from context
    var questionType = question.getIn(['@attr', 'type'], dtype);
    var dohide =  String( questionType ) == 'aibased'  && ! use_chatgpt 
    var allow_ai = this.props.allow_ai || this.props.author || this.props.admin || this.props.superuser
    dohide = dohide || ! allow_ai
    if ( String( questionType) != 'aibased' ) { dohide = false } 
    var questionState = exerciseState.getIn(['question', questionKey], immutable.Map({}));
    var okornot = questionState.getIn(['response', 'correct'], null);
    var iscorrect = questionState.getIn(['correct'], 'undefined');
    if (questionType && questionType in questionDispatch) {
      var globals = json.getIn(['exercise', 'global'], immutable.List([])).find((q) => {
        return q.getIn(['@attr', 'type']) === questionType || !q.hasIn(['@attr', 'type']);
      });
      if (globals) {
        question = question.set('global', globals);
      }
      var canViewSolution = this.props.view || this.props.admin || this.props.author
      if ( ! dohide ){
      var questionDOM = React.createElement(questionDispatch[questionType], {
        key: questionKey + nextUnstableKey() ,
        questionkey: questionKey,
        locked: locked,
        feedback: feedback,
        exerciseKey: exerciseKey,
        questionData: question,
	exerciseState: this.props.exerciseState,
	assets: this.props.assets,
        renderText: this.props.renderText || ((itemjson) => renderText(itemjson, null, this.props.lang)),
        questionState: questionState,
	pendingState: pendingState,
        questionPending: pendingState.getIn( ['exercises', exerciseKey, 'questions', question.getIn(['@attr', 'key']), 'waiting'], false),
        answerPending: pendingState.getIn(
          ['exercises', exerciseKey, 'questions', question.getIn(['@attr', 'key']), 'waiting_for'],'NO_ANSWER_PENDING'
        ),
        isAuthor: this.props.author,
	isSuperUser: this.props.superuser,
        lang: this.props.lang,
        canViewSolution: canViewSolution,
        submitFunction: (data) => onQuestionSubmit(exerciseKey, questionKey, data),
        ref: this.questionRef.current
      });
      } else {
	var questionDOM = <div/>
      }
      var alerts = [];
      if (question.getIn(['@attr', 'key'], undefined) == undefined && this.props.admin) {
        alerts.push(<Alert key={'alertkey'} message="No question key, please add an attribute key=..." type="error" />);
      }
      var cname = 'question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top ';
      var yescorrect = '';
      if (iscorrect == true) {
        yescorrect = 'yescorrect';
        cname = 'question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top yescorrect ready';
      } else if (iscorrect == null) {
        yescorrect = 'unchecked';
        cname = 'question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top unchecked ready';
      } else if (iscorrect == false) {
        cname = 'question uk-panel uk-panel-box uk-padding-bottom-remove uk-margin-top notcorrect ready';
        yescorrect = 'notcorrect';
      }
      //console.log(exerciseKey + ' ' + questionKey + " okornot , YESCORRECT = " +  okornot + ' ' +   yescorrect  )
      //console.log(exerciseKey + ' ' + questionKey + " cname = " +  cname)
      if( ! dohide ){
      var topDOM = React.createElement(
        'div',
        {
          className: cname,
          id: questionKey,
          key: questionKey
        },
        [alerts, questionDOM]
      );
      } else {
	      var topDOM = <div/>
      }
      return topDOM;
    } else {
      return <div>Invalid question</div>;
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

  componentDidUpdate(props, state, root) {
    // var node = ReactDOM.findDOMNode(this.questionref);
    var node = this.questionRef.current;
    //MathJax.Hub.Queue(["Typeset", MathJax.Hub, node]);
    if (node !== null) {
      renderMathInElement(node, {
        delimiters: [{ left: '$', right: '$', display: false }]
      });
    }
  }
}

const mapStateToProps = (state) => {
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return {
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    superuser : state.getIn(['login', 'groups'], immutable.List([])).includes('SuperUser'),
    view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState'),
    assets: activeExerciseState.getIn(['assets','files'], immutable.List([])),
    lang: state.get('lang', state.getIn(['course', 'languages', 0], 'en')),
    allow_ai: activeExerciseState.getIn(['meta','allow_ai'], true ) 
  };
};

const mapDispatchToProps = (dispatch) => ({
  onQuestionSubmit: (exerciseKey, questionKey, data) => {
    //console.log("exerciseKey = ", exerciseKey );
    //console.log("questionKey = ", questionKey );
    //console.log("data = ", data );
    dispatch(checkQuestion(exerciseKey, questionKey, data));
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseQuestion);
