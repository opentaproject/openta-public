import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercise,
  fetchExerciseRemoteState,
  fetchExercises, 
  fetchSameFolder,
  fetchAddExercise,
  updatePendingStateIn,
} from '../fetchers.js';
import {
  updateExercises,
  updateExerciseTreeUI,
} from '../actions.js';
import {
  navigateMenuArray
} from '../menu.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import SafeImg from './SafeImg.jsx';
import AddExercise from './AddExercise.jsx';
import ExerciseHoverMenu from './ExerciseHoverMenu.jsx';
import FolderHoverMenu from './FolderHoverMenu.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

var difficulties = {
  '1': 'Lätt',
  '2': 'Medel',
  '3': 'Svår',
};

function generateItem(onExerciseClick, exercise, exerciseState, metaImmutable, folder, foldername, showStatistics, statistics, activityRange, author) {
  var meta = metaImmutable.toJS();
  var deadlineClass = "uk-badge-primary";
  var legend = 'Obligatorisk';
  if( meta.bonus ) {
    deadlineClass = "uk-badge-warning";
    legend = 'Bonus';
  }
  if(showStatistics) {
    var percent_complete = exerciseState.getIn([exercise, 'percent_complete'], 0);
    var percent_correct = exerciseState.getIn([exercise, 'percent_correct'], 0);
    var percent_tried = exerciseState.getIn([exercise, 'percent_tried'], 0);
    var maxActivity = statistics.getIn(['aggregates', 'max_' + activityRange], 0);
    var activity = 0;
    if(maxActivity > 0)
      activity = 100*exerciseState.getIn([exercise, 'activity', activityRange]) / maxActivity;
    if(percent_complete === null)percent_complete = 0;
    if(percent_correct === null)percent_correct = 0;
    if(percent_tried === null)percent_tried = 0;
  }
  var imageUploaded = exerciseState.getIn([exercise, 'image_answers'], immutable.List([])).size > 0;
  var imageUploadClass = imageUploaded ? "uk-badge-success" : "uk-badge-danger";
return (
  <li key={exercise} id={exercise} className="course-exercise-item ">
    <div className="uk-position-relative" data-uk-dropdown="{hoverDelayIdle: 0, delay: 300}">
    <a className={"uk-thumbnail exercise-a " + (meta.published ? "" : "exercise-unpublished")} onClick={(ev) => onExerciseClick(exercise, foldername)}>
        <div className="exercise-thumb-wrap" style={{minWidth: '80px'}}>
            <SafeImg className="exercise-thumb-nav" src={SUBPATH + "/exercise/" + exercise + "/asset/thumbnail.png"}><i className="uk-icon uk-icon-question-circle uk-icon-large"/></SafeImg>
            <div className="exercise-thumb-badge">
                { meta.difficulty && <Badge className="uk-badge-notification">{difficulties[meta.difficulty]}</Badge> }
                { meta.deadline_date && <Badge className={"uk-badge-notification " + deadlineClass} title={legend}>{moment(meta.deadline_date).format('D MMM')}</Badge> }
                { meta.image && <span className={"uk-badge uk-badge-notification " + imageUploadClass}><i className="uk-icon uk-icon-camera"/></span> }
                { meta.solution && <Badge className={"uk-badge-notification"}>lösning</Badge> }
                {exerciseState.getIn([exercise, 'correct'], false) && <span className="uk-badge uk-badge-notification uk-badge-success "><i className="uk-icon uk-icon-check"/></span> }
                {exerciseState.getIn([exercise, 'modified']) && <Badge className={"uk-badge-notification uk-badge-danger"}><i className="uk-icon uk-icon-save"/></Badge>}
                {exerciseState.getIn([exercise, 'audit', 'published'], false) && <Badge type={exerciseState.getIn([exercise, 'audit', 'revision_needed'], false) ? 'error' : 'success'} className={"uk-badge-notification"}>granskad</Badge> }
            </div>
        </div>
      <div className={"uk-thumbnail-caption exercise-thumb-nav-caption "}>
      {folder.getIn(['exercises',exercise, 'name'])}
      </div>
      { showStatistics && !meta.deadline_date &&
        <div className="uk-progress uk-margin-remove uk-progress-small uk-progress-warning" title="blue: correct, orange: tried">
          <div className="uk-progress-bar" style={{'width': (percent_correct*100) + '%', 'backgroundColor': '#00a8e6'}}></div>
          <div className="uk-progress-bar" style={{'width': ((percent_tried-percent_correct)*100) + '%'}}></div>
        </div>
      }
      { showStatistics && meta.deadline_date &&
        <div className="uk-progress uk-margin-remove uk-progress-small uk-progress-success" title="green: complete, blue: correct, orange: tried">
          <div className="uk-progress-bar" style={{'width': (percent_complete*100) + '%'}}></div>
          <div className="uk-progress-bar" style={{'width': ((percent_correct-percent_complete)*100) + '%', 'backgroundColor': '#00a8e6'}}></div>
          <div className="uk-progress-bar" style={{'width': ((percent_tried-percent_correct)*100) + '%', 'backgroundColor': '#faa732'}}></div>
        </div>
      }
      { activity >= 0 &&
      <div className="uk-progress uk-margin-remove uk-progress-small uk-progress-danger" title="Tries/Question">
        <div className="uk-progress-bar uk-text-small" style={{'width': activity + '%', 'backgroundColor': '#de96e2'}}>
        { activity >= 10 && <span className="uk-text-small">{exerciseState.getIn([exercise,'activity',activityRange])}</span>}
        { activity < 10 && activity > 0 && <span style={{position: 'relative', left: '200%'}} className="uk-text-danger uk-text-small">{exerciseState.getIn([exercise,'activity',activityRange])}</span>}
        { activity == 0 && <span className="uk-text-primary uk-text-small">0</span>}
        </div>
      </div>
      }
    </a>
      { author && 
    <div className="uk-dropdown uk-dropdown-small uk-margin-remove" style={{minWidth: 0}}>
      <ExerciseHoverMenu exerciseKey={exercise}/>
    </div>
      }
    </div>
  </li>);
}


