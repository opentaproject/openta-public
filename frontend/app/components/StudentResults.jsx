import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercise
} from '../fetchers.js';
import {
  setResultsFilter,
  setDetailResultExercise,
  setDetailResultsView,
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

const BaseStudentResults = ({userResults, 
                            pendingResults, 
                            filter, 
                            onExerciseClick, 
                            activeExercise, 
                            onBack, 
                            exerciseState, 
                            detailResultsView,
                            onChangeView}) => {
  var required = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'required'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var bonus = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'bonus'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var optional = userResults.get('exercises', immutable.Map({})).filter( item => (!item.getIn(['meta', 'required']))&&(!item.getIn(['meta', 'bonus']))).toList().sortBy( item => item.get('folder') + item.getIn(['meta', 'sort_key'])); 
  var optionalByFolder = optional.groupBy(item => item.get('folder'))
                                 .toOrderedMap()
                                 .sortBy( (v, k) => k);
  var optionalByFolderSorted = optionalByFolder.map( folder => folder.sortBy( item => item.getIn(['meta', 'sort_key']) ));

  var n_required = required.filter( e =>
    filter.get('requiredKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;
  var n_bonus = bonus.filter( e =>
    filter.get('bonusKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;

  const renderExercises = (exercises, caption, columnName) => (
      <table className="uk-table uk-table-hover">
        <caption className="uk-text-primary uk-text-bold">{ caption }</caption>
        <thead>
          <tr>
            <th>{columnName}</th>
            <th>Tries/Q</th>
            <th>Passed</th>
          </tr>
        </thead>
        <tbody>
           { exercises.map( e => (
            <tr key={e.get('exercise_key')} onClick={() => onExerciseClick(e.get('exercise_key'))} className="pointer">
              <td>
                {e.get('name')}
                <img style={{height:'30px', maxWidth:'40px'}} className="exercise-thumb-nav" src={SUBPATH + "/exercise/" + e.get('exercise_key') + "/asset/thumbnail.png"}/>
              </td>
              <td>{(e.get('tries', 0) / e.get('questions').size).toFixed(1)}</td>
              <td>
                      <i className={'uk-margin-small-right uk-icon ' + (e.get('correct', false) ? 'uk-icon-check uk-text-success' : 'uk-icon-close uk-text-danger')}/>
                      <i className={'uk-margin-small-right uk-icon uk-icon-picture-o ' + (e.get('imageanswers', immutable.List([])).size > 0 ? 'uk-text-success' : 'uk-text-danger')}/>
                      <i className={'uk-margin-small-right uk-icon uk-icon-clock-o ' + (e.get('image_deadline', false) && e.get('correct_deadline',false) ? 'uk-text-success' : 'uk-text-danger')}/> 
              </td>
            </tr>
          )) }
        </tbody>
      </table> );
      var safeActivity = (item) => item.get('questions').size > 0 ? (item.get('tries') / item.get('questions').size) : 0;
      if(optional.size > 0)
        var maxOptionalActivity = safeActivity(optional.maxBy(item => safeActivity(item) ))
  return (
    <div className="uk-panel uk-panel-box" id="studentresults" style={ activeExercise ? {} : {}}>
      <article className="uk-article">
      <div className="uk-flex">
      
      { !pendingResults && !activeExercise && 
        <h1 className="uk-article-title">
        {userResults.get('username')/*userResults.get('first_name') + " " + userResults.get('last_name')*/}
        </h1>
      }
      { pendingResults && <Spinner/> }

      { !pendingResults && !activeExercise &&
      <div className="uk-button-group uk-margin-left">
        <a onClick={() => onChangeView('graded')} className={detailResultsView==="graded" ? 'uk-button uk-button-primary' : 'uk-button'}>Graded</a>
        <a onClick={() => onChangeView('optional')} className={detailResultsView==="optional" ? 'uk-button uk-button-primary' : 'uk-button'}>Optional</a>
      </div>
      }
      </div>
      { !pendingResults && !activeExercise && detailResultsView === 'graded' &&
      <div className="uk-grid">
      <div>
          { renderExercises(required, "Obligatory " + n_required +'/'+ required.size, 'Obligatory') }
      </div>
      <div>
          { renderExercises(bonus, "Bonus " + n_bonus + '/' + bonus.size, 'Bonus') }
      </div>
      </div>
      }
      
      { !pendingResults && !activeExercise && detailResultsView === 'optional' &&
        <div>
        { optionalByFolderSorted.map( (folder, key) => (
        <ul key={key} className="uk-thumbnav uk-flex uk-margin-small" style={{maxWidth: '500px'}}>
        {folder.map( item => (
            <li key={item.get('exercise_key')} className="uk-margin-remove">
              <a className="uk-thumbnail" style={{
                borderColor: item.get('correct') ? '#00dd00' : (item.get('tries') > 0 ? '#ff0000' : '#929292'),
                borderWidth: item.get('tries') > 0 ? '2px' : '1px',
              }}
                 onClick={() => onExerciseClick(item.get('exercise_key'))}
              >
                <img style={{height:'30px'}} className="exercise-thumb-nav" src={SUBPATH + "/exercise/" + item.get('exercise_key') + "/asset/thumbnail.png"}/>
                <div className="uk-thumbnail-caption uk-text-small">{item.get('name')}</div>
                <div className="uk-progress uk-margin-remove uk-progress-mini uk-progress-danger" title="Tries/Question">
                  <div className="uk-progress-bar uk-text-small" style={{'width': (100 * safeActivity(item) / maxOptionalActivity) + '%', 'backgroundColor': '#e62ef1'}}>
                  </div>
                </div>
              </a>
            </li>
         ))}
        </ul>
        )).toList().interpose( (<hr className="uk-margin-small"/>)) }
        </div>
      }
      { !pendingResults && activeExercise &&
        <div className="uk-flex uk-flex-wrap uk-flex-space-around">
        <div className="uk-width-1-1">
          <button className="uk-button uk-button-primary" onClick={() => onBack()}>Back to list</button>
        </div>
        <div style={{maxWidth: '400px'}}>
          <Exercise/>
        </div>
          <StudentAuditExercise anonymous={true}/>
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
  detailResultsView: state.getIn(['results', 'detailResultsView']),
});

const mapDispatchToProps = dispatch => ({
  onExerciseClick: (exercise) =>  {
    dispatch(setDetailResultExercise(exercise));
    dispatch(fetchExercise(exercise, true));
  },
  onBack: () => dispatch(setDetailResultExercise(false)),
  onChangeView: (view) => dispatch(setDetailResultsView(view)),
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStudentResults)
