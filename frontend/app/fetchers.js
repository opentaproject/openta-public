import { 
  updateQuestionResponse, 
  updateLoginStatus,
  updateExercises,
  setExerciseTree,
  updateExerciseXML,
  updateExerciseActiveXML,
  updateExerciseJSON,
  updateExerciseState,
  updateExercisesState,
  updateExercisesReloadMessages,
  updateActiveExercise,
  updateActiveAdminTool,
  updatePendingState,
  updatePendingStateIn,
  updateExerciseStatistics,
  updateAggregateStatistics,
  updateStudentResults,
  updateStudentDetailResults,
  updateMenuPath,
  updateMenuPathArray,
  updateMenuLeafDefaults,
  setSavePendingState,
  setResetPendingState,
  setSaveError,
  setExerciseModifiedState,
  setImageAnswers,
  setImageAnswersData,
  setExerciseRecentResults,
} from './actions.js';
import {logImmutable} from 'immutablehelpers.js'
import _ from 'lodash'
import immutable from 'immutable'
import {jsonfetch, CSRF_TOKEN} from './fetch_backend.js'
import {SUBPATH} from 'settings.js'

import {fetchAssets} from './fetchers/assets.js';

function fetchLoginStatus() {//{{{
  return dispatch => {
    return jsonfetch('/loggedin')
    .then(response => response.json() )
    .then(json => {
      if(!json.username) {
        window.location.href="/login";
      }
      return json;
    })
          .then(json => ({
              username: json.username,
              user_pk: json.user_pk,
              groups: json.groups,
              course: json.course
          }))
    .then(data => {
      dispatch(updateLoginStatus(data))
      if(data.groups.indexOf('Author') > -1)
        dispatch(updateMenuLeafDefaults(['activeExercise'], 'student'));
        //dispatch(updateMenuLeafDefaults(['activeExercise'], 'xmleditor'));
        //dispatch(updateActiveAdminTool('xml-editor'));
      if(data.groups.indexOf('Admin') > -1) 
        dispatch(updateMenuLeafDefaults(['activeExercise'], 'student'));
        //dispatch(updateMenuLeafDefaults(['activeExercise'], 'options'));
        //dispatch(updateActiveAdminTool('options'));
      if(data.groups.indexOf('View') > -1) {
        dispatch(updateMenuLeafDefaults(['activeExercise'], 'student'));
        //dispatch(updateMenuLeafDefaults(['activeExercise'], 'statistics'));
        //dispatch(updateActiveAdminTool('statistics'));
        dispatch(fetchAllExerciseStatistics());
      }
      }
         );
  };
}//}}}

function fetchExercises() {//{{{
  return dispatch => {
    return jsonfetch('/exercises/')
      .then(response => response.json())
      .then(json => {
         dispatch(updatePendingStateIn( ['course', 'loadingExercises'], false));
         return json;
      })
      .then(json => dispatch(updateExercisesState(json)))
      .catch( err => console.log(err) );
  };
}//}}}

function fetchExerciseTree() {//{{{
  return dispatch => {
    return jsonfetch('/exercises/tree/')
      .then(response => response.json())
      .then(json => dispatch(setExerciseTree(json)))
      .catch( err => console.log(err) );
  };
}//}}}

function fetchSameFolder(exercise, folder) {//{{{
  return dispatch => {
    return jsonfetch('/exercise/' + exercise + '/samefolder')
      .then(response => response.json())
      .then(json => {
        dispatch(updatePendingStateIn( ['exerciseList'], false));
        return json;
      })
      .then(json => dispatch(updateExercises(json, folder)))
      .catch( err => console.log(err) );
  };
}//}}}

function fetchExerciseJSON(exercise) {
  return dispatch => {
    return jsonfetch('/exercise/' + exercise + '/json')
      .then( res => { 
        return res;
      })
      .then( res => res.json() )
      .then(json => {
        dispatch(updateExerciseJSON(exercise, json));
        dispatch(setSaveError(exercise, undefined));
      })
      .catch( err => console.log(err) );
  }
}

function fetchExerciseXML(exercise) {//{{{
  return dispatch => {
    dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingXML'], true));
    return jsonfetch('/exercise/' + exercise + '/xml')
      .then( res => { 
        dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingXML'], false));
        return res;
      })
      .then( res => res.json() )
      .then( json => json.xml )
      .then( xml => {
        dispatch(updateExerciseActiveXML(exercise, xml));
        return dispatch(updateExerciseXML(exercise, xml))
      });
  }
}//}}}

