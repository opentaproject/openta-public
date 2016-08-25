import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

import { updateActiveExercise } from '../actions.js';

import immutable from 'immutable';

function listClass(item, active) {
  if(item === active)return "uk-active";
  else return "";
}

const BaseExercises = ({ exerciselist, folder, activeExercise, exerciseState, onExerciseClick, onExercisesClick, onBack }) => (
  <div className="uk-width-medium-1-6" id="exercises-menu">
    <ul className="uk-nav uk-nav-side uk-list-space exercise-menu">
    <li className="uk-nav-header">
      <a onClick={(ev) => onBack()}><i className="uk-icon uk-icon-medium uk-icon-arrow-left"></i></a> <span className="uk-text-large">{folder}</span>
    </li>
    {exerciselist.map( exercise => ( 
                      <li className={exercise.get('exercise_key') === activeExercise ? "uk-active" : ""}>
                        <a onClick={() => onExerciseClick(exercise.get('exercise_key'), exerciseState.getIn([exercise,'json'], immutable.Map({})).isEmpty())}>
                          <ul>
                          <li><img className="uk-margin-right" style={{maxHeight: '40px'}} height="40px" src={'/exercise/' + exercise.get('exercise_key') + '/asset/thumbnail.png'}/>
                          <li className="uk-text-break">{exercise.get('name')}</li>
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
  folder: PropTypes.string,
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  onExerciseClick: PropTypes.func.isRequired,
  onExercisesClick: PropTypes.func.isRequired,
  onBack: PropTypes.func,
};

const mapStateToProps = state => {
  var exerciseState = state.getIn(['exerciseState'], immutable.Map({}));
  return (
  {
    exerciselist: state.get('exercises', immutable.List([])).sort(),
    folder: state.get('folder', ""),
    activeExercise: state.get('activeExercise') ,
    exerciseState: exerciseState
  }
  )
};

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: (exercise, empty) => dispatch(fetchExercise(exercise, empty)),
    onExercisesClick: () => dispatch(fetchExercises()),
    onBack: () => dispatch(updateActiveExercise(""))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
