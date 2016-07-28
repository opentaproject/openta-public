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
    alerts.push( ( <Alert message={response.error} type="error"/> )
               );
  }
  if(response.correct !== undefined) {
    if(response.correct) {
      var message = '$' + _.get(response, 'latex', '') + '$' + " is correct!";
      alerts.push( (<Alert message={message} type="success"/>) );
    } else {
      var message = '$' + _.get(response, 'latex', '') + '$' + " is incorrect.";
      alerts.push( (<Alert message={message} type="warning"/> ) );
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

export { updateExercises, updateActiveExercise, updateExerciseXML, updateExerciseJSON, updateQuestionResponse }
