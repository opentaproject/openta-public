// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

'use strict';
import React, { Component } from 'react';
import { connect } from 'react-redux';
import MathSpan from './MathSpan.jsx';
import immutable from 'immutable';
import { questionDispatch } from './questiontypes/question_type_dispatch.jsx';
import { external_renderAsciiMath } from './questiontypes/renderAsciiMath';

/**
 * Renders mathematical expressions in the context of a question.
 * Uses the renderAsciiMath function of the corresponding question type.
 */
class BaseQMath extends Component {
  constructor(props) {
    super(props);
    var questionType = props.questionType;
    var exerciseKey = props.exerciseKey;
    var exerciseState = props.exerciseState;
    var json = exerciseState.get('json', immutable.Map({})) || immutable.Map({});
    var question = immutable.Map({});
    if (questionType && questionType in questionDispatch) {
      var globals = json.getIn(['exercise', 'global'], immutable.List([])).find((q) => {
        return q.getIn(['@attr', 'type']) === questionType || !q.hasIn(['@attr', 'type']);
      });
      if (globals) {
        question = question.set('global', globals);
      }
      this.mathTag = new questionDispatch[questionType]({
        exerciseKey: exerciseKey,
        questionData: question,
        questionState: immutable.Map({}),
        isAuthor: props.author,
        canViewSolution: props.view
      });
      this.mathTag.parseVariables();
    }
  }
  renderAsciiMath = (input) => {
    return external_renderAsciiMath(input, this.mathTag);
  };
  render() {
    //var renderedMath = this.mathTag.renderAsciiMath(this.props.expression,true);
    if (/^\w*\?/.test(this.props.expression)) {
	return ( <span className='uk-text-small'> {this.props.expression.replace(/^\w*\?/,'') } </span> )
    } else {
    var renderedMath = this.renderAsciiMath(this.props.expression, true);
    return <MathSpan message={'$' + renderedMath.out + '$'} />;
    } 
  }
}

const mapStateToProps = (state) => {
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return {
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    view: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    exerciseState: activeExerciseState,
    pendingState: state.get('pendingState'),
    lang: state.get('lang', state.getIn(['course', 'languages', 0], 'en'))
  };
};

const mapDispatchToProps = (dispatch) => ({
  onQuestionSubmit: (exerciseKey, questionKey, data) => dispatch(checkQuestion(exerciseKey, questionKey, data))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseQMath);
