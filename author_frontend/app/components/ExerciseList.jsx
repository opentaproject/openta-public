import React, { PropTypes } from 'react';
import { connect } from 'react-redux';

function listClass(item, active) {
  if(item === active)return "uk-active";
  else return "";
}

const BaseExercises = ({ exerciselist, activeExercise, onExerciseClick, onExercisesClick }) => (
  <div className="uk-width-medium-1-4">
    <div className="uk-panel uk-panel-box uk-margin-top">
    <h3 className="uk-panel-title">Exercises</h3>
    <ul className="uk-nav uk-nav-side uk-list-line">
    {/*<ul className="uk-thumbnav">*/}
    {exerciselist.map( exercise => ( 
                      <li className={exercise === activeExercise ? "uk-active" : ""}>
                        <a onClick={() => onExerciseClick(exercise)}>
                          <ul>
                          <li><img className="uk-margin-right" style={{maxHeight: '40px'}} height="40px" src={'http://localhost:8000/exercise/' + exercise + '/thumbnail.png'}/>
                          <li>{exercise}</li>
                          </li>
                          </ul>
                        </a>
                      </li>
                                   )
                     )}
    {/* //{exerciselist.map( exercise => { return <span>{exercise}</span> } )}
      //<button onClick={onMinusClick}>-</button>
      //{count}
      //<button onClick={onPlusClick}>+</button>} */}
    </ul>
    </div>
  <button className="uk-margin-top" onClick={onExercisesClick}>Fetch</button>
  </div>
);

BaseExercises.propTypes = {
  exerciselist: PropTypes.array.isRequired,
  activeExercise: PropTypes.string,
  onExerciseClick: PropTypes.func.isRequired,
  onExercisesClick: PropTypes.func.isRequired
};

const mapStateToProps = state => (
  {
    exerciselist: state.exercises,
    activeExercise: state.activeExercise }
);

function updateExercises(exercises) {
  return {
    type: 'UPDATE_EXERCISES',
    exercises: exercises
  };
}

function fetchExercises() {
  return dispatch => {
    return fetch('http://localhost:8000/exercises')
      //.then(response => {console.dir(response); return response;})
      .then(response => response.json())
      .then(json => dispatch(updateExercises(json)))
      .catch( err => console.log(err) );
  };
}

function updateActiveExercise(exerciseJSON) {
  return {
    type: 'UPDATE_ACTIVE_EXERCISE',
    exerciseJSON: exerciseJSON
  };
}

function updateActiveExerciseName(exercise) {
  return {
    type: 'UPDATE_ACTIVE_EXERCISE_NAME',
    exerciseName: exercise
  };
}

function fetchExercise(exercise) {
  return dispatch => {
    dispatch(updateActiveExerciseName(exercise));
    return fetch('http://localhost:8000/exercise/' + exercise)
      .then(response => response.json())
      .then(json => dispatch(updateActiveExercise(json)))
      .catch( err => console.log(err) );
  };
}

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: (exercise) => dispatch(fetchExercise(exercise)),
    onExercisesClick: () => dispatch(fetchExercises())
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
