function setExerciseHistory(exerciseKey, list) {
  return {
    type: 'SET_EXERCISE_HISTORY',
    exercise: exerciseKey,
    data: list
  };
}

function updateSelectedExercises(exerciseKey) {
  return {
    type: 'UPDATE_SELECTED_EXERCISES',
    exerciseKey: exerciseKey
  };
}

function resetSelectedExercises() {
  return {
    type: 'RESET_SELECTED_EXERCISES'
  };
}

function updateSelectedExercisesMeta(data) {
  return {
    type: 'UPDATE_SELECTED_EXERCISES_META',
    data: data
  };
}

export { setExerciseHistory, updateSelectedExercises, updateSelectedExercisesMeta, resetSelectedExercises };
