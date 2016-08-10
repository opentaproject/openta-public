import immutable from 'immutable';

var defaultState = immutable.fromJS({ 
  exercises: ['test'], 
  //activeExerciseJSON: {}, 
  //activeExerciseXML: "",
  activeExercise: "",
  exerciseState: {"3_05_7.no_problem": {alerts: [1]}}
});

function logImmutable(x) {
  console.log(JSON.stringify(x, null, 4));
  return x;
}

export default (state = defaultState, action) => {
  switch (action.type) {
    case 'UPDATE_ACTIVE_EXERCISE':
      return state.set('activeExercise', action.activeExercise);
    case 'UPDATE_EXERCISE_JSON':
      return state.setIn(['exerciseState',action.exercise, 'json'], immutable.fromJS(action.json));
    case 'UPDATE_EXERCISES':
      return state.set('exercises', action.exercises);
    case 'UPDATE_QUESTION_RESPONSE':
      return logImmutable(state.mergeDeep(action.data));
    case 'UPDATE_EXERCISE_XML':
      return state.setIn(['exerciseState', action.exercise, 'xml'], action.xml);
    default:
      return state
  }
}
