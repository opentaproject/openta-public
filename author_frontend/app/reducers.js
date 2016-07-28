import immutable from 'immutable';

var defaultState = immutable.fromJS({ 
  exercises: ['test'], 
  activeExerciseJSON: {}, 
  activeExerciseXML: "",
  activeExercise: "",
  exerciseState: {"3_05_7.no_problem": {alerts: [1]}}
});

function logImmutable(x) {
  console.dir(JSON.stringify(x));
  return x;
}

export default (state = defaultState, action) => {
  switch (action.type) {
    case 'UPDATE_ACTIVE_EXERCISE_NAME':
      return state.mergeDeep({activeExercise: action.exerciseName});//Object.assign({}, state, {activeExercise: action.exerciseName});
    case 'UPDATE_ACTIVE_EXERCISE':
      return state.mergeDeep({activeExerciseJSON: action.exerciseJSON});//Object.assign({}, state, {activeExerciseJSON: action.exerciseJSON});
    case 'UPDATE_EXERCISES':
      return state.mergeDeep({exercises: action.exercises});//Object.assign({}, state, {exercises: action.exercises});
    case 'UPDATE_QUESTION_RESPONSE':
      return state.mergeDeep(action.data);//Object.assign({}, state, action.data);
    case 'UPDATE_ACTIVE_EXERCISE_XML':
      return state.mergeDeep(action.data);//Object.assign({}, state, action.data); 
    default:
      return state
  }
}
