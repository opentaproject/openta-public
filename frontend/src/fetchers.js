// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

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
  updateExercisesValidateMessages,
  updateActiveExercise,
  updatePendingStateIn,
  updateExerciseStatistics,
  updateAggregateStatistics,
  updateCourseAggregateStatistics,
  updateStudentResults,
  updateStudentDetailResults,
  updateMenuLeafDefaults,
  setSavePendingState,
  setResetPendingState,
  setSaveError,
  setExerciseModifiedState,
  setImageAnswers,
  setImageAnswersData,
  setExerciseRecentResults
} from './actions.js';

// import notify from './notify.jsx'
import _ from 'lodash';
import immutable from 'immutable';
import { jsonfetch, CSRF_TOKEN, sendFrontendLog } from './fetch_backend.js';
import { SUBPATH , username , answer_delay, user_permissions} from './settings.js';

import { fetchAssets } from './fetchers/assets.js';
import { enqueueTask } from './fetchers/tasks.js';
import {  fetchCurrentAuditsExercise } from './fetchers.js'

function notify(messages, levels) {
  var levelsRender = {
    error: 'danger',
    warning: 'warning',
    success: 'success',
    info: 'primary'
  };
  var did_notify = false
  var errormessage = messages.filter( i => 'error' == i[0] )
  if ( errormessage.length   > 0  ){
    var msg = ( errormessage[0][1] ).toString() ;
    UIkit.notify( msg , {timeout:40000 , status: 'warning' } )
  } else {

  for (let message of messages) {
    if (levels.indexOf(message[0]) ) {
      if (message[0] in levelsRender) {
        did_notify = true
        UIkit.notify(message[1], { timeout: 30000, status: levelsRender[message[0]] });
      } else {
        did_notify = true
        UIkit.notify(message[1], { timeout: 10000, status: 'primary' });
      }
    }
  };
  if ( ! did_notify ){
    if ( !  JSON.stringify(messages).indexOf('task_id') > 0 ) {
      console.log( "A1 " + JSON.stringify( messages) )
    }
  }
  }
}

function handleMessages(json) {
  var messages = [];
  if ('messages' in json) {
    messages = json.messages;
  } else {
    messages = [json];
  }
  if ('error' in json) {
    messages.push(['error', json.error]);
  }
  if ( messages.length > 0  ){
    if ( Object.hasOwn(  messages[0] , 'task_id' )  ) {
      messages[0][1] = "run task " + String( messages[0].task_id  )
    }
    notify(messages, ['error', 'warning', 'info', 'success']);
  }
  var errors = messages.filter((message) => message[0] == 'error');
  if (errors.length > 0) {
    throw errors;
  }
  return json;
}

function fetchSendMyAudits() {
  //console.log("fetchSendMyAudits")
  return ( dispatch , getState ) => {
    var state = getState();
    var exercise = state.get('activeExercise');
      return jsonfetch( '/exercise/' + exercise + '/send_my_audits/')
       .then((response) => response.json())
       .then( (json) => {
          return json ;
       } )
    .then(() => dispatch(fetchCurrentAuditsExercise()))
     }
  }


