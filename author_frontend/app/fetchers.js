import { 
  updateQuestionResponse, 
  updateLoginStatus,
  updateExercises,
  updateExerciseXML,
  updateExerciseJSON,
  updateActiveExercise,
  setSavePendingState,
  setResetPendingState,
  setSaveError,
  setExerciseModifiedState
} from './actions.js';
import {logImmutable} from 'immutablehelpers.js'
import {getcookie} from 'cookies.js'
import immutable from 'immutable'

var CSRF_TOKEN = getcookie('csrftoken')[0]; 

function jsonfetch(url, options = {}) {
  var defaults = {
      headers: { 
        'X-CSRFToken': CSRF_TOKEN,
        'Accept': 'application/json',
      },
      credentials: 'same-origin'
  };
  var _opts = immutable.fromJS(defaults).mergeDeep(immutable.fromJS(options));
  return fetch(url, _opts.toJS());
}

function fetchLoginStatus() {
  return dispatch => {
    return jsonfetch('/loggedin')
    .then(response => response.json() )
    .then(json => ({
      username: json.username,
      admin: json.admin
    }))
    .then(data => dispatch(updateLoginStatus(data)));
  };
}

function fetchExercises() {
  return dispatch => {
    return jsonfetch('http://localhost:8000/exercises/')
      //.then(response => {console.dir(response); return response;})
      .then(response => response.json())
      .then(json => json.map( item => item.exercise_name ))
      .then(json => dispatch(updateExercises(json)))
      .catch( err => console.log(err) );
  };
}


function fetchExerciseXML(exercise) {
  return dispatch => {
    return jsonfetch('http://localhost:8000/exercise/' + exercise + '/xml')
      .then(res => res.json())
      .then( json => json.xml )
      .then( xml => dispatch(updateExerciseXML(exercise, xml)));
  }
}

function fetchExercise(exercise, empty) {
  return dispatch => {
    dispatch(updateActiveExercise(exercise));
    if(empty) {
    dispatch(setResetPendingState(exercise, true));
    return jsonfetch('http://localhost:8000/exercise/' + exercise)
      .then(response => response.json())
      .then(json => {
        dispatch(fetchExerciseXML(exercise));
        dispatch(updateExerciseJSON(exercise, json));
        dispatch(setResetPendingState(exercise, false));
        dispatch(setExerciseModifiedState(exercise, false));
        dispatch(setSaveError(exercise, undefined));
      })
      .catch( err => console.log(err) );
  } else {
    return;
  }
  };
}

function saveExercise(exercise) {
  return (dispatch, getState) => {
    var state = getState();
    var xml = state.getIn(['exerciseState', exercise, 'xml']);
    var payload = {
      exercise: exercise,
      xml: xml
    }
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: data
    }
    dispatch(setSavePendingState(exercise, true));
    return jsonfetch('http://localhost:8000/exercise/' + exercise + '/save', fetchconfig)
    .catch( err => console.dir("Fetch error" + err) )
    .then( res => {
      if(res.status >= 300) {
        throw res.status;
      } 
      else {
        return res;
      }
    })
    .then(res => res.json())
    .then( json => {
      if(_.get(json, 'success', false)) {
        dispatch(setSavePendingState(exercise, false));
        dispatch(setExerciseModifiedState(exercise, false));
        dispatch(setSaveError(exercise, false));
      } 
      else {
        throw "Parse error";
      }
    })
    .catch( err => {
        dispatch(setSavePendingState(exercise, false));
        dispatch(setSaveError(exercise, true));
        console.log('Error while saving:' + err);
    });
  }
}

function checkQuestion(exercise, question, expression) {
  return dispatch => {
    var payload = {
      expression: expression
    }
    //var data = new FormData();
    //data.append('json', new Blob([JSON.stringify(payload)], {type: 'application/json'}));
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: data
    }
      
    jsonfetch('http://localhost:8000/exercise/' + exercise + '/question/' + question + '/check', fetchconfig)
    .catch( err => console.log("checkQuestion error!") )
    .then(res => res.json())
    .then(json => { dispatch(updateQuestionResponse(exercise, question, json)); return json});
    //.then(json => console.dir(json))
  }
}

export {
  fetchLoginStatus,
  fetchExercises, 
  fetchExerciseXML,
  fetchExercise,
  saveExercise,
  checkQuestion
};