const BaseCourse = ({ exercisetree, exerciseTreeUI, exerciseState, pendingState, currentpath, onExerciseClick, showStatistics, statistics, activityRange, onFolderClick, student, onExerciseAdd, pendingExerciseAdd, author }) => {
  function flatten(arr) {
    return arr.reduce( (flat, toFlat) => flat.concat( Array.isArray(toFlat) ? flatten(toFlat) : toFlat), [])
  }
  function countFinished(folder, name, type) {
    if(folder.has('exercises')) {
        var results = folder.get('exercises').filter( e => e.getIn(['meta', type]))
                               .map( (e, key) => exerciseState.getIn([key, 'correct'], false) );
        return {
          total: results.size,
          correct: results.filter( x => x).size
        }
      }
      else
        return {
          total: 0,
          correct: 0
        };
  }
  function parseFolder( folder, foldername, level=0 ) {
    var exercises = immutable.List([]), children = [];
    if(folder.has('exercises')) {
      exercises = folder.get('order').map( exercise => {
        var meta = folder.getIn(['exercises', exercise, 'meta']);
        return generateItem(onExerciseClick, exercise, exerciseState, meta, folder, foldername, showStatistics, statistics, activityRange, author);
      })
    }
    exercises = exercises.push(( <AddExercise key="addExercise" path={folder.get('path')}/>));
    if(folder.has('folders'))
      children = folder.get('folders', immutable.Map({})).keySeq().sort().map ( childfolder => 
                                                          ({
                                                            name: childfolder, 
                                                            folder: folder.getIn(['folders', childfolder, 'content']), 
                                                            content: parseFolder( folder.getIn(['folders', childfolder, 'content']), childfolder, level + 1), 
                                                            path: folder.getIn(['folders', childfolder, 'content', 'path']),
                                                            folded: exerciseTreeUI.getIn(folder.getIn(['folders', childfolder, 'content', 'path']).push('$folded$'), true),
                                                            pending: exerciseTreeUI.getIn(folder.getIn(['folders', childfolder, 'content', 'path']).push('$pending$'), false)
                                                          }) );
    var levelClass = "";
    switch(level) {
      case 1:
        levelClass = "uk-block-muted"; break;
      case 0:
        levelClass = "uk-block-muted"; break;
    }
    var DOM = (
      <div className={"uk-block uk-padding-remove " + levelClass}>
      <div className="uk-container uk-margin-small-left uk-margin-small-right uk-padding-remove">
      <ul className="uk-thumbnav uk-flex uk-flex-bottom uk-padding-remove">
        {exercises}
      </ul>
        <dl className="uk-description-list-horizontal">
      { children.map( child => {
        var folderPrename = child.name.split('.')[0].split(':');
        var folderName = folderPrename[folderPrename.length - 1]
        var folderClass = child.folded ? 'uk-icon-folder' : 'uk-icon-folder-open';
        var summaryReq = countFinished(child.folder, child.name, 'required');
        if(summaryReq.total > 0) 
          var percentReq = 100 * summaryReq.correct / summaryReq.total;
        var summaryBonus = countFinished(child.folder, child.name, 'bonus');
        if(summaryBonus.total > 0)
          var percentBonus = 100 * summaryBonus.correct / summaryBonus.total;
        var rendered = [
          (<dt className="uk-text-large uk-margin-right" style={{float:'none', overflow:'visible', width: 'auto'}} key={"dt"+child.name}>
            <div className="uk-position-relative uk-display-inline" data-uk-dropdown="{hoverDelayIdle: 0, delay: 300, pos: 'right-center'}">
            <a onClick={ () => onFolderClick(child.path, child.folded) }>
              <i className={"uk-icon " + folderClass}/>
              {
                folderName === 'Trash' &&
                <i className='uk-icon uk-icon-trash uk-margin-small-left'/>
              }
                <span className="uk-margin-small-left">
                  {folderName}
                  {child.pending && <Spinner size=""/>}
                  {child.pending === null && <i className="uk-icon uk-icon-exclamation-triangle"/>}
                </span>
                  { student && false &&
                  <div className="uk-grid">
                  { summaryReq.total > 0 &&
                  <div className="uk-width-1-1 uk-progress uk-margin-remove uk-padding-remove uk-progress-mini uk-progress-success">
                    <div className="uk-progress-bar" style={{'width': percentReq + '%'}}></div>
                  </div>
                  }
                  { summaryBonus.total > 0 &&
                  <div className="uk-width-1-1 uk-progress uk-margin-remove uk-padding-remove uk-progress-mini uk-progress-warning">
                    <div className="uk-progress-bar" style={{'width': percentBonus + '%'}}></div>
                  </div>
                  }
                  </div>
                  }
            </a>
              { author && 
            <div className="uk-dropdown uk-dropdown-small uk-margin-small" style={{minWidth: 0, paddingLeft: '5px', paddingRight:'5px', paddingTop: 0, paddingBottom: 0}}>
                <FolderHoverMenu folderPath={child.path}/>
            </div>
              }
            </div>
            </dt>)];
        if(!child.folded) 
          rendered.push((<dd className="uk-margin-left" key={"dd"+child.name}> {child.content} </dd>));
        return rendered;
      }
      )
      }
        </dl>
        </div>
      </div>
    );
    return DOM;
  }
  if(pendingState.getIn(['course', 'loadingExercises'], false)) {
      return (<Spinner/>);
  }
  if(exercisetree) {
  var top = parseFolder(exercisetree, "/");
  return (
  <div className="uk-content-center">
    <ul className="uk-list">
      {top}
    </ul>
  </div>
);
  } 
  else {
      return (<Spinner/>);
  }
}