function fetchLoginStatus(coursePk) {
  return (dispatch) => {
    return jsonfetch('/loggedin/', { cache: 'no-cache' })
      .then(async (response) => {
        if (!response || !response.ok) {
          console.warn('Login status request failed', { status: response && response.status });
          return {};
        }
        try {
          return await response.json();
        } catch (e) {
          console.warn('Login status JSON parse failed');
          return {};
        }
      })
      .then((json) => {
        if (!json.username) {
          try {
            window.location.href = SUBPATH + '/login/';
          } catch (_) {}
        }
        return json;
      })
      .then((json) => ({
        username: json && json.username,
        user_pk: json && json.user_pk,
        groups: json && Array.isArray(json.groups) ? json.groups : [],
        course: json && json.course,
        course_pk: json && json.course_pk,
        lti_login: json && json.lti_login,
        compactview: json && json.compactview,
        subdomain: json && json.subdomain,
        backupstatus: json && json.backupstatus,
        sidecar_count: json && json.sidecar_count,
      }))
      .then((data) => {
        dispatch(updateLoginStatus(data));
        const groups = Array.isArray(data.groups) ? data.groups : [];
        if (groups.indexOf('Author') > -1) {
          dispatch(updateMenuLeafDefaults(['activeExercise'], 'student'));
          dispatch(fetchAllExerciseStatistics(coursePk));
        }
        //dispatch(updateMenuLeafDefaults(['activeExercise'], 'xmleditor'));
        //dispatch(updateActiveAdminTool('xml-editor'));
        else if (groups.indexOf('Admin') > -1) {
          dispatch(updateMenuLeafDefaults(['activeExercise'], 'student'));
          dispatch(fetchAllExerciseStatistics(coursePk));
        }
        //dispatch(updateMenuLeafDefaults(['activeExercise'], 'options'));
        //dispatch(updateActiveAdminTool('options'));
        else if (groups.indexOf('View') > -1) {
          dispatch(updateMenuLeafDefaults(['activeExercise'], 'student'));
          //dispatch(updateMenuLeafDefaults(['activeExercise'], 'statistics'));
          //dispatch(updateActiveAdminTool('statistics'));
          dispatch(fetchAllExerciseStatistics(coursePk));
        }
      })
      .catch((error) => {
        console.warn('Error in fetchLoginStatus', error);
        sendFrontendLog('error', 'fetchLoginStatus failed', { error: String(error) });
      });
  };
}

function fetchUserExercises(coursePk, user_pk) {
  //{{{
  return (dispatch) => {
    return jsonfetch('/course/' + coursePk + '/exercises/' + user_pk + '/')
      .then((response) => response.json())
      .then((json) => {
        dispatch(updatePendingStateIn(['course', 'loadingExercises'], false));
        return json;
      })
      .then((json) => dispatch(updateExercisesState(json)))
      .catch((err) => {
        console.log(err);
        sendFrontendLog('error', 'fetchUserExercises failed', { coursePk, user_pk, error: String(err) });
      });
  };
}

function fetchExercises(coursePk) {
  //{{{
  return (dispatch) => {
    return jsonfetch('/course/' + coursePk + '/exercises/')
      .then((response) => response.json())
      .then((json) => {
        dispatch(updatePendingStateIn(['course', 'loadingExercises'], false));
        return json;
      })
      .then((json) => dispatch(updateExercisesState(json)))
      .catch((err) => {
        console.log(err);
        sendFrontendLog('error', 'fetchExercises failed', { coursePk, error: String(err) });
      });
  };
} //}}}

function fetchExerciseTree(coursePk) {
  return (dispatch, getState) => {
    var state = getState();
    var exercisefilter = state.get('exercisefilter');
    var filter = { exercisefilter: exercisefilter };
    var filterdata = JSON.stringify(filter);
    var fstring =
      (exercisefilter['required_exercises'] ? '1' : '0') +
      (exercisefilter['bonus_exercises'] ? '1' : '0') +
      (exercisefilter['optional_exercises'] ? '1' : '0') +
      (exercisefilter['unpublished_exercises'] ? '1' : '0') +
      (exercisefilter['organize'] ? '1' : '0');
    var fetchconfig = {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: filterdata
    };
    // dispatch(updatePendingStateIn( ['course', 'loadingExerciseTree'], true));
    return (
      jsonfetch('/course/' + coursePk + '/exercises/tree/' + fstring + '/') // , fetchconfig )
        .then((response) => response.json())
        //.then(json => {
        //   dispatch(updatePendingStateIn( ['course', 'loadingExerciseTree'], false));
        //   return json;
        //})
        .then((json) => dispatch(setExerciseTree(json, coursePk, filterdata)))
    );
    //.catch( err => console.log(err) );
  };
}

