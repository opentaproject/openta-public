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

import immutable from 'immutable';
import moment from 'moment';

const BaseStudentResults = ({userResults, pendingResults, filter, onExerciseClick, activeExercise, onBack, exerciseState}) => {
  var required = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'required'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var bonus = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'bonus'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var n_required = required.filter( e =>
    filter.get('requiredKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;
  var n_bonus = bonus.filter( e =>
    filter.get('bonusKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;
  return (
    <div className="uk-panel uk-panel-box">
      <article className="uk-article">
      <h1 className="uk-article-title">
      { !pendingResults && userResults.get('first_name') + " " + userResults.get('last_name')}
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
            <tr key={e.get('exercise_key')} onClick={() => onExerciseClick(e.get('exercise_key'))}>
              <td>{e.get('name')}</td>
              <td>{(e.get('tries', 0) / e.get('questions').size).toFixed(1)}</td>
              <td>
                {filter.get('requiredKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b) ? <i className="uk-icon uk-icon-check uk-text-success"/> : <i className="uk-icon uk-icon-close uk-text-danger"/> }
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
            <tr key={e.get('exercise_key')} onClick={() => onExerciseClick(e.get('exercise_key'))}>
              <td>{e.get('name')}</td>
              <td>{(e.get('tries', 0) / e.get('questions').size).toFixed(1)}</td>
              <td>
                {filter.get('bonusKeys', []).map(key => e.get(key, false)).reduce( (a,b) => a && b) ? <i className="uk-icon uk-icon-check uk-text-success"/> : <i className="uk-icon uk-icon-close uk-text-danger"/> }
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
          <button onClick={() => onBack()}>Back</button>
        </div>
        <div style={{maxWidth: '300px'}}>
          <Exercise/>
        </div>
          { userResults.getIn(['exercises', activeExercise, 'questions']).map( (q, key) => (
        <div>
          <table className="uk-table uk-table-condensed">
            <thead>
              <tr>
                <th>{exerciseState.getIn([activeExercise, 'json', 'exercise', 'question', key, 'text', '$'], '')}  </th>
              </tr>
            </thead>
            <tbody>
                  {q.get('answers').map( a => (
                    <tr>
                      <td className={a.get('correct', false) ? 'uk-text-success' : 'uk-text-danger'}>
                        {a.get('answer')}
                      </td>
                    </tr>
                  ))}          
            </tbody>
          </table>
        </div>
          ))}
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
