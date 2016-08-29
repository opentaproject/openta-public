import immutable from 'immutable';
import {logImmutable} from 'immutablehelpers.js';

var defaultState = immutable.fromJS({ 
  exercises: [], 
  folder: "",
  //activeExerciseJSON: {}, 
  //activeExerciseXML: "",
  activeExercise: "",
  exerciseState: {"3_05_7.no_problem": {alerts: [1]}}
});

export default (state = defaultState, action) => {
  switch (action.type) {
    case 'UPDATE_LOGIN_STATUS':
      return state.set('login', immutable.fromJS(action.data));
    case 'UPDATE_ACTIVE_EXERCISE':
      return state.set('activeExercise', action.activeExercise);
    case 'UPDATE_EXERCISE_JSON':
      return state.setIn(['exerciseState',action.exercise, 'json'], immutable.fromJS(action.json));
    case 'UPDATE_EXERCISE_STATE':
      return state.mergeDeepIn(['exerciseState', action.exercise], action.state);
    case 'UPDATE_EXERCISES_STATE':
      return state.mergeDeepIn(['exerciseState'], action.state);
    case 'UPDATE_EXERCISES':
      return state.merge({
        'exercises': immutable.fromJS(action.exercises),
        'folder': action.folder
      });
    case 'UPDATE_EXERCISE_TREE':
      return state.set('exerciseTree', action.exercisetree);
    case 'UPDATE_QUESTION_RESPONSE':
      return state.setIn(['exerciseState', action.exercise, 'question', action.question, 'response'], immutable.fromJS(action.response));
      //return state.mergeDeep(action.data);
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