function fetchSameFolder(exercise, subdomain) {
  //{{{
  //console.log("fetchSameFolder exercise=", exercise)
  //console.log("fetchSameFolder subdomain =", subdomain)
  return (dispatch) => {
    return jsonfetch('/exercise/' + exercise + '/samefolder/' + subdomain + '/')
      .then((response) => response.json())
      .then((json) => {
        dispatch(updatePendingStateIn(['exerciseList'], false));
        return json;
      })
      .then((json) => dispatch(updateExercises(json, subdomain)))
      .catch((err) => {
        console.log(err);
        sendFrontendLog('error', 'fetchSameFolder failed', { exercise, subdomain, error: String(err) });
      });
  };
} //}}}

function fetchExerciseJSON(exercise) {
  // console.log("fetcExerciseJSON")
  return (dispatch) => {
    return jsonfetch('/exercise/' + exercise + '/json')
      .then((res) => {
        return res;
      })
      .then((res) => res.json())
      .then((json) => {
        dispatch(updateExerciseJSON(exercise, json));
        dispatch(setSaveError(exercise, undefined));
      })
      .catch((err) => {
        console.log(err);
        sendFrontendLog('error', 'fetchExerciseJSON failed', { exercise, error: String(err) });
      });
  };
}

function fetchExerciseXML(exercise) {
  //{{{
  return (dispatch) => {
    dispatch(updatePendingStateIn(['exercises', exercise, 'loadingXML'], true));
    return jsonfetch('/exercise/' + exercise + '/xml')
      .then((res) => {
        dispatch(updatePendingStateIn(['exercises', exercise, 'loadingXML'], false));
        return res;
      })
      .then((res) => res.json())
      .then((json) => json.xml)
      .then((xml) => {
        dispatch(updateExerciseActiveXML(exercise, xml));
        return dispatch(updateExerciseXML(exercise, xml));
      })
      .catch((err) => {
        console.warn('Failed to fetch exercise XML', exercise, err);
        sendFrontendLog('error', 'fetchExerciseXML failed', { exercise, error: String(err) });
        dispatch(updatePendingStateIn(['exercises', exercise, 'loadingXML'], false));
      });
  };
} //}}}

function fetchExerciseRemoteState(exercise) {
  //{{{
  // console.log("fetchExerciseRemoteState")
  return (dispatch) => {
    return jsonfetch('/exercise/' + exercise)
      .then((response) => response.json())
      .then((json) => dispatch(updateExerciseState(exercise, json)))
      .catch((err) => {
        console.warn('Failed to fetch exercise state', exercise, err);
        sendFrontendLog('error', 'fetchExerciseRemoteState failed', { exercise, error: String(err) });
      });
  };
} //}}}

function fetchExercise(exercise, empty) {
  //{{{
  // console.log("fetchExercise")
  return (dispatch, getState) => {
    dispatch(updateActiveExercise(exercise));
    const state = getState();
    const groups = state.getIn(['login', 'groups'], immutable.List([]));
    const json = state.getIn(['exerciseState', exercise, 'json']);
    //Only fetch XML if user is an Author and there is no XML already loaded
    var canViewXML = groups.includes('Author') || groups.includes('View');
    if (canViewXML && state.getIn(['exerciseState', exercise, 'xml']) === undefined) {
      dispatch(fetchExerciseXML(exercise));
      dispatch(fetchAssets(exercise));
    }
    //Do not fetch new JSON if user is Author and JSON has already been loaded (This ensures that unsaved changes will be rendered when returning to an exercise

    if (!(json !== undefined && canViewXML)) {
      dispatch(updatePendingStateIn(['exercises', exercise, 'loadingJSON'], true));
      return jsonfetch('/exercise/' + exercise + '/json')
        .then((res) => {
          dispatch(updatePendingStateIn(['exercises', exercise, 'loadingJSON'], false));
          return res;
        })
        .then((response) => {
          if (response.status >= 300) {
            response.text().then((t) => console.log(t));
            dispatch(setResetPendingState(exercise, false));
            dispatch(setExerciseModifiedState(exercise, false));
            dispatch(setSaveError(exercise, undefined));
            throw response.status;
          }
          return response;
        })
        .then((response) => response.json())
        .then((json) => {
          dispatch(updateExerciseJSON(exercise, json));
          dispatch(setSaveError(exercise, undefined));
        })
        .catch((err) => {
          console.log(err);
          sendFrontendLog('error', 'fetchExercise failed', { exercise, error: String(err) });
          dispatch(updatePendingStateIn(['exercises', exercise, 'loadingJSON'], false));
        });
    } else {
      return;
    }
  };
} //}}}

