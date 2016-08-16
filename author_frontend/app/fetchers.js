import { 
  updateExercises,
  updateExerciseXML,
  updateExerciseJSON,
  updateActiveExercise,
  setSavePendingState,
  setResetPendingState,
  setSaveError,
  setExerciseModifiedState
} from './actions.js';
import {logImmutable} from 'immutablehelpers.js'

function fetchExercises() {
  return dispatch => {
    return fetch('http://localhost:8000/exercises')
      //.then(response => {console.dir(response); return response;})
      .then(response => response.json())
      .then(json => dispatch(updateExercises(json)))
      .catch( err => console.log(err) );
  };
}


function fetchExerciseXML(exercise) {
  return dispatch => {
    return fetch('http://localhost:8000/exercise/' + exercise + '/xml')
      .then(res => res.text())
      .then( xml => dispatch(updateExerciseXML(exercise, xml)));
  }
}

function fetchExercise(exercise, empty) {
  return dispatch => {
    dispatch(updateActiveExercise(exercise));
    if(empty) {
    dispatch(setResetPendingState(exercise, true));
    return fetch('http://localhost:8000/exercise/' + exercise)
      .then(response => response.json())
      .then(json => {
        dispatch(fetchExerciseXML(exercise));
        dispatch(updateExerciseJSON(exercise, json));
        dispatch(setResetPendingState(exercise, false));
        dispatch(setExerciseModifiedState(exercise, false));
        dispatch(setSaveError(exercise, undefined));
      })
      .catch( err => console.log(err) );
  } else {
    return;
  }
  };
}

function saveExercise(exercise) {
  return (dispatch, getState) => {
    var state = getState();
    var xml = state.getIn(['exerciseState', exercise, 'xml']);
    var payload = {
      exercise: exercise,
      xml: xml
    }
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      body: data
    }
    dispatch(setSavePendingState(exercise, true));
    return fetch('http://localhost:8000/exercise/' + exercise + '/save', fetchconfig)
    .catch( err => console.dir("Fetch error" + err) )
    .then(res => res.json())
    .then( json => {
      if(_.get(json, 'success', false)) {
        dispatch(setSavePendingState(exercise, false));
        dispatch(setExerciseModifiedState(exercise, false));
        dispatch(setSaveError(exercise, false));
      } 
      else {
        dispatch(setSavePendingState(exercise, false));
        dispatch(setSaveError(exercise, true));
        console.log('Error while saving');
      }
    });
  }
}

export {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise,
  saveExercise
};
