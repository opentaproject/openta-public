// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import { connect } from 'react-redux';
import MathSpan from './MathSpan';
import ImageCollection from './ImageCollection';
import Alert from './Alert.jsx'; 

import immutable from 'immutable';
import moment from 'moment';
import { SUBPATH } from '../settings';
import { asciiMathToMathJS } from './mathrender/string_parse';

function renderExpression(expression) {
  try {
    const preParsed = asciiMathToMathJS(expression);
    return '$' + mathjs.parse(expression).toTex() + '$';
  } catch (e) {
    return expression;
  }
}

const BaseStudentAuditExercise = ({
  userResults,
  pendingResults,
  exerciseState,
  activeExercise,
  anonymous = false
}) => {
  const getQuestionText = (key) => {
    const q = exerciseState
      .getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([]))
      .find((q) => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['text', '$']);
    }
    return '';
  };
  var answers = userResults
    .getIn(['exercises', activeExercise, 'questions'], immutable.Map({})) //{{{
    .map((q, key) => (
      <div className="uk-display-inline-block uk-margin-right" key={key}>
        <table className="uk-table uk-table-condensed">
          <thead>
            <tr>
              <th style={{ maxWidth: '300px' }}>
                <MathSpan message={getQuestionText(key)} />
              </th>
            </tr>
          </thead>
          <tbody>
            {q.get('answers').map((a) => (
              <tr key={a.get('date')}>
                <td
                  className={a.get('correct', false) ? 'uk-text-success' : 'uk-text-danger'}
                  title={moment(a.get('date')).format('YYYY-MM-DD HH:mm') + ': ' + a.get('answer')}
                  data-uk-tooltip
                >
                  <MathSpan>{renderExpression(a.get('answer'))}</MathSpan>
                </td> <td> {a.get('type','default')} </td> 
		    <td> <MathSpan> <div dangerouslySetInnerHTML={ 
			{ __html: (() => { try { return JSON.parse(a.get("grader_response") || "{}").comment || ""; } catch (e) { return ""; } })() }
		    } /> </MathSpan> </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ))
    .toList(); //}}}
  const imageAnswers = userResults.getIn(['exercises', activeExercise, 'imageanswers'], immutable.List([])).reverse();
  const srcs = imageAnswers.map((ia) => SUBPATH + '/imageanswer/' + ia.get('pk')).toJS();
  const badges = imageAnswers.map((ia) => moment(ia.get('date')).format('YYYY-MM-DD HH:mm')).toJS();
  const types = imageAnswers.map((ia) => ia.get('filetype')).toJS();
  const imageRequired = exerciseState.getIn(['meta', 'image'], false);
  const imageBeforeDeadline = userResults.getIn(['exercises', activeExercise, 'image_deadline'], false);
  const correctBeforeDeadline = userResults.getIn(['exercises', activeExercise, 'correct_by_deadline'], false);
  const exerciseKey = activeExercise
  var beforeDeadline = null;
  if (imageRequired) {
    if (imageBeforeDeadline && correctBeforeDeadline) {
      beforeDeadline = true;
    } else {
      beforeDeadline = false;
    }
  }
  if (!imageRequired) {
    if (correctBeforeDeadline) {
      beforeDeadline = true;
    } else {
      beforeDeadline = false;
    }
  }
  return (
    <div className="uk-panel uk-panel-box">
      <div className="uk-flex uk-flex-center">
        <div className="uk-margin-small-right uk-width-1-1">
          <h3 className="uk-panel-title">
            {!anonymous && userResults.get('first_name') + ' ' + userResults.get('last_name')}
            {anonymous && userResults.get('username')}
            <i
              className={
                'uk-margin-small-right uk-margin-small-left uk-icon ' +
                (userResults.getIn(['exercises', activeExercise, 'correct'], false)
                  ? 'uk-icon-check uk-text-success'
                  : 'uk-icon-close uk-text-danger')
              }
              title="Green: Correct answer"
            />
            {imageRequired && (
              <i
                className={
                  'uk-margin-small-right uk-icon uk-icon-picture-o ' +
                  (userResults.getIn(['exercises', activeExercise, 'imageanswers'], immutable.List([])).size > 0
                    ? 'uk-text-success'
                    : 'uk-text-danger')
                }
                title="Green: Image uploaded"
              />
            )}
            {beforeDeadline !== null && (
              <i
                className={
                  'uk-margin-small-right uk-icon uk-icon-clock-o ' +
                  (beforeDeadline ? 'uk-text-success' : 'uk-text-danger')
                }
                title="Green: Answer (and image if required) submitted before deadline"
              />
            )}
            {userResults.getIn(['exercises', activeExercise, 'force_passed'], false) && (
              <i
                className="uk-margin-small-right uk-icon uk-icon-exclamation-circle uk-text-success"
                title="Manually passed"
              />
            )}
          </h3>

          <div
            className="uk-panel uk-panel-box uk-flex uk-flex-wrap uk-overflow-container uk-margin-small-left"
            style={{ maxHeight: '80vh' }}
          >
            {answers}
          </div>
          <ImageCollection exerciseKey={exerciseKey} srcs={srcs} badges={badges} types={types} />
        </div>
      </div>
    </div>
  );
};

const mapStateToProps = (state) => ({
  userResults: state.getIn(['results', 'detailResults', state.getIn(['results', 'selectedUser'])], immutable.Map({})),
  pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
  activeExercise: state.getIn(['results', 'detailResultExercise'], false),
  exerciseState: state.get('exerciseState')
});

const mapDispatchToProps = (dispatch) => ({});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStudentAuditExercise);