function resetExercise(exercise) {
  return (dispatch) => {
    dispatch(updateExerciseXML(exercise, '')); // Trigger reload of editor XML
    return dispatch(fetchExerciseXML(exercise)).then(() => dispatch(fetchExerciseJSON(exercise)));
  };
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
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data
    };
    dispatch(setSavePendingState(exercise, true));
    return jsonfetch('/exercise/' + exercise + '/save', fetchconfig)
      .catch((err) => console.dir('Fetch error' + err))
      .then((res) => {
        if (res.status >= 300) {
          throw res.status;
        } else {
          return res;
        }
      })
      .then((res) => res.json())
      .then((json) => {
        notify(_.get(json, 'messages', []), ['error', 'warning']);
        if (_.get(json, 'success', false)) {
          dispatch(setSavePendingState(exercise, false));
          dispatch(setExerciseModifiedState(exercise, false));
          dispatch(setSaveError(exercise, false));
          dispatch(updateExerciseXML(exercise, xml));
        } else {
          dispatch(setSavePendingState(exercise, false));
          dispatch(setExerciseModifiedState(exercise, true));
          dispatch(setSaveError(exercise, true));
        }
      })
      .catch((err) => {
        dispatch(setSavePendingState(exercise, false));
        dispatch(setSaveError(exercise, true));
        console.log('Error while saving:' + err);
      });
  };
}

function checkQuestion(exerciseKey, questionKey, answerData) {
  return (dispatch) => {
    if (answerData === '') {
      return;
    }
    var payload = {
      answerData: answerData
    };
    //var data = new FormData();
    //data.append('json', new Blob([JSON.stringify(payload)], {type: 'application/json'}));
    var postData = JSON.stringify(payload);
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: postData
    };
    var delay = username == 'super' ? 0 :  answer_delay 
    //console.log("answerData = ", answerData )
    // console.log("ANSWER_DELAY ", answer_delay)
    var t = Date.now()
    dispatch(updatePendingStateIn(['exercises', exerciseKey, 'questions', questionKey, 'waiting'], true ));
    dispatch(updatePendingStateIn(['exercises', exerciseKey, 'questions', questionKey, 'waiting_for'], String( answerData ) ));
    const promise1 = jsonfetch('/exercise/' + exerciseKey + '/question/' + questionKey + '/check', fetchconfig)
    const promise2 = promise1.then((res) => {
        //console.log("B", Date.now() - t  )
        //console.log("id = ", id )

        if (res.status == 429) {
          return {
            error: 'Rate limit error. Try again in a minute or so'
          };
        } 
      else if (res.status >= 400) {
          return {
            error: 'Unknown error. Try again. If that fails, log out and back in again. If it still fails, give up and send a bug report.'
          };
        } 

      else {


          //console.log("C", Date.now() - t  )
          try {
            var corrected  = [ ...res.headers ].filter( n => ( n[0] == 'corrected' ) )[0][1]
          } catch( error ){
            var corrected = 'false'
          }
          if ( corrected == 'false' ){ // DON'T FORCE STUDENT TO WAIT TO FIND OUT SYNTAX ERROR
            dispatch(updateQuestionResponse(exerciseKey, questionKey, res.json));
            dispatch(updateExerciseState(exerciseKey, { question: { [questionKey]: { answer: answerData } } }));
            dispatch(updatePendingStateIn(['exercises', exerciseKey, 'questions', questionKey, 'waiting'], false))
            dispatch(fetchExerciseRemoteState(exerciseKey));
            }
          return res.json();
        }
      })
    var dt = Date.now()  - t // make sure minimum delay is answer_delay
    var id = setTimeout( ( () => {
      const promise3=promise2.then((json) => {
        //console.log("DELAY = ", delay )
        dispatch(updateQuestionResponse(exerciseKey, questionKey, json));
          })
        const promise4=promise3.then(() => {
            dispatch(updateExerciseState(exerciseKey, { question: { [questionKey]: { answer: answerData } } }));
          })
        const promise5 = promise4.then(() => {
            dispatch(updatePendingStateIn(['exercises', exerciseKey, 'questions', questionKey, 'waiting'], false));
          })
    
        const promise6=promise5.then(( (json) => {
            dispatch(fetchExerciseRemoteState(exerciseKey))} )
          )
          .catch((err) => console.log(err));
        }), Math.max( delay - dt  ,0 )
     )
  }
} 

