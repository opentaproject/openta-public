import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

function listClass(item, active) {
  if(item === active)return "uk-active";
  else return "";
}

const BaseExercises = ({ exerciselist, activeExercise, onExerciseClick, onExercisesClick }) => (
  <div className="uk-width-medium-1-6" id="exercises-menu">
    <ul className="uk-nav uk-nav-side uk-list-space exercise-menu">
    <li className="uk-nav-header">Exercises</li>
    {exerciselist.map( exercise => ( 
                      <li className={exercise === activeExercise ? "uk-active" : ""}>
                        <a onClick={() => onExerciseClick(exercise)}>
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
  onExerciseClick: PropTypes.func.isRequired,
  onExercisesClick: PropTypes.func.isRequired
};

const mapStateToProps = state => (
  {
    exerciselist: state.exercises,
    activeExercise: state.activeExercise }
);

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: (exercise) => dispatch(fetchExercise(exercise)),
    onExercisesClick: () => dispatch(fetchExercises())
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
