import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise
} from '../fetchers.js';

import { updateActiveExercise } from '../actions.js';
import immutable from 'immutable';
import Spinner from './Spinner.jsx'

function listClass(item, active) {
  if(item === active)return "uk-active";
  else return "";
}

const BaseExercises = ({ exerciselist, folder, activeExercise, exerciseState, onExerciseClick, onBack, pendingState }) => (
  <div className="uk-text-center" id="exercises-menu">
    <ul className="uk-nav uk-nav-side uk-list-space exercise-menu">
    <li className="uk-nav-header" key="header">
      <a onClick={(ev) => onBack()}><i className="uk-icon uk-icon-medium uk-icon-arrow-left"></i></a> <span className="uk-text-large">{folder}</span>
    </li>
    {exerciselist.map( exercise => ( 
                      <li className={exercise.get('exercise_key') === activeExercise ? "uk-active" : ""} key={exercise.get('exercise_key')}>
                        <a onClick={() => onExerciseClick(exercise.get('exercise_key'), exerciseState.getIn([exercise.get('exercise_key'),'json'], immutable.Map({})).isEmpty())}>
                          <ul>
                            <li>
                              <div className="exercise-thumb-wrap">
                              <img className="uk-margin-right" style={{maxHeight: '40px'}} height="40px" src={'/exercise/' + exercise.get('exercise_key') + '/asset/thumbnail.png'}/>
                                {exerciseState.getIn([exercise.get('exercise_key'), 'correct'], false) && <span className="uk-badge uk-badge-notification uk-badge-success exercise-thumb-badge"><i className="uk-icon uk-icon-check"></i></span> }
                              </div>
                            </li>
                            <li className="uk-text-break">{exercise.get('name')}</li>
                          </ul>
                        </a>
                      </li>
                                   )
                     ).toArray()}
    </ul>
  </div>
);

BaseExercises.propTypes = {
  exerciselist: PropTypes.object.isRequired,
  folder: PropTypes.string,
  activeExercise: PropTypes.string,
  exerciseState: PropTypes.object,
  pendingState: PropTypes.object,
  onExerciseClick: PropTypes.func.isRequired,
  onBack: PropTypes.func,
};

const mapStateToProps = state => {
  var exerciseState = state.getIn(['exerciseState'], immutable.Map({}));
  return (
  {
    exerciselist: state.get('exercises', immutable.List([])).sort(),
    folder: state.get('folder', ""),
    activeExercise: state.get('activeExercise') ,
    exerciseState: exerciseState,
    pendingState: state.get('pendingState')
  }
  )
};

const mapDispatchToProps = dispatch => {
  return {
    onExerciseClick: (exercise, empty) => dispatch(fetchExercise(exercise, empty)),
    onBack: () => dispatch(updateActiveExercise(""))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExercises)