function uploadProgress(dispatch, evt, exerciseKey) {
  //{{{
  if (evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageupload'], evt.loaded / evt.total));
  } else if (evt.position && evt.totalSize && evt.totalSize > 0) {
    return dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageupload'], evt.position / evt.totalSize));
  }
} //}}}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function reUploadImage(exerciseKey, file, src, action) {
  //{{{
  //console.log("ReUPloadImage KEY=", exerciseKey )
  //console.log("ReUPloadImage FILE =", file )
  //console.log("ReUPloadImage SRC =", src )
  //console.log("ReUPloadImage action =", action)
  return (dispatch) => {
   // console.log("NOW DISPATCH")
    return new Promise((resolve, reject) => {
      //console.log("NEW PROMISE")
      if (!file) {
        reject('No file');
      }
      //console.log("AA")
      var fd = new FormData();
      //console.log("BB")
      fd.append('file', file);
      var xhr = new XMLHttpRequest();
      var req = '/exercise/' + exerciseKey + '/imageupload' + '/' + action + src
      //console.log("REQ = ", req )
      xhr.open('POST', req)
      //console.log("BB")
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
      xhr.setRequestHeader('Accept', 'application/json');
      xhr.setRequestHeader('Cache-Control', 'no-store');
      //console.log("CC")
      if (xhr.upload) {
        xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, exerciseKey);
      }
      xhr.onload = () => {
        dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageuploadpending'], false));
        dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageupload'], 1.0));
        dispatch(fetchExerciseRemoteState(exerciseKey));
        resolve(JSON.parse(xhr.response));
      };
      //console.log("DD")
      xhr.onerror = () => resolve(JSON.parse(xhr.response));
      xhr.send(fd);
      dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageuploadpending'], true));
    });
  };
} //}}}

