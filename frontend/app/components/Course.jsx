import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercise,
  fetchExerciseRemoteState,
  fetchExercises, 
  fetchSameFolder,
  updatePendingStateIn,
} from '../fetchers.js';
import {
  updateExercises,
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

var difficulties = {
  '1': 'Lätt',
  '2': 'Medel',
  '3': 'Svår',
};

function generateItem(onExerciseClick, exercise, exerciseState, meta, folder, foldername) {
  var deadlineClass = "uk-badge-primary";
  if( meta.bonus )
    deadlineClass = "uk-badge-warning";
return (
  <li key={exercise} id={exercise} className="course-exercise-item">
    <a className={"uk-thumbnail " + (meta.published ? "" : "exercise-unpublished")} onClick={(ev) => onExerciseClick(exercise, foldername)}>
    <div className="exercise-thumb-wrap">
      <img className="exercise-thumb-nav" src={SUBPATH + "/exercise/" + exercise + "/asset/thumbnail.png"}/>
      <div className="exercise-thumb-badge">
      {exerciseState.getIn([exercise, 'correct'], false) && <span className="uk-badge uk-badge-notification uk-badge-success "><i className="uk-icon uk-icon-check"/></span> }
      { meta.difficulty && <Badge className="uk-badge-notification">{difficulties[meta.difficulty]}</Badge> }
      { /*meta.required && <Badge className="uk-badge-notification"><i className="uk-icon uk-icon-asterisk" title="Obligatorisk"/></Badge> */ }
      { /*meta.bonus && <Badge className="uk-badge-notification uk-badge-warning"><i className="uk-icon uk-icon-plus uk-text-bold " title="Bonus"/></Badge> */}
      { meta.deadline_date && <Badge className={"uk-badge-notification " + deadlineClass}><i className="uk-icon uk-icon-calendar uk-text-bold uk-margin-small-right" title="Bonus"/>{moment(meta.deadline_date).format('D MMM')}</Badge> }
      { meta.solution && <Badge className={"uk-badge-notification"}>pdf</Badge> }
      </div>
      </div>
      <div className={"uk-thumbnail-caption exercise-thumb-nav-caption "}>
      {folder.exercises[exercise].name}
      </div>
    </a>
  </li>);
}

const BaseCourse = ({ exercisetree, exerciseState, pendingState, currentpath, onExerciseClick }) => {
  function flatten(arr) {
    return arr.reduce( (flat, toFlat) => flat.concat( Array.isArray(toFlat) ? flatten(toFlat) : toFlat), [])
  }
  function parseFolder( folder, foldername ) {
    var exercises = [], children = [];
    if(folder.exercises) {
      //exerciseState.getIn([exercise, 'correct'], false)
      exercises = folder.order/*Object.keys(folder.exercises)/*.sort( (a,b) => folder.exercises[a].name > folder.exercises[b].name )*/.map( exercise => {
        var meta = folder.exercises[exercise].meta;
        return generateItem(onExerciseClick, exercise, exerciseState, meta, folder, foldername);
      });
    }
    if(folder.folders)
      children = Object.keys(folder.folders).sort().map ( childfolder => ({name: childfolder, content: parseFolder( folder.folders[childfolder].content, childfolder)}) );

    var DOM = (
      <div>
      <ul className="uk-thumbnav uk-flex uk-flex-bottom ">
        {exercises}
      </ul>
        <dl className="uk-description-list-line">
      { children.map( child => [
          (<dt className="uk-text-large" key={"dt"+child.name}><i className="uk-icon uk-icon-folder-open"></i> {child.name.split('.')[0]} </dt>),
          (<dd key={"dd"+child.name}> {child.content} </dd>)]
      )
      }
        </dl>
      </div>
    );
    return DOM;
    //return exercises.concat( flatten(children) );
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

const mapStateToProps = state => ({
  exerciseState: state.get('exerciseState'),
  pendingState: state.get('pendingState'),
  exercisetree: state.get('exerciseTree'),
  currentpath: state.get('currentpath')
});

const mapDispatchToProps = dispatch => ({
  onExerciseClick: (exercise, folder) => {
    dispatch(updatePendingStateIn( ['exerciseList'], true));
    dispatch(fetchExerciseRemoteState(exercise))
      .then(dispatch(fetchExercise(exercise, true)));
    dispatch(updateExercises([], folder));
    dispatch(fetchSameFolder(exercise, folder));
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourse);


