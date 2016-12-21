import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercise
} from '../fetchers.js';
import {
  setResultsFilter,
  setDetailResultExercise,
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Exercise from './Exercise.jsx';
import MathSpan from './MathSpan.jsx';
import ImageCollection from './ImageCollection.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

const BaseStudentResults = ({userResults, pendingResults, filter, onExerciseClick, activeExercise, onBack, exerciseState}) => {
  var required = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'required'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var bonus = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'bonus'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var n_required = required.filter( e =>
    filter.get('requiredKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;
  var n_bonus = bonus.filter( e =>
    filter.get('bonusKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;
  return (
    <div className="uk-panel uk-panel-box" id="studentresults" style={ activeExercise ? {} : {}}>
      <article className="uk-article">
      <h1 className="uk-article-title">
      { !pendingResults && !activeExercise && userResults.get('first_name') + " " + userResults.get('last_name')}
      { pendingResults && <Spinner/> }
      </h1>
      { !pendingResults && !activeExercise &&
      <div className="uk-grid">
      <div>
      <table className="uk-table uk-table-hover">
        <caption>Obligatory {n_required} / {required.size}</caption>
        <thead>
          <tr>
            <th>Exercise</th>
            <th>Tries/Q</th>
            <th>Passed</th>
          </tr>
        </thead>
        <tbody>
          { required.map( e => (
            <tr key={e.get('exercise_key')} onClick={() => onExerciseClick(e.get('exercise_key'))} className="pointer">
              <td>{e.get('name')}</td>
              <td>{(e.get('tries', 0) / e.get('questions').size).toFixed(1)}</td>
              <td>
                      <i className={'uk-margin-small-right uk-icon ' + (e.get('correct', false) ? 'uk-icon-check uk-text-success' : 'uk-icon-close uk-text-danger')}/>
                      <i className={'uk-margin-small-right uk-icon uk-icon-picture-o ' + (e.get('imageanswers', immutable.List([])).size > 0 ? 'uk-text-success' : 'uk-text-danger')}/>
                      <i className={'uk-margin-small-right uk-icon uk-icon-clock-o ' + (e.get('image_deadline', false) && e.get('correct_deadline',false) ? 'uk-text-success' : 'uk-text-danger')}/> 
                { /* filter.get('requiredKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b) ? <i className="uk-icon uk-icon-check uk-text-success"/> : <i className="uk-icon uk-icon-close uk-text-danger"/> */ }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      <div>
      <table className="uk-table uk-table-hover">
        <caption>Bonus {n_bonus} / {bonus.size}</caption>
        <thead>
          <tr>
            <th>Exercise</th>
            <th>Tries/Q</th>
            <th>Passed</th>
          </tr>
        </thead>
        <tbody>
          { bonus.map( e => (
            <tr key={e.get('exercise_key')} onClick={() => onExerciseClick(e.get('exercise_key'))} className="pointer">
              <td>{e.get('name')}</td>
              <td>{(e.get('tries', 0) / e.get('questions').size).toFixed(1)}</td>
              <td>
                      <i className={'uk-margin-small-right uk-icon ' + (e.get('correct', false) ? 'uk-icon-check uk-text-success' : 'uk-icon-close uk-text-danger')}/>
                      <i className={'uk-margin-small-right uk-icon uk-icon-picture-o ' + (e.get('imageanswers', immutable.List([])).size > 0 ? 'uk-text-success' : 'uk-text-danger')}/>
                      <i className={'uk-margin-small-right uk-icon uk-icon-clock-o ' + (e.get('image_deadline', false) && e.get('correct_deadline',false) ? 'uk-text-success' : 'uk-text-danger')}/> 
                {/*filter.get('bonusKeys', []).map(key => e.get(key, false)).reduce( (a,b) => a && b) ? <i className="uk-icon uk-icon-check uk-text-success"/> : <i className="uk-icon uk-icon-close uk-text-danger"/>*/ }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      </div>
      }
      { !pendingResults && activeExercise &&
        <div className="uk-grid">
        <div className="uk-width-1-1">
          <button className="uk-button uk-button-primary" onClick={() => onBack()}>Back to list</button>
        </div>
        <div style={{maxWidth: '400px'}}>
          <Exercise/>
        </div>
          <StudentAuditExercise/>
        </div>
      }
      </article>
    </div>
  );
}

const mapStateToProps = state => ({
  userResults: state.getIn(['results', 'detailResults', state.getIn(['results', 'selectedUser'])], immutable.Map({})),
  pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
  filter: state.getIn(['results', 'detailResultsFilters'], immutable.Map({requiredKeys: ['correct_deadline', 'image_deadline'], bonusKeys: ['correct_deadline','image_deadline']})),
  activeExercise: state.getIn(['results', 'detailResultExercise'], false),
  exerciseState: state.get('exerciseState'),
});

const mapDispatchToProps = dispatch => ({
  onExerciseClick: (exercise) =>  {
    dispatch(setDetailResultExercise(exercise));
    dispatch(fetchExercise(exercise, true));
  },
  onBack: () => dispatch(setDetailResultExercise(false))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStudentResults)
