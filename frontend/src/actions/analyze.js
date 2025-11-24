// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

function updateAnalyzeResults(exercise, question, json) {
  //console.log("updateAnalyzeResults", exercise, question )
  return {
    type: 'UPDATE_ANALYZE_RESULTS',
    results: json,
    exercise: exercise,
    question_key: question
  };
}

function setExerciseAnalyzeResults(exercise, question, data) {
  //{{{
  //console.log("setExerciseAnalyzeResults", exercise, question )
  return {
    type: 'SET_EXERCISE_ANALYZE_RESULTS',
    exercise: exercise,
    question: question,
    data: data
  };
}

export { updateAnalyzeResults, setExerciseAnalyzeResults };
