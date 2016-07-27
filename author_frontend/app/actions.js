function updateExercises(exercises) {//{{{
  return {
    type: 'UPDATE_EXERCISES',
    exercises: exercises
  };
}//}}}

function updateActiveExercise(exerciseJSON) {//{{{
  return {
    type: 'UPDATE_ACTIVE_EXERCISE',
    exerciseJSON: exerciseJSON
  };
}//}}}

function updateActiveExerciseName(exercise) {//{{{
  return {
    type: 'UPDATE_ACTIVE_EXERCISE_NAME',
    exerciseName: exercise
  };
}//}}}

function updateActiveExerciseXML(exercise, xml) {//{{{
  var data = {
    exerciseState: {
      [exercise]: {
        xml: xml
      }
    }
  };
  return {
    type: 'UPDATE_ACTIVE_EXERCISE_XML',
    exercise: exercise,
    data: data
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

export { updateExercises, updateActiveExercise, updateActiveExerciseName, updateActiveExerciseXML, updateQuestionResponse }
