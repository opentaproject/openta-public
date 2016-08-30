import _ from 'lodash'
import React from 'react';
import ReactDOM from 'react-dom';
import Alert from './components/Alert.jsx';

function updateLoginStatus(data) {//{{{
  return {
    type: 'UPDATE_LOGIN_STATUS',
    data: data
  }
}//}}}

function updateExercises(exercises, folder) {//{{{
  return {
    type: 'UPDATE_EXERCISES',
    exercises: exercises,
    folder: folder
  };
}//}}}

function updateExerciseTree(exercisetree) {//{{{
  return {
    type: 'UPDATE_EXERCISE_TREE',
    exercisetree: exercisetree
  };
}//}}}

function updateExerciseState(exercise, state) {//{{{
  return {
    type: 'UPDATE_EXERCISE_STATE',
    state: state,
    exercise: exercise
  };
}//}}}

function updateExercisesState(state) {//{{{
  return {
    type: 'UPDATE_EXERCISES_STATE',
    state: state
  };
}//}}}

function updateExerciseJSON(exercise, json) {//{{{
  return {
    type: 'UPDATE_EXERCISE_JSON',
    exercise: exercise,
    json: json
  };
}//}}}

function updateActiveExercise(exercise) {//{{{
  return {
    type: 'UPDATE_ACTIVE_EXERCISE',
    activeExercise: exercise
  };
}//}}}

function updateExerciseXML(exercise, xml) {//{{{
  return {
    type: 'UPDATE_EXERCISE_XML',
    exercise: exercise,
    xml: xml
  };
}//}}}

function updateQuestionResponse(exerciseKey, questionKey, response) {//{{{
  return {
    type: 'UPDATE_QUESTION_RESPONSE',
    exercise: exerciseKey,
    question: questionKey,
    response: response
  }
}//}}}

function setSavePendingState(exercise, pending) {//{{{
  return {
    type: 'SET_SAVE_PENDING',
    exercise: exercise,
    pending: pending
  }
}//}}}

function setSaveError(exercise, error) {//{{{
  return {
    type: 'SET_SAVE_ERROR',
    exercise: exercise,
    error: error
  }
}//}}}

function setResetPendingState(exercise, pending) {//{{{
  return {
    type: 'SET_RESET_PENDING',
    exercise: exercise,
    pending: pending
  }
}//}}}

function setExerciseModifiedState(exercise, modified) {//{{{
  return {
    type: 'SET_EXERCISE_MODIFIED',
    exercise: exercise,
    modified: modified
  }
}//}}}

export { updateLoginStatus, updateExercises, updateExerciseTree, updateActiveExercise, updateExerciseXML, updateExerciseJSON, updateQuestionResponse, setSavePendingState, setSaveError, setResetPendingState, setExerciseModifiedState, updateExercisesState, updateExerciseState }
