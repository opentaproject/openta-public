import _ from 'lodash'
import React from 'react';
import ReactDOM from 'react-dom';
import Alert from './components/Alert.jsx';

function updateExercises(exercises) {//{{{
  return {
    type: 'UPDATE_EXERCISES',
    exercises: exercises
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

function updateQuestionResponse(exercise, question, response) {//{{{
  var alerts = []
  if(response.error) {
    //alerts.push( ( <Alert message={response.error} type="error"/> )
    alerts.push( { type:"error", message: response.error } );
  }
  if(response.correct !== undefined) {
    if(response.correct) {
      var message = '$' + _.get(response, 'latex', '') + '$' + " is correct!";
      //alerts.push( (<Alert message={message} type="success"/>) );
      alerts.push( { type:"success", message: message } );
    } else {
      var message = '$' + _.get(response, 'latex', '') + '$' + " is incorrect.";
      //alerts.push( (<Alert message={message} type="warning"/> ) );
      alerts.push( { type:"warning", message: message } );
    }
  }
  var data = { 
    exerciseState: { 
      [exercise]: {
        question: {
         [question]: {
           alerts: alerts
         }
        }
      }
    }
  }; 
  return {
    type: 'UPDATE_QUESTION_RESPONSE',
    exercise: exercise,
    question: question,
    data: data
  }
}//}}}

function setSavePendingState(exercise, pending) {
  return {
    type: 'SET_SAVE_PENDING',
    exercise: exercise,
    pending: pending
  }
}

function setResetPendingState(exercise, pending) {
  return {
    type: 'SET_SAVE_PENDING',
    exercise: exercise,
    pending: pending
  }
}

function setExerciseModifiedState(exercise, modified) {
  return {
    type: 'SET_EXERCISE_MODIFIED',
    exercise: exercise,
    modified: modified
  }
}

export { updateExercises, updateActiveExercise, updateExerciseXML, updateExerciseJSON, updateQuestionResponse, setSavePendingState, setExerciseModifiedState }
