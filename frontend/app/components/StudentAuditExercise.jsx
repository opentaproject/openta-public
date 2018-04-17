import React from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Exercise from './Exercise.jsx';
import MathSpan from './MathSpan.jsx';
import ImageCollection from './ImageCollection.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import mathjs from 'mathjs';
import {asciiMathToMathJS} from './mathrender/string_parse.js'

function renderExpression(expression) {
  try {
    const preParsed = asciiMathToMathJS(expression);
    return '$' + mathjs.parse(expression).toTex() + '$';
  }
  catch(e) {
    return expression;
  }
}

const BaseStudentAuditExercise = ({userResults, pendingResults, exerciseState, activeExercise, anonymous=false}) => {
  const getQuestionText = key => {
    const q = exerciseState.getIn([activeExercise, 'json', 'exercise', 'question'], immutable.List([])).find(q => q.getIn(['@attr', 'key']) === key, null);
    if (q) {
      return q.getIn(['text', '$']);
    }
    return '';
  }
  var answers = userResults.getIn(['exercises', activeExercise, 'questions'], immutable.Map({}))//{{{
      .map( (q, key) => (
            <div className="uk-display-inline-block uk-margin-right" key={key}>
              <table className="uk-table uk-table-condensed">
                <thead>
                  <tr>
                    <th style={{maxWidth: '300px'}}><MathSpan message={getQuestionText(key)}/></th>
                  </tr>
                </thead>
                <tbody>
                      {q.get('answers').map( a => (
                        <tr key={a.get('date')}>
                          <td className={a.get('correct', false) ? 'uk-text-success' : 'uk-text-danger'} title={moment(a.get('date')).format('YYYY-MM-DD HH:mm') + ': ' + a.get('answer')} data-uk-tooltip>
                            <MathSpan>
                              {renderExpression(a.get('answer'))}
                            </MathSpan>
                          </td>
                        </tr>
                      ))}          
                </tbody>
              </table>
            </div>
            )).toList();//}}}
  const imageAnswers = userResults.getIn(['exercises', activeExercise,'imageanswers'], immutable.List([])).reverse();
  const srcs = imageAnswers.map( ia => SUBPATH + "/imageanswer/"+ia.get('pk')).toJS();
  const badges = imageAnswers.map( ia => moment(ia.get('date')).format('YYYY-MM-DD HH:mm')).toJS();
  const types = imageAnswers.map( ia => ia.get('filetype') ).toJS();
  return (
    <div className="uk-panel uk-panel-box">
        <div className="uk-flex">
          <div className="uk-width-2-3 uk-margin-small-right">
            <ImageCollection srcs={srcs} badges={badges} types={types}/>
          </div>
          <div className="uk-width-1-3">

        <h3 className="uk-panel-title">
        { !anonymous && userResults.get('first_name') + ' ' + userResults.get('last_name')}
        { anonymous && userResults.get('username')}
        <i className={'uk-margin-small-right uk-margin-small-left uk-icon ' + (userResults.getIn(['exercises', activeExercise, 'correct'], false) ? 'uk-icon-check uk-text-success' : 'uk-icon-close uk-text-danger')} title="Green: Correct answer"/>
        <i className={'uk-margin-small-right uk-icon uk-icon-picture-o ' + (userResults.getIn(['exercises', activeExercise,'imageanswers'], immutable.List([])).size > 0 ? 'uk-text-success' : 'uk-text-danger')} title="Green: Image uploaded"/>
        <i className={'uk-margin-small-right uk-icon uk-icon-clock-o ' + (userResults.getIn(['exercises', activeExercise,'image_deadline'], false) && userResults.getIn(['exercises', activeExercise,'correct_deadline'], false) ? 'uk-text-success' : 'uk-text-danger')} title="Green: Image and answer submitted before deadline"/> 
        { userResults.getIn(['exercises', activeExercise,'force_passed'], false) &&
          <i className='uk-margin-small-right uk-icon uk-icon-exclamation-circle uk-text-success' title="Manually passed"/> }
        </h3>
          <div className="uk-panel uk-panel-box uk-flex uk-flex-wrap uk-overflow-container uk-margin-small-left" style={{maxHeight: '80vh'}}> 
            { answers }
        </div>
        </div>
    </div>
    </div>
  );
}

const mapStateToProps = state => ({
  userResults: state.getIn(['results', 'detailResults', state.getIn(['results', 'selectedUser'])], immutable.Map({})),
  pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
  activeExercise: state.getIn(['results', 'detailResultExercise'], false),
  exerciseState: state.get('exerciseState'),
});

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStudentAuditExercise)
