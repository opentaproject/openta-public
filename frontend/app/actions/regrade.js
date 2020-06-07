
function updateRegradeResults(exercise,json) {
  return {
    type: 'UPDATE_REGRADE_RESULTS',
    results: json,
    exercise: exercise
  }
}

function setExerciseRegradeResults(exercise, data) {//{{{
  return {
    type: 'SET_EXERCISE_REGRADE_RESULTS',
    exercise: exercise,
    data: data
  }
}

export {updateRegradeResults, setExerciseRegradeResults, }
