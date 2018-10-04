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
import MathSpan from './MathSpan.jsx';
import ImageCollection from './ImageCollection.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import Audit from './Audit.jsx';
import { menuPositionAt, menuPositionUnder, navigateMenuArray } from '../menu.js';

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
                            menuPath,}) => {
  var required = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'required'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  var bonus = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'bonus'])).toList().sortBy(item => item.getIn(['meta','deadline_date']));
  //var optional = userResults.get('exercises', immutable.Map({})).filter( item => (!item.getIn(['meta', 'required']))&&(!item.getIn(['meta', 'bonus']))).toList().sortBy( item => item.get('folder') + item.getIn(['meta', 'sort_key'])); 
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

      { !pendingResults && !activeExercise &&
      <div className="uk-button-group uk-margin-left">
        <a onClick={() => onChangeView('all')} className={detailResultsView==="all" ? 'uk-button uk-button-primary' : 'uk-button'}>All</a>
        <a onClick={() => onChangeView('graded')} className={detailResultsView==="graded" ? 'uk-button uk-button-primary' : 'uk-button'}>Graded</a>
        <a onClick={() => onChangeView('optional')} className={detailResultsView==="optional" ? 'uk-button uk-button-primary' : 'uk-button'}>Optional</a>
      </div>
      }
      </div> );//}}}
  var exercisesFilteredList = optionalByFolderSorted
    .map((folder, key) => {
      return <div className="uk-panel uk-margin-small-top" key={key}>
          <h5 className="uk-margin-remove uk-text-success">{key}</h5>
          <ul key={key} className="uk-thumbnav uk-flex uk-margin-small-top" style={{ maxWidth: "500px" }}>
            {folder.map(item => {
              var imageRequired = item.getIn(["meta", "image"], false);
              var imageBeforeDeadline = item.get('image_deadline', false);
              var correctBeforeDeadline = item.get('correct_deadline', false);
              var beforeDeadline = null;
              if(imageRequired)
                if(imageBeforeDeadline && correctBeforeDeadline)
                  beforeDeadline = true;
                else
                  beforeDeadline = false;
              if(!imageRequired)
                if(correctBeforeDeadline)
                  beforeDeadline = true;
                else
                  beforeDeadline = false;
              return <li key={item.get("exercise_key")} className="uk-margin-remove">
                  <a className="uk-thumbnail uk-margin-small-top" style={{ borderColor: item.get("correct") ? "#00dd00" : item.get("tries") > 0 ? "#ff0000" : "#929292", borderWidth: item.get("tries") > 0 ? "2px" : "1px" }} onClick={() => onExerciseClick(item.get("exercise_key"))}>
                    <div className="exercise-thumb-wrap">
                      <div className="uk-flex">
                        <img style={{ height: "30px" }} className="exercise-thumb-nav" src={SUBPATH + "/exercise/" + item.get("exercise_key") + "/asset/thumbnail.png"} />
                        {item.getIn(["meta", "deadline_date"], false) && <div className="uk-flex uk-flex-column">
                            <div style={{ lineHeight: "0" }}>
                              {imageRequired && <i className={"uk-icon uk-icon-picture-o " + (item.get("imageanswers", immutable.List([])).size > 0 ? "uk-text-success" : "uk-text-danger")} />}
                            </div>
                            <div style={{ lineHeight: "0" }}>
                              {beforeDeadline !== null && <i className={"uk-icon uk-icon-clock-o " + (beforeDeadline ? "uk-text-success" : "uk-text-danger")} />}
                            </div>
                            {item.get("force_passed") && <div style={{ lineHeight: "0" }}>
                                <i className="uk-margin-small-right uk-icon uk-icon-exclamation-circle uk-text-success" title="Manually passed" />
                              </div>}
                          </div>}
                      </div>
                      <div style={{ position: "absolute", left: "-10px", top: "-10px" }}>
                        {item.getIn(["meta", "bonus"]) && <Badge className="uk-badge-warning">
                            {item.getIn([
                              "meta",
                              "deadline_date"
                            ]) && moment(item.getIn(["meta", "deadline_date"])).format("D MMM")}
                            {!item.getIn(["meta", "deadline_date"]) && <span>bonus</span>}
                          </Badge>}
                        {item.getIn(["meta", "required"]) && <Badge className="">
                            {item.getIn([
                              "meta",
                              "deadline_date"
                            ]) && moment(item.getIn(["meta", "deadline_date"])).format("D MMM")}
                            {!item.getIn(["meta", "deadline_date"]) && <span>required</span>}
                          </Badge>}
                      </div>
                      <div className="uk-thumbnail-caption uk-text-small">{item.get("name")}</div>
                      <div className="uk-progress uk-margin-remove uk-progress-mini uk-progress-danger" title="Tries/Question">
                        <div className="uk-progress-bar uk-text-small" style={{ width: (100 * safeActivity(item)) / maxOptionalActivity + "%", backgroundColor: "#e62ef1" }} />
                      </div>
                    </div>
                  </a>
                </li>;
            })}
          </ul>
          <hr className="uk-margin-remove" />
        </div>;
    })
    .toList();
  return (
    <div className="uk-panel uk-panel-box uk-width-1-1" id="studentresults" style={ activeExercise ? {} : {}}>
      <article className="uk-article uk-width-1-1">
      { menuPositionAt(menuPath, ['results', 'list']) && pendingResults &&
        <Spinner/>
      }
      { typeFilterMenu }
      { !pendingResults && !activeExercise && menuPositionAt(menuPath, ['results', 'list']) &&
        <div>
          {exercisesFilteredList }
        </div>
      }
      { activeExercise && menuPositionUnder(menuPath, ['results', 'list']) &&
        <div className="uk-flex uk-flex-wrap uk-flex-space-around uk-width-1-1">
        <div className="uk-width-1-1">
          <button className="uk-button uk-button-primary" onClick={() => onBack()}>Back to list</button>
          <button className={"uk-button uk-button-primary uk-margin-left " + (menuPositionAt(menuPath, ['results', 'list', 'audit']) ? 'uk-active' : '')} onClick={() => onAudit(activeExercise, userResults.get('pk'))}>Audit</button>
        </div>
        { menuPositionAt(menuPath, ['results', 'list']) &&
        <div className="uk-width-1-4">
          <Exercise/>
        </div>
        }
        { menuPositionAt(menuPath, ['results', 'list']) &&
        <div className="uk-width-3-4">
          <StudentAuditExercise anonymous={true}/>
        </div>
        }
        { menuPositionAt(menuPath, ['results', 'list', 'audit']) &&
          <Audit/>
        }
        </div>
      }
      </article>
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