function fetchExerciseRemoteState(exercise) {//{{{
  return dispatch => {
    return jsonfetch('/exercise/' + exercise)
      .then(response => response.json() )
      .then(json => dispatch(updateExerciseState(exercise, json)));
  }
}//}}}

function fetchExercise(exercise, empty) {//{{{
  return (dispatch, getState) => {
    dispatch(updateActiveExercise(exercise));
    const state = getState();
    const groups = state.getIn(['login','groups'], immutable.List([]));
    const json = state.getIn(['exerciseState', exercise, 'json']);
    //Only fetch XML if user is an Author and there is no XML already loaded
    if(groups.includes('Author') && state.getIn(['exerciseState', exercise, 'xml']) === undefined) {
      dispatch(fetchExerciseXML(exercise));
      dispatch(fetchAssets(exercise));
    }
    //Do not fetch new JSON if user is Author and JSON has already been loaded (This ensures that unsaved changes will be rendered when returning to an exercise
    if( !( json !== undefined && groups.includes('Author'))) {
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
        dispatch(setSaveError(exercise, undefined));
      })
      .catch( err => console.log(err) );
    } else {
      return;
    }
  };
}//}}}

function resetExercise(exercise) {
  return (dispatch) => {
    dispatch(updateExerciseXML(exercise, "")); // Trigger reload of editor XML
    return dispatch(fetchExerciseXML(exercise))
      .then( () => dispatch(fetchExerciseJSON(exercise)));
  }
}

function saveExercise(exercise) {//{{{
  return (dispatch, getState) => {
    var state = getState();
    var xml = state.getIn(['exerciseState', exercise, 'activeXML']);
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
        dispatch(updateExerciseXML(exercise, xml));
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
}//}}}

function checkQuestion(exerciseKey, questionKey, answerData) {//{{{
  return dispatch => {
    if(answerData === "")return;
    var payload = {
      answerData: answerData
    };
    //var data = new FormData();
    //data.append('json', new Blob([JSON.stringify(payload)], {type: 'application/json'}));
    var postData = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: postData
    };
    dispatch(updatePendingStateIn( ['exercises', exerciseKey, 'questions', questionKey, 'waiting'], true));
    jsonfetch('/exercise/' + exerciseKey + '/question/' + questionKey + '/check', fetchconfig)
    .then( res => {
      dispatch(updatePendingStateIn( ['exercises', exerciseKey, 'questions', questionKey, 'waiting'], false));
      return res;
    })
    .then(res => {
      if(res.status >= 400) {
        return {
            error: 'Ett fel uppstod. (Detta kan bero på att du inte är inloggad, om problem kvarstår var vänlig hör av dig.)'
        };
      }
      else {
          return res.json();
      }
    })
    .then(json => { dispatch(updateQuestionResponse(exerciseKey, questionKey, json)); return json})
    .then( json => {
      dispatch(updateExerciseState(exerciseKey, { question: { [questionKey]: { answer: answerData } } }));
      if(json.hasOwnProperty('error')) {
        throw "Error occured in question check";
      }
      return json;
    })
    .then( json => dispatch(fetchExerciseRemoteState(exerciseKey)))
    .catch( err => console.log(err) )
  }
}//}}}

function uploadProgress(dispatch, evt, exerciseKey) {//{{{
  if(evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageupload'], evt.loaded / evt.total));
  }
  else if(evt.position && evt.totalSize && evt.totalSize > 0) {
    return dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageupload'], evt.position / evt.totalSize));
  }
}//}}}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function uploadImage(exerciseKey, file) {//{{{
  return dispatch => {
      //|| !file.type.match(/image.*/)
      if (!file ) return;
      var fd = new FormData();
      fd.append('file', file);
      var xhr = new XMLHttpRequest();
      xhr.open("POST", SUBPATH + "/exercise/" + exerciseKey + "/imageupload");
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
      xhr.setRequestHeader('Accept', 'application/json');
      if(xhr.upload)
        xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, exerciseKey);
      xhr.onload = () => {
        dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageuploadpending'], false));
        dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageupload'], 1.0));
        dispatch(fetchExerciseRemoteState(exerciseKey));
      }
      xhr.send(fd);
      dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageuploadpending'], true));
    }
} //}}}

