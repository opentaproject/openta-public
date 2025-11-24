function updateRegradeResults(exercise, question, json) {
  //console.log("updateRegradeResults", exercise, question )
  return {
    type: 'UPDATE_REGRADE_RESULTS',
    results: json,
    exercise: exercise,
    question_key: question
  };
}

function setExerciseRegradeResults(exercise, question, data) {
  //{{{
  //console.log("setExerciseRegradeResults", exercise, question )
  return {
    type: 'SET_EXERCISE_REGRADE_RESULTS',
    exercise: exercise,
    question: question,
    data: data
  };
}

export { updateRegradeResults, setExerciseRegradeResults };