function uploadImage(exerciseKey, file) {
  //{{{
  return (dispatch) => {
    //|| !file.type.match(/image.*/)
    return new Promise((resolve, reject) => {
      if (!file) {
        reject('No file');
      }
      var fd = new FormData();
      fd.append('file', file);
      var xhr = new XMLHttpRequest();
      xhr.open('POST', SUBPATH + '/exercise/' + exerciseKey + '/imageupload');
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
      xhr.setRequestHeader('Accept', 'application/json');
      if (xhr.upload) {
        xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, exerciseKey);
      }
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

function deleteImageAnswer(imageAnswerId) {
  //{{{
  return (dispatch) => {
    var fetchconfig = {
      method: 'POST'
    };
    return jsonfetch('/imageanswer/' + imageAnswerId + '/delete', fetchconfig).then((res) => res.json());
  };
} //}}}

function fetchImageAnswers(exerciseKey) {
  //{{{
  return (dispatch) => {
    return jsonfetch('/exercise/' + exerciseKey + '/imageanswers')
      .then((res) => res.json())
      .then((json) => {
        dispatch(setImageAnswers(exerciseKey, json.ids));
        dispatch(setImageAnswersData(exerciseKey, json.data));
      })
      .catch((err) => console.dir(err));
  };
} 

function fetchAllExerciseStatistics(coursePk) {
  return (dispatch) => {
    dispatch(updateExerciseStatistics(null)); // SEND THIS TO FLAG ACTIONS TO GET FROM LOCAL STORAGE
    dispatch(updatePendingStateIn(['exercises_statistics'], true));
    return jsonfetch('/course/' + coursePk + '/statistics/statsperexercise')
      .then((response) => response.json())
      .then((json) => {
        dispatch(updateExerciseStatistics(json.exercises));
        dispatch(updateAggregateStatistics(json.aggregates));
      })
      .then(() => dispatch(updatePendingStateIn(['exercises_statistics'], false)))
      .catch((err) => console.log(err));
  };
} 

function fetchCourseStatistics() {
  return (dispatch, getState) => {
    //dispatch(updateExerciseStatistics(null ) ); // SEND THIS TO FLAG ACTIONS TO GET FROM LOCAL STORAGE
    dispatch(updatePendingStateIn(['course_statistics'], true));
    var state = getState();
    var x = state.getIn(['activityRange'], 'all');
    var coursePk = state.get('activeCourse');
    return jsonfetch('/course/' + coursePk + '/course_statistics/' + x + '/')
      .then((response) => response.json())
      .then((json) => {
        dispatch(updateCourseAggregateStatistics(json));
      })
      .then(() => dispatch(updatePendingStateIn(['course_statistics'], false)))
      .catch((err) => console.log(err));
  };
}

function fetchStudentResults(coursePk) {
  return (dispatch, getState) => {
    var state = getState();
    var coursePk = state.get('activeCourse');
    dispatch(updateStudentResults(null)); // SEND THIS TO FLAG ACTIONS TO GET FROM LOCAL STORAGE
    dispatch(updatePendingStateIn(['studentResults'], true));

    var taskOptions = {
      progressAction: (progress) => (dispatch) => dispatch(updatePendingStateIn(['studentResults'], progress)),
      completeAction: (data) => (dispatch) => {
        dispatch(updateStudentResults(data));
        dispatch(updatePendingStateIn(['studentResults'], false));
      }
    };
    return dispatch(enqueueTask('/course/' + coursePk + '/statistics/resultsasync', taskOptions)).catch((err) =>
      dispatch(updatePendingStateIn(['studentResults'], false))
    );
  };
}

function fetchStudentDetailResults(userPk, coursePk) {
  return (dispatch, getState) => {
    var state = getState();
    var coursePk = state.get('activeCourse');
    var exerciseKey = state.get('activeExercise');
    dispatch(updatePendingStateIn(['detailedResults', userPk], true));
    return jsonfetch('/course/' + coursePk + '/results/user/' + userPk + '/' + exerciseKey + '/')
      .then((response) => response.json())
      .then((json) => dispatch(updateStudentDetailResults(userPk, json)))
      .then(() => dispatch(updatePendingStateIn(['detailedResults', userPk], false)))
      .catch((err) => console.log(err));
  };
}

function fetchExerciseStatistics() {
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(updatePendingStateIn(['exercise', exercise, 'statistics'], true));
    return jsonfetch('/statistics/exercise/' + exercise + '/activity')
      .then((response) => response.json())
      .then((json) => ({
        activity: json
      }))
      .then((json) => {
        return dispatch(updateExerciseState(exercise, json));
      })
      .then(() => dispatch(updatePendingStateIn(['exercise', exercise, 'statistics'], false)))
      .catch((err) => console.log(err));
  };
}

function validateExercises(iAmSure = false, coursePkIn = null) {
  return (dispatch, getState) => {
    var coursePk = null;
    if (coursePkIn == null) {
      var state = getState();
      coursePk = state.get('activeCourse');
    } else {
      coursePk = coursePkIn;
    }
    var payload = {
      i_am_sure: iAmSure
    };
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data
    };
    dispatch(updatePendingStateIn(['exercisesValidate'], true));
    return jsonfetch('/course/' + coursePk + '/exercises/validate/json/', fetchconfig)
      .then((response) => response.json())
      .then((json) => {
        if ('detail' in json) {
          UIkit.notify(json.detail, { timeout: 10000, status: 'danger' });
          dispatch(updatePendingStateIn(['exercisesValidate'], false));
          throw json.detail;
        }
        return json;
      })
      .then((json) => dispatch(updateExercisesValidateMessages(json)))
      .then(() => dispatch(updatePendingStateIn(['exercisesValidate'], false)))
      .then(() => dispatch(fetchExercises(coursePk)))
      .then(() => dispatch(fetchExerciseTree(coursePk)))
      .catch((err) => console.log(err));
  };
}


function reloadExercises(iAmSure = false, coursePkIn = null) {
  return (dispatch, getState) => {
    var coursePk = null;
    if (coursePkIn == null) {
      var state = getState();
      coursePk = state.get('activeCourse');
    } else {
      coursePk = coursePkIn;
    }
    var username = state.get('login').get('username')
    if ( username != 'super' ){
      return null
      }
    var payload = {
      i_am_sure: iAmSure
    };
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data
    };
    dispatch(updatePendingStateIn(['exercisesReload'], true));
    return jsonfetch('/course/' + coursePk + '/exercises/reload/json/', fetchconfig)
      .then((response) => response.json())
      .then((json) => {
        if ('detail' in json) {
          UIkit.notify(json.detail, { timeout: 10000, status: 'danger' });
          dispatch(updatePendingStateIn(['exercisesReload'], false));
          throw json.detail;
        }
        return json;
      })
      .then((json) => dispatch(updateExercisesReloadMessages(json)))
      .then(() => dispatch(updatePendingStateIn(['exercisesReload'], false)))
      .then(() => dispatch(fetchExercises(coursePk)))
      .then(() => dispatch(fetchExerciseTree(coursePk)))
      .catch((err) => console.log(err));
  };
}