function deleteImageAnswer(imageAnswerId) {//{{{
  return dispatch => {
    var fetchconfig = {
      method: "POST"
    }
    return jsonfetch('/imageanswer/' + imageAnswerId + '/delete', fetchconfig)
  }
}//}}}

function fetchImageAnswers(exerciseKey) {//{{{
  return dispatch => {
    return jsonfetch('/exercise/' + exerciseKey + '/imageanswers')
      .then( res => res.json() )
      .then( json => { 
        dispatch(setImageAnswers(exerciseKey, json.ids));
        dispatch(setImageAnswersData(exerciseKey, json.data));
      })
      .catch( err => console.dir(err) )
  }
}//}}}

function fetchAllExerciseStatistics() {//{{{
  return dispatch => {
    dispatch(updatePendingStateIn( ['exercises_statistics'], true));
    return jsonfetch('/statistics/statsperexercise')
      .then(response => response.json())
      .then(json =>  { 
        dispatch(updateExerciseStatistics(json.exercises))
        dispatch(updateAggregateStatistics(json.aggregates))
      })
      .then( () => dispatch(updatePendingStateIn( ['exercises_statistics'], false)))
      .catch( err => console.log(err) );
  };
}//}}}

function fetchStudentResults() {
  return dispatch => {
    dispatch(updatePendingStateIn( ['studentResults'], true));
    return jsonfetch('/statistics/results')
      .then(response => response.json())
      .then(json => dispatch(updateStudentResults(json)))
      .then( () => dispatch(updatePendingStateIn( ['studentResults'], false)))
      .catch( err => console.log(err) );
  }
}

function fetchStudentDetailResults(userPk) {
  return dispatch => {
    dispatch(updatePendingStateIn( ['detailedResults', userPk], true));
    return jsonfetch('/results/user/' + userPk + '/')
      .then(response => response.json())
      .then(json => dispatch(updateStudentDetailResults(userPk, json)))
      .then( () => dispatch(updatePendingStateIn( ['detailedResults', userPk], false)))
      .catch( err => console.log(err) );
  }
}

function fetchExerciseStatistics() {
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(updatePendingStateIn( ['exercise', exercise, 'statistics'], true));
    return jsonfetch('/statistics/exercise/'+exercise+'/activity')
      .then(response => response.json())
      .then(json => ({
        activity: json
      }))
      .then(json => {return dispatch(updateExerciseState(exercise, json))})
      .then( () => dispatch(updatePendingStateIn( ['exercise', exercise, 'statistics'], false)))
      .catch( err => console.log(err) );
  }
}

function reloadExercises(iAmSure = false) {
    return dispatch => {
        var payload = {
            i_am_sure: iAmSure
        };
        var data = JSON.stringify(payload);
        var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: data
        };
        dispatch(updatePendingStateIn( ['exercisesReload'], true));
        return jsonfetch('/exercises/reload/json', fetchconfig)
            .then(response => response.json())
            .then(json => dispatch(updateExercisesReloadMessages(json)))
            .then( () => dispatch(updatePendingStateIn( ['exercisesReload'], false)))
            .then( () => dispatch( fetchExercises() ))
            .then( () => dispatch( fetchExerciseTree() )) 
            .catch( err => console.log(err) );
    };
}


function fetchExerciseRecentResults() {
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(updatePendingStateIn( ['results', 'exercises', exercise, 'recent'], true));
    return jsonfetch('/exercise/' + exercise + '/recentresults')
      .then(response => response.json())
      .then( json => dispatch(setExerciseRecentResults(exercise, json)))
      .then( () => dispatch(updatePendingStateIn( ['results', 'exercises', exercise, 'recent'], false)))
      .catch( err => console.log(err) );
  }
}

export {
  fetchLoginStatus,
  fetchExercises, 
  fetchSameFolder,
  fetchExerciseTree, 
  fetchExerciseXML,
  fetchExercise,
  fetchExerciseRemoteState,
  updatePendingStateIn,
  saveExercise,
  resetExercise,
  uploadImage,
  deleteImageAnswer,
  fetchImageAnswers,
  checkQuestion,
  fetchAllExerciseStatistics,
  fetchExerciseStatistics,
  fetchStudentResults,
  fetchStudentDetailResults,
  reloadExercises,
  fetchExerciseRecentResults,
};
export * from './fetchers/audit.js'
export * from './fetchers/exercise.js'
export * from './fetchers/assets.js'
