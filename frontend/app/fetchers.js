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

import {
  setExerciseRegradeResults,
  updateRegradeResults,
 } from './actions/regrade.js'   ;

  
import {logImmutable} from 'immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from './fetch_backend.js';
import {SUBPATH} from 'settings.js';

import {fetchAssets} from './fetchers/assets.js';
import {enqueueTask} from './fetchers/tasks.js';

function notify(messages, levels) {
    var levelsRender = {
        'error': 'danger',
        'warning': 'warning',
        'success': 'success',
        'info': 'primary'
    };
    for(let message of messages) {
        if(levels.indexOf(message[0]) !== -1) {
            if(message[0] in levelsRender)
                UIkit.notify(message[1], {timeout: 10000, status: levelsRender[message[0]]});
            else
                UIkit.notify(message[1], {timeout: 10000, status: 'primary'});
        }
    }
}

function handleMessages(json) {
  var messages = []
  if('messages' in json)
    messages = json.messages;
  if('error' in json)
    messages.push(['error', json.error]);
  notify(messages, ['error', 'warning', 'info', 'success']);
  var errors = messages.filter(message => message[0] == 'error');
  if(errors.length > 0)
    throw errors;
  return json;
}

function fetchLoginStatus(coursePk) {
    return dispatch => {
        return jsonfetch('/loggedin/')
            .then(response => response.json() )
            .then(json => {
                if(!json.username) {
                    window.location.href= SUBPATH + "/login/";
                }
                return json;
            })
            .then(json => ({
                username: json.username,
                user_pk: json.user_pk,
                groups: json.groups,
                course: json.course,
                course_pk: json.course_pk,
                lti_login: json.lti_login,
                compactview: json.compactview,
            }))
            .then(data => {
                dispatch(updateLoginStatus(data));
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
                    dispatch(fetchAllExerciseStatistics(coursePk));
                }
            }
                 )
                 .catch(error => console.dir(error));
    };
}


function fetchUserExercises(coursePk, user_pk) {//{{{
  return dispatch => {
    return jsonfetch('/course/' + coursePk + '/exercises/' + user_pk + '/')
      .then(response => response.json())
      .then(json => {
         dispatch(updatePendingStateIn( ['course', 'loadingExercises'], false));
         return json;
      })
      .then(json => dispatch(updateExercisesState(json)))
      .catch( err => console.log(err) );
  };
}//}}}

function fetchExercises(coursePk) {//{{{
  //console.log("fetchExercises")
  return dispatch => {
    return jsonfetch('/course/' + coursePk + '/exercises/')
      .then(response => response.json())
      .then(json => {
         dispatch(updatePendingStateIn( ['course', 'loadingExercises'], false));
         return json;
      })
      .then(json => dispatch(updateExercisesState(json)))
      .catch( err => console.log(err) );
  };
}//}}}

function fetchExerciseTree(coursePk) {//{{{
  // console.log("fetchExerciseTree", exercisefilter)
  return ( dispatch, getState ) => {
  var state = getState()
  var exercisefilter = state.get('exercisefilter' )
  var filter = {'exercisefilter' : exercisefilter }
  var filterdata = JSON.stringify( filter )
  var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: filterdata 
        };
    dispatch(updatePendingStateIn( ['course', 'loadingExerciseTree'], true));
    return jsonfetch('/course/' + coursePk + '/exercises/tree/' , fetchconfig )
      .then(response => response.json())
      .then(json => {
         dispatch(updatePendingStateIn( ['course', 'loadingExerciseTree'], false));
         return json;
      })
      .then(json => dispatch(setExerciseTree(json, coursePk, filterdata)))
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
  // console.log("fetcExerciseJSON")
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
  // console.log("fetchExerciseRemoteState")
  return dispatch => {
    return jsonfetch('/exercise/' + exercise)
      .then(response => response.json() )
      .then(json => dispatch(updateExerciseState(exercise, json)));
  }
}//}}}

function fetchExercise(exercise, empty) {//{{{
  // console.log("fetchExercise")
  return (dispatch, getState) => {
    dispatch(updateActiveExercise(exercise));
    const state = getState();
    const groups = state.getIn(['login','groups'], immutable.List([]));
    const json = state.getIn(['exerciseState', exercise, 'json']);
    //Only fetch XML if user is an Author and there is no XML already loaded
    var canViewXML = groups.includes('Author') || groups.includes('View');
    if( canViewXML && state.getIn(['exerciseState', exercise, 'xml']) === undefined) {
      dispatch(fetchExerciseXML(exercise));
      dispatch(fetchAssets(exercise));
    }
    //Do not fetch new JSON if user is Author and JSON has already been loaded (This ensures that unsaved changes will be rendered when returning to an exercise
    if( !( json !== undefined &&  canViewXML)) {
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

function saveExercise(exercise) {
    return (dispatch, getState) => {
        var state = getState();
        var xml = state.getIn(['exerciseState', exercise, 'activeXML']);
        var payload = {
            exercise: exercise,
            xml: xml
        };
        var data = JSON.stringify(payload);
        var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: data
        };
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
                notify(_.get(json, 'messages', []), ['error', 'warning']);
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
                }
            })
            .catch( err => {
                dispatch(setSavePendingState(exercise, false));
                dispatch(setSaveError(exercise, true));
                console.log('Error while saving:' + err);
            });
    };
}

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
        throw "Error occurred in question check";
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
      return new Promise((resolve, reject) => {
          if (!file ) reject("No file");
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
              resolve(JSON.parse(xhr.response));
          };
          xhr.onerror = () => resolve(JSON.parse(xhr.response));
          xhr.send(fd);
          dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageuploadpending'], true));
      });
  };
} //}}}