const handleAddExercise = (path) => dispatch => {
    console.dir("Will add exercise at " + path)
    return dispatch(fetchAddExercise(path));
}

const mapStateToProps = state => ({
    exerciseState: state.get('exerciseState'),
    pendingState: state.get('pendingState'),
    exercisetree: state.get('exerciseTree'),
    exerciseTreeUI: state.get('exerciseTreeUI'),
    currentpath: state.get('currentpath'),
    showStatistics: state.getIn(['login', 'groups'], immutable.List([])).includes('View'),
    statistics: state.get('statistics', immutable.Map({})),
    activityRange: state.get('activityRange', '1h'),
    student: state.getIn(['login', 'groups'], immutable.List([])).includes('Student'),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author')
});

const mapDispatchToProps = dispatch => ({
  onExerciseClick: (exercise, folder) => {
    dispatch(updatePendingStateIn( ['exerciseList'], true));
    dispatch(fetchExerciseRemoteState(exercise))
      .then(dispatch(fetchExercise(exercise, true)))
      .then(dispatch(navigateMenuArray(['activeExercise'])));
    dispatch(updateExercises([], folder));
    dispatch(fetchSameFolder(exercise, folder));
  },
  onFolderClick: (path, folded) => {
    var fullPath = immutable.List(path).push('$folded$');
    var updated = immutable.Map({}).setIn(fullPath, !folded)
    dispatch(updateExerciseTreeUI(updated))
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourse);


