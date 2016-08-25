import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercise,
  fetchExercises, 
  fetchSameFolder,
} from '../fetchers.js';

import immutable from 'immutable';

const BaseCourse = ({ exercisetree, currentpath, onExerciseClick }) => {
  function flatten(arr) {
    return arr.reduce( (flat, toFlat) => flat.concat( Array.isArray(toFlat) ? flatten(toFlat) : toFlat), [])
  }
  function parseFolder( folder, foldername ) {
    var exercises = [], children = [];
    if(folder.exercises) {
      exercises = Object.keys(folder.exercises).sort().map( exercise => (
        <li>
          <a className="uk-thumbnail" onClick={(ev) => onExerciseClick(exercise, foldername)}>
            <img className="exercise-thumb-nav" src={"/exercise/" + exercise + "/asset/thumbnail.png"}/>
            <div className="uk-thumbnail-caption">{exercise.split('.')[0]} {/*folder.exercises[exercise].correct ? "correct" : "incorrect"*/ }</div>
          </a>
        </li>));
        console.dir(folder.exercises);
    }
    if(folder.folders)
      children = Object.keys(folder.folders).sort().map ( childfolder => ({name: childfolder, content: parseFolder( folder.folders[childfolder].content, childfolder)}) );

    var DOM = (
      <div>
      <ul className="uk-thumbnav uk-flex uk-flex-bottom uk-flex-space-between">
        {exercises}
      </ul>
        <dl className="uk-description-list-line">
      { children.map( child => [
          (<dt className="uk-text-large"><i className="uk-icon uk-icon-navicon"></i> {child.name} </dt>),
          (<dd> {child.content} </dd>)]
      )
      }
        </dl>
      </div>
    );
    return DOM;
    //return exercises.concat( flatten(children) );
  }
  if(exercisetree) {
  console.dir(exercisetree);
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


