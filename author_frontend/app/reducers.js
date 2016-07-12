var defaultState = { 
  exercises: ['test'], 
  activeExerciseJSON: {}, 
  activeExerciseXML: "",
  activeExercise: "",
  exerciseState: {"3_05_7.no_problem": {alerts: [1]}}
};

export default (state = defaultState, action) => {
  switch (action.type) {
    case 'UPDATE_ACTIVE_EXERCISE_NAME':
      return Object.assign({}, state, {activeExercise: action.exerciseName});
    case 'UPDATE_ACTIVE_EXERCISE':
      return Object.assign({}, state, {activeExerciseJSON: action.exerciseJSON});
    case 'UPDATE_EXERCISES':
      return Object.assign({}, state, {exercises: action.exercises});
    case 'UPDATE_QUESTION_RESPONSE':
      return Object.assign({}, state, action.data);
    case 'UPDATE_ACTIVE_EXERCISE_XML':
      return Object.assign({}, state, action.data); 
    default:
      return state
  }
}
