import React, { PropTypes } from 'react';
import { connect } from 'react-redux';

const BaseExercises = ({ exerciselist, onExerciseClick, onExercisesClick }) => (
  <div className="uk-width-medium-1-3">
    <h2>Exercises:</h2>
    <button onClick={onExercisesClick}>Update</button>
    <ul className="uk-nav uk-nav-side">
    {exerciselist.map( exercise => <li><a>{exercise}</a></li> )}
    {/* //{exerciselist.map( exercise => { return <span>{exercise}</span> } )}
      //<button onClick={onMinusClick}>-</button>
      //{count}
      //<button onClick={onPlusClick}>+</button>} */}
    </ul>
  </div>
);

BaseExercises.propTypes = {
  exerciselist: PropTypes.array.isRequired,
  onExerciseClick: PropTypes.func.isRequired,
  onExercisesClick: PropTypes.func.isRequired
};

const mapStateToProps = state => ({exerciselist: state.exercises });

function updateExercises(exercises) {
  return {
    type: 'UPDATE_EXERCISES',
    exercises: exercises
  }
}

function fetchExercises() {
  return dispatch => {
    return fetch('http://localhost:8000/exercises')
      //.then(response => {console.dir(response); return response;})
      .then(response => response.json())
      .then(json => dispatch(updateExercises(json)))
      .catch( err => console.log(err) );
  }
}

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: () => dispatch({ type: 'EXERCISECLICK' }),
    onExercisesClick: () => dispatch(fetchExercises())
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
