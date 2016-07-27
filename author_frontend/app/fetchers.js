import { 
  updateExercises,
  updateActiveExerciseXML,
  updateActiveExerciseName,
  updateActiveExercise
} from './actions.js';

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
      .then( xml => dispatch(updateActiveExerciseXML(exercise, xml)));
  }
}

function fetchExercise(exercise) {
  return dispatch => {
    dispatch(updateActiveExerciseName(exercise));
    return fetch('http://localhost:8000/exercise/' + exercise)
      .then(response => response.json())
      .then(json => {
        dispatch(fetchExerciseXML(exercise));
        dispatch(updateActiveExercise(json));
      })
      .catch( err => console.log(err) );
  };
}

export {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise 
};
