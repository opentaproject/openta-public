import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import MathSpan from './MathSpan.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

const BaseExerciseRecentResults = ({activeExercise, exerciseState, recentAnswers, pending}) => {
  var questions = recentAnswers.keys();
  return (
    <div className="uk-panel uk-panel-box uk-margin-top">
        <h3 className="uk-panel-title">
          Recent answers
        </h3>
        <div className="uk-scrollable-box uk-margin-bottom" style={{height:'70vh'}}>
          <table className="uk-table uk-table-condensed">
            <thead>
              <tr>
              { recentAnswers.map( (answers, question) => (
                <th key={question} style={{maxWidth: '300px'}}><MathSpan message={exerciseState.getIn([activeExercise, 'json', 'exercise', 'question', question, 'text', '$'], '')}/></th>
              )).toList()}
              </tr>
            </thead>
            <tbody>
              <tr>
                { recentAnswers.map( (answers, question) => (
                  <td key={question}>
                    <ul className="uk-list">
                      {
                        answers.map( answer => (
                          <li className={answer.get('correct', false) ? 'uk-text-success' : 'uk-text-danger'} key={answer.get('question')+':'+answer.get('user')+':'+answer.get('date')} title={moment(answer.get('date')).format('YYYY-MM-DD HH:mm')} data-uk-tooltip>
                            { answer.get('answer') }
                          </li>
                        ))
                      }
                    </ul>
                  </td>
                )).toList()}
              </tr>
                  {/*q.get('answers').map( a => (
                    <tr key={a.get('date')}>
                      <td className={a.get('correct', false) ? 'uk-text-success' : 'uk-text-danger'} title={moment(a.get('date')).format('YYYY-MM-DD HH:mm')} data-uk-tooltip>
                        {a.get('answer')}
                      </td>
                    </tr>
                  ))*/}          
            </tbody>
          </table>
        </div>
    </div>
  );
}

const mapStateToProps = state => {
  var activeExercise = state.get('activeExercise');
  return ({
    recentAnswers: state.getIn(['results', 'exercises', activeExercise, 'recent'], immutable.Map({})),
    pending: state.getIn(['pendingState', 'results', 'exercises', activeExercise, 'recent'], false),
    activeExercise: activeExercise,
    exerciseState: state.get('exerciseState'),
  });
}

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseRecentResults)
