import immutable from 'immutable';
import {logImmutable} from 'immutablehelpers.js';

var defaultState = immutable.fromJS({ 
  exercises: ['test'], 
  //activeExerciseJSON: {}, 
  //activeExerciseXML: "",
  activeExercise: "",
  exerciseState: {"3_05_7.no_problem": {alerts: [1]}}
});

export default (state = defaultState, action) => {
  switch (action.type) {
    case 'UPDATE_ACTIVE_EXERCISE':
      return state.set('activeExercise', action.activeExercise);
    case 'UPDATE_EXERCISE_JSON':
      return state.setIn(['exerciseState',action.exercise, 'json'], immutable.fromJS(action.json));
    case 'UPDATE_EXERCISES':
      return state.set('exercises', action.exercises);
    case 'UPDATE_QUESTION_RESPONSE':
      return state.mergeDeep(action.data);
    case 'UPDATE_EXERCISE_XML':
      return state.setIn(['exerciseState', action.exercise, 'xml'], action.xml);
    case 'SET_SAVE_PENDING':
      return state.setIn(['exerciseState', action.exercise, 'savepending'], action.pending);
    case 'SET_SAVE_ERROR':
      return state.setIn(['exerciseState', action.exercise, 'saveerror'], action.error);
    case 'SET_RESET_PENDING':
      return state.setIn(['exerciseState', action.exercise, 'resetpending'], action.pending);
    case 'SET_EXERCISE_MODIFIED':
      return state.setIn(['exerciseState', action.exercise, 'modified'], action.modified);

    default:
      return state
  }
}
