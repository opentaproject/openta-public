import { 
  updateQuestionResponse, 
  updateLoginStatus,
  updateExercises,
  updateExerciseTree,
  updateExerciseXML,
  updateExerciseJSON,
  updateExerciseState,
  updateExercisesState,
  updateActiveExercise,
  updatePendingState,
  updatePendingStateIn,
  setSavePendingState,
  setResetPendingState,
  setSaveError,
  setExerciseModifiedState
} from './actions.js';
import {logImmutable} from 'immutablehelpers.js'
import {getcookie} from 'cookies.js'
import immutable from 'immutable'
import _ from 'lodash'

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
    return jsonfetch('/exercises/')
      //.then(response => {console.dir(response); return response;})
      .then(response => response.json())
      .then(json => json.map( exercise =>
                             ({
                               [exercise.exercise_key]: { ...exercise }
                             }) ))
      .then(json => json.reduce( (a,b) => Object.assign(a,b) ))
      //.then(json => json.map( item => item.exercise_name ))
      .then(json => dispatch(updateExercisesState(json)))
      .catch( err => console.log(err) );
  };
}

function fetchExerciseTree() {
  return dispatch => {
    return jsonfetch('/exercises/tree')
      //.then(response => {console.dir(response); return response;})
      .then(response => response.json())
      .then(json => dispatch(updateExerciseTree(json)))
      .catch( err => console.log(err) );
  };
}

function fetchSameFolder(exercise, folder) {
  return dispatch => {
    return jsonfetch('/exercise/' + exercise + '/samefolder')
      //.then(response => {console.dir(response); return response;})
      .then(response => response.json())
      //.then(json => json.map( item => item.exercise_name ))
      .then(json => dispatch(updateExercises(json, folder)))
      .catch( err => console.log(err) );
  };
}

function fetchExerciseXML(exercise) {
  return dispatch => {
    dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingXML'], true));
    return jsonfetch('/exercise/' + exercise + '/xml')
      .then( res => { 
        dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingXML'], false));
        return res;
      })
      .then( res => res.json() )
      .then( json => json.xml )
      .then( xml => dispatch(updateExerciseXML(exercise, xml)));
  }
}

function fetchExerciseRemoteState(exercise) {
  return dispatch => {
    return jsonfetch('/exercise/' + exercise)
      .then(response => response.json() )
      .then(json => dispatch(updateExerciseState(exercise, json)));
  }
}

function fetchExercise(exercise, empty) {
  return dispatch => {
    dispatch(updateActiveExercise(exercise));
    dispatch(fetchExerciseXML(exercise));
    if(empty) {
      dispatch(setResetPendingState(exercise, true));
      dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingJSON'], true));
      return jsonfetch('/exercise/' + exercise + '/json')
      .then( res => {
        dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingJSON'], false));
        return res;
      })
      .then(response => {
        if(response.status >= 300){
          response.text().then( t => console.log(t) );
          dispatch(setResetPendingState(exercise, false));
          dispatch(setExerciseModifiedState(exercise, false));
          dispatch(setSaveError(exercise, undefined));
          throw response.status;
        }
        return response;
      }
       )
      .then(response => response.json())
      .then(json => {
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
    return jsonfetch('/exercise/' + exercise + '/save', fetchconfig)
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
        dispatch(setSavePendingState(exercise, false));
        dispatch(setExerciseModifiedState(exercise, true));
        dispatch(setSaveError(exercise, true));
        //dispatch(
      }
    })
    .catch( err => {
        dispatch(setSavePendingState(exercise, false));
        dispatch(setSaveError(exercise, true));
        console.log('Error while saving:' + err);
    });
  }
}

function checkQuestion(exerciseKey, questionKey, answerData) {
  return dispatch => {
    var payload = {
      answerData: answerData
    }
    //var data = new FormData();
    //data.append('json', new Blob([JSON.stringify(payload)], {type: 'application/json'}));
    var postData = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: postData
    }
    dispatch(updatePendingStateIn( ['exercises', exerciseKey, 'questions', questionKey, 'waiting'], true));
    jsonfetch('/exercise/' + exerciseKey + '/question/' + questionKey + '/check', fetchconfig)
    .then( res => {
      dispatch(updatePendingStateIn( ['exercises', exerciseKey, 'questions', questionKey, 'waiting'], false));
      return res;
    })
    .catch( err => console.log("checkQuestion error!") )
    .then(res => res.json())
    .then(json => { dispatch(updateQuestionResponse(exerciseKey, questionKey, json)); return json})
    .then( json => dispatch(fetchExerciseRemoteState(exerciseKey)))
    //.then(json => console.dir(json))
  }
}

export {
  fetchLoginStatus,
  fetchExercises, 
  fetchSameFolder,
  fetchExerciseTree, 
  fetchExerciseXML,
  fetchExercise,
  saveExercise,
  checkQuestion
};
