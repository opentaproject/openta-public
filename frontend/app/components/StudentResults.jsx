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
          <button className="uk-button uk-button-primary" onClick={() => onBack()}>Back to list</button>
        </div>
        <div style={{maxWidth: '400px'}}>
          <Exercise/>
        </div>
        <div className="uk-panel uk-panel-box">
        <h3 className="uk-panel-title">{userResults.get('first_name') + ' ' + userResults.get('last_name')}</h3>
        <div className="uk-grid" style={{maxWidth: '700px'}}>
        <div className="uk-width-1-1 uk-flex"> 
          { userResults.getIn(['exercises', activeExercise, 'questions']).toList().map( (q, key) => (
        <div className="uk-display-inline-block uk-margin-right" key={key}>
          <table className="uk-table uk-table-condensed">
            <thead>
              <tr>
                <th style={{maxWidth: '300px'}}><MathSpan message={exerciseState.getIn([activeExercise, 'json', 'exercise', 'question', key, 'text', '$'], '')}/></th>
              </tr>
            </thead>
            <tbody>
                  {q.get('answers').map( a => (
                    <tr key={a.get('date')}>
                      <td className={a.get('correct', false) ? 'uk-text-success' : 'uk-text-danger'} title={moment(a.get('date')).format('YYYY-MM-DD HH:mm')} data-uk-tooltip>
                        {a.get('answer')}
                      </td>
                    </tr>
                  ))}          
            </tbody>
          </table>
        </div>
          ))}
        </div>
        <div className="uk-width-1-1">
        <ImageCollection srcs={userResults.getIn(['exercises', activeExercise,'imageanswers'], immutable.List([])).reverse().map( ia => "/"+SUBPATH+"imageanswer/"+ia.get('pk')).toJS()} badges={userResults.getIn(['exercises', activeExercise,'imageanswers'], immutable.List([])).reverse().map( ia => moment(ia.get('date')).format('YYYY-MM-DD HH:mm')).toJS()}/>
        </div>
        </div>
        </div>
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