function deleteImageAnswer(imageAnswerId) {//{{{
  return dispatch => {
    var fetchconfig = {
      method: "POST"
    };
      return jsonfetch('/imageanswer/' + imageAnswerId + '/delete', fetchconfig)
          .then(res => res.json());
  };
}//}}}

function fetchImageAnswers(exerciseKey) {//{{{
  return dispatch => {
    return jsonfetch('/exercise/' + exerciseKey + '/imageanswers')
      .then( res => res.json() )
      .then( json => { 
        dispatch(setImageAnswers(exerciseKey, json.ids));
        dispatch(setImageAnswersData(exerciseKey, json.data));
      })
          .catch( err => console.dir(err) );
  };
}//}}}

function fetchAllExerciseStatistics(coursePk) {//{{{
  return dispatch => {
    dispatch(updatePendingStateIn( ['exercises_statistics'], true));
    return jsonfetch('/course/' + coursePk + '/statistics/statsperexercise')
      .then(response => response.json())
      .then(json =>  { 
          dispatch(updateExerciseStatistics(json.exercises));
          dispatch(updateAggregateStatistics(json.aggregates));
      })
      .then( () => dispatch(updatePendingStateIn( ['exercises_statistics'], false)))
      .catch( err => console.log(err) );
  };
}//}}}




function fetchStudentResults(coursePk) {
  return (dispatch, getState) => {
    var state = getState();
    var coursePk = state.get('activeCourse');
    dispatch(updatePendingStateIn(['studentResults'], true));

    var taskOptions = {
      progressAction: (progress) => dispatch => dispatch(updatePendingStateIn(['studentResults'], progress)),
      completeAction: (data) => dispatch => {
        dispatch(updateStudentResults(data));
        dispatch(updatePendingStateIn(['studentResults'], false));
      }
    };
    return dispatch(enqueueTask('/course/' + coursePk + '/statistics/resultsasync', taskOptions))
      .catch(err => dispatch(updatePendingStateIn(['studentResults'], false)));
  };
}

function fetchStudentDetailResults(userPk, coursePk) {
  return (dispatch, getState) => {
    var state = getState();
    var coursePk = state.get('activeCourse');
    var exerciseKey = state.get('activeExercise');
    dispatch(updatePendingStateIn( ['detailedResults', userPk], true));
    return jsonfetch('/course/' + coursePk + '/results/user/' + userPk + '/' + exerciseKey+ '/')
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

function reloadExercises(iAmSure = false, coursePkIn=null) {
  return (dispatch, getState) => {
    var coursePk = null;
    if (coursePkIn == null) {
      var state = getState();
      coursePk = state.get('activeCourse');
    }
    else {
      coursePk = coursePkIn;
    }
    var payload = {
      i_am_sure: iAmSure
    };
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: data
    };
    dispatch(updatePendingStateIn(['exercisesReload'], true));
    return jsonfetch('/course/' + coursePk + '/exercises/reload/json/', fetchconfig)
      .then(response => response.json())
      .then(json => {
        if ('detail' in json) {
          UIkit.notify(json.detail, { timeout: 10000, status: 'danger' });
          dispatch(updatePendingStateIn(['exercisesReload'], false));
          throw json.detail;
        }
        return json;
      })
      .then(json => dispatch(updateExercisesReloadMessages(json)))
      .then(() => dispatch(updatePendingStateIn(['exercisesReload'], false)))
      .then(() => dispatch(fetchExercises(coursePk)))
      .then(() => dispatch(fetchExerciseTree(coursePk)))
      .catch(err => console.log(err));
  };
}


function fetchExerciseRecentResults() {
  // console.log("fetchExerciseRecentResults entered ")
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
  notify,
  handleMessages,
  fetchLoginStatus,
  fetchExercises,
  fetchSameFolder,
  fetchExerciseTree,
  fetchExerciseXML,
  fetchExerciseJSON,
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
  fetchUserExercises,
  fetchExerciseRecentResults,
};
export * from './fetchers/audit.js'
export * from './fetchers/exercise.js'
export * from './fetchers/assets.js'
export * from './fetchers/tasks.js'
export * from './fetchers/course.js'
export * from './fetchers/server.js'
export * from './fetchers/canvas.js'
export * from './fetchers/regrade.js'
