import React from 'react';
import { connect } from 'react-redux';
import {
  fetchCurrentAuditsExercise,
  fetchExercise,
  addAudit
} from '../fetchers.js';
import {
  setActiveAudit,
  setResultsFilter,
  setDetailResultExercise,
  setDetailResultsView,
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Exercise from './Exercise.jsx';
import ExerciseItem from './ExerciseItem.jsx';
import SummaryBar from "./SummaryBar.jsx"
import MathSpan from './MathSpan.jsx';
import ImageCollection from './ImageCollection.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import Audit from './Audit.jsx';
import { menuPositionAt, menuPositionUnder, navigateMenuArray } from '../menu.js';
import Course from "./Course.jsx"

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
                            onChangeView,
                            onAudit,
                            menuPath,
                            displaystyle }) => {
  var required = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'required'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var bonus = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'bonus'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  //var optional = userResults.get('exercises', immutable.Map({})).filter( item => (!item.getIn(['meta', 'required']))&&(!item.getIn(['meta', 'bonus']))).toList().sortBy( item => item.get('folder') + item.getIn(['meta', 'sort_key'])); 
  var user_pk= userResults.get('pk')
  var optional = userResults.get('exercises', immutable.Map({})).filter( item => {
    switch(detailResultsView) {
      case 'graded':
        return item.getIn(['meta', 'required']) || item.getIn(['meta','bonus']);
      case 'optional':
        return !(item.getIn(['meta', 'required']) || item.getIn(['meta','bonus']));
      case 'all':
        return true
    }
  })
                            .toList().sortBy( item => item.get('folder') + item.getIn(['meta', 'sort_key'])); 
  var optionalByFolder = optional.groupBy(item => item.get('folder'))
                                 .toOrderedMap()
                                 .sortBy( (v, k) => k);
  var optionalByFolderSorted = optionalByFolder.map( folder => folder.sortBy( item => item.getIn(['meta', 'sort_key']) ));

  var n_required = required.filter( e =>
    filter.get('requiredKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;
  var n_bonus = bonus.filter( e =>
    filter.get('bonusKeys').map(key => e.get(key, false)).reduce( (a,b) => a && b)).size;

  var safeActivity = (item) => item.get('questions').size > 0 ? (item.get('tries') / item.get('questions').size) : 0;
  if(optional.size > 0)
    var maxOptionalActivity = safeActivity(optional.maxBy(item => safeActivity(item) ))




  var typeFilterMenu = //{{{
    (
      <div className="uk-flex uk-margin-bottom">
      { !pendingResults && !activeExercise &&
      <div className="uk-button-group uk-margin-right">
        <a onClick={(e) => UIkit.modal.confirm("Log in as user " + userResults.get('username') + "?", () => window.open(SUBPATH + "/hijack/username/"+userResults.get('username') , "_self"))} className="uk-button uk-alert-warning" data-uk-tooltip title="Log in as user"> {userResults.get('username')} 
        </a>
      </div>
      }

      </div> );//}}}
  return (
    <div className="uk-panel uk-panel-box uk-width-1-1" id="studentresults" style={ activeExercise ? {} : {}}>
      { menuPositionAt(menuPath, ['results', 'list']) && pendingResults && <Spinner/> }
      { typeFilterMenu }
      { !pendingResults && !activeExercise && menuPositionAt(menuPath, ['results', 'list']) && <div> 
                <Course onExerciseClick={onExerciseClick} compact={true} user_pk={user_pk} /> </div> }
      { activeExercise && menuPositionUnder(menuPath, ['results', 'list']) &&
        <div className="uk-flex uk-flex-wrap uk-flex-space-around uk-width-1-1">
        <div className="uk-width-1-1">
          <button className="uk-button uk-button-primary" onClick={() => onBack()}>Back to list</button>
          <button className={"uk-button uk-button-primary uk-margin-left " + (menuPositionAt(menuPath, 
                ['results', 'list', 'audit']) ? 'uk-active' : '')} onClick={() => onAudit(activeExercise, userResults.get('pk'))}>Audit</button>
        </div>
        { menuPositionAt(menuPath, ['results', 'list']) && <div className=""> <Exercise/> </div> }
        { menuPositionAt(menuPath, ['results', 'list']) && <div className=""> <StudentAuditExercise anonymous={true}/> </div> }
        { menuPositionAt(menuPath, ['results', 'list', 'audit']) && <Audit/> } </div> 
    } 
    </div> 
); 

}

const handleAudit = (exercise, studentPk) => dispatch => {
  dispatch(navigateMenuArray(['results', 'list', 'audit']))
  dispatch(setDetailResultExercise(exercise));
  dispatch(addAudit(exercise, studentPk))
    .then(res => {
      dispatch(fetchCurrentAuditsExercise())
        .then(() => dispatch(setActiveAudit(res.pk)))
    });
  //dispatch(setActiveAudit(auditPk));
  //dispatch(fetchStudentDetailResults(studentPk));
  //dispatch(setSelectedStudentResults(studentPk));
}

const mapStateToProps = state => ({
  userResults: state.getIn(['results', 'detailResults', state.getIn(['results', 'selectedUser'])], immutable.Map({})),
  pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
  filter: state.getIn(['results', 'detailResultsFilters'], immutable.Map({requiredKeys: ['correct_deadline', 'image_deadline'], bonusKeys: ['correct_deadline','image_deadline']})),
  activeExercise: state.getIn(['results', 'detailResultExercise'], false),
  exerciseState: state.get('exerciseState'),
  detailResultsView: state.getIn(['results', 'detailResultsView']),
  menuPath: state.get('menuPath'),
  displaystyle: state.get("displaystyle"),
  

});

const mapDispatchToProps = dispatch => ({
  onExerciseClick: (exercise) =>  {
    dispatch(setDetailResultExercise(exercise));
    dispatch(fetchExercise(exercise, true));
  },
  onBack: () => {
    dispatch(setDetailResultExercise(false))
    dispatch(navigateMenuArray(['results', 'list']))
  },
  onAudit: (exercise, studentPk) => dispatch(handleAudit(exercise, studentPk)),
  onChangeView: (view) => dispatch(setDetailResultsView(view)),
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStudentResults)
