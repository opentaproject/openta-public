export default (state = { exercises: ['test'], activeExerciseJSON: {}, activeExercise: "" }, action) => {
  switch (action.type) {
    case 'UPDATE_ACTIVE_EXERCISE_NAME':
      return Object.assign({}, state, {activeExercise: action.exerciseName});
    case 'UPDATE_ACTIVE_EXERCISE':
      return Object.assign({}, state, {activeExerciseJSON: action.exerciseJSON});
    case 'UPDATE_EXERCISES':
      return Object.assign({}, state, {exercises: action.exercises});
    default:
      return state
  }
}
