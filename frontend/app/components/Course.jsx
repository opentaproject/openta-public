import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercise,
  fetchExercises, 
  fetchSameFolder,
} from '../fetchers.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';

import immutable from 'immutable';

var difficulties = {
  '1': 'Lätt',
  '2': 'Medel',
  '3': 'Svår',
};

const BaseCourse = ({ exercisetree, exerciseState, currentpath, onExerciseClick }) => {
  function flatten(arr) {
    return arr.reduce( (flat, toFlat) => flat.concat( Array.isArray(toFlat) ? flatten(toFlat) : toFlat), [])
  }
  function parseFolder( folder, foldername ) {
    var exercises = [], children = [];
    if(folder.exercises) {
      //exerciseState.getIn([exercise, 'correct'], false)
      exercises = Object.keys(folder.exercises).sort( (a,b) => folder.exercises[a].name > folder.exercises[b].name ).map( exercise => {
        var meta = folder.exercises[exercise].meta;
        return (
        <li key={exercise}>
          <a className="uk-thumbnail" onClick={(ev) => onExerciseClick(exercise, foldername)}>
          <div className="exercise-thumb-wrap">
            <img className="exercise-thumb-nav" src={"/exercise/" + exercise + "/asset/thumbnail.png"}/>
            <div className="exercise-thumb-badge">
            {exerciseState.getIn([exercise, 'correct'], false) && <span className="uk-badge uk-badge-notification uk-badge-success "><i className="uk-icon uk-icon-check"/></span> }
            { meta.difficulty && <Badge className="uk-badge-notification">{difficulties[meta.difficulty]}</Badge> }
            { meta.required && <Badge className="uk-badge-notification"><i className="uk-icon uk-icon-asterisk" title="Obligatorisk"/></Badge> }
            { meta.bonus && <Badge className="uk-badge-notification uk-badge-warning"><i className="uk-icon uk-icon-plus uk-text-bold " title="Bonus"/></Badge> }
            </div>
            </div>
            <div className={"uk-thumbnail-caption exercise-thumb-nav-caption "}>
            {folder.exercises[exercise].name}
            </div>
          </a>
        </li>)
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
          (<dt className="uk-text-large" key={"dt"+child.name}><i className="uk-icon uk-icon-navicon"></i> {child.name.split('.')[0]} </dt>),
          (<dd key={"dd"+child.name}> {child.content} </dd>)]
      )
      }
        </dl>
      </div>
    );
    return DOM;
    //return exercises.concat( flatten(children) );
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
    return (<div></div>);
  }
}

const mapStateToProps = state => ({
  exerciseState: state.get('exerciseState'),
  exercisetree: state.get('exerciseTree'),
  currentpath: state.get('currentpath')
});

const mapDispatchToProps = dispatch => ({
  onExerciseClick: (exercise, folder) => {
    dispatch(fetchExercise(exercise, true));
    dispatch(fetchSameFolder(exercise, folder));
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourse);