function fetchExerciseRecentResults() {
  // console.log("fetchExerciseRecentResults entered ")
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(updatePendingStateIn(['results', 'exercises', exercise, 'recent'], true));
    return jsonfetch('/exercise/' + exercise + '/recentresults')
      .then((response) => response.json())
      .then((json) => dispatch(setExerciseRecentResults(exercise, json)))
      .then(() => dispatch(updatePendingStateIn(['results', 'exercises', exercise, 'recent'], false)))
      .catch((err) => console.log(err));
  };
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
  reUploadImage,
  deleteImageAnswer,
  fetchImageAnswers,
  checkQuestion,
  fetchAllExerciseStatistics,
  fetchExerciseStatistics,
  fetchStudentResults,
  fetchStudentDetailResults,
  reloadExercises,
  validateExercises,
  fetchUserExercises,
  fetchExerciseRecentResults,
  fetchCourseStatistics,
  fetchSendMyAudits,
};
export * from './fetchers/audit.js';
export * from './fetchers/exercise.js';
export * from './fetchers/folder.js';
export * from './fetchers/assets.js';
export * from './fetchers/tasks.js';
export * from './fetchers/course.js';
export * from './fetchers/server.js';
export * from './fetchers/canvas.js';
export * from './fetchers/regrade.js';
export * from './fetchers/analyze.js';
