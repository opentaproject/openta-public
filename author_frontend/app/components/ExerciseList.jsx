import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

import immutable from 'immutable';

function listClass(item, active) {
  if(item === active)return "uk-active";
  else return "";
}

const BaseExercises = ({ exerciselist, activeExercise, exerciseState, onExerciseClick, onExercisesClick }) => (
  <div className="uk-width-medium-1-6" id="exercises-menu">
    <ul className="uk-nav uk-nav-side uk-list-space exercise-menu">
    <li className="uk-nav-header">Exercises</li>
    {exerciselist.map( exercise => ( 
                      <li className={exercise === activeExercise ? "uk-active" : ""}>
                        <a onClick={() => onExerciseClick(exercise, exerciseState.getIn([exercise,'json'], immutable.Map({})).isEmpty())}>
                          <ul>
                          <li><img className="uk-margin-right" style={{maxHeight: '40px'}} height="40px" src={'http://localhost:8000/exercise/' + exercise + '/asset/thumbnail.png'}/>
                          <li className="uk-text-break">{exercise.split('.')[0]}</li>
                          </li>
                          </ul>
                        </a>
                      </li>
                                   )
                     )}
    </ul>
  <button className="uk-margin-top" onClick={onExercisesClick}>Fetch</button>
  </div>
);

BaseExercises.propTypes = {
  exerciselist: PropTypes.array.isRequired,
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  onExerciseClick: PropTypes.func.isRequired,
  onExercisesClick: PropTypes.func.isRequired
};

const mapStateToProps = state => {
  var exerciseState = state.getIn(['exerciseState'], immutable.Map({}));
  return (
  {
    exerciselist: state.get('exercises', []),
    activeExercise: state.get('activeExercise') ,
    exerciseState: exerciseState
  }
  )
};

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: (exercise, empty) => dispatch(fetchExercise(exercise, empty)),
    onExercisesClick: () => dispatch(fetchExercises())
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
