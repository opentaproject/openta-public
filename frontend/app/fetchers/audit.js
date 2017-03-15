import {logImmutable, keyIn} from '../immutablehelpers.js'
import _ from 'lodash'
import immutable from 'immutable'
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js'
import {SUBPATH} from '../settings.js';

import {
  updateAudits,
  updatePendingStateIn,
  setAuditData,
  setAuditExerciseStats,
} from '../actions.js';

import {
} from '../fetchers';

function uploadProgress(dispatch, evt, auditPk) {//{{{
  if(evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'uploadProgress'], evt.loaded / evt.total));
  }
  else if(evt.position && evt.totalSize && evt.totalSize > 0) {
    return dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'uploadProgress'], evt.position / evt.totalSize));
  }
}//}}}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function uploadAuditResponseFile(audit, file) { 
  return dispatch => {
      if (!file ) return;
      var fd = new FormData();
      fd.append('file', file);
      var xhr = new XMLHttpRequest();
      xhr.open("POST", SUBPATH + "/auditresponsefile/new/" + audit + "/");
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
      xhr.setRequestHeader('Accept', 'application/json');
      if(xhr.upload)
        xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, audit);
      xhr.onload = () => {
        dispatch(updatePendingStateIn(['audit', 'audits', audit, 'uploadPending'], false));
        dispatch(updatePendingStateIn(['audit', 'audits', audit, 'uploadProgress'], 1.0));
        dispatch(fetchCurrentAuditsExercise());
      }
      xhr.send(fd);
      dispatch(updatePendingStateIn(['audit', 'audits', audit, 'uploadPending'], true));
    }
} 

function deleteAuditResponseFile(auditResponseId) {
  return dispatch => {
    var fetchconfig = {
      method: "POST",
    }
    return jsonfetch('/auditresponsefile/delete/' + auditResponseId + '/', fetchconfig)
      .then( res => res.json() )
      .catch(err => console.dir(err))
  }
}

function fetchUnsentAudits() {
  return dispatch => {
    dispatch(updatePendingStateIn( ['audit', 'fetchUnsertAudits'], true));
    return jsonfetch('/audit/unsent/')
      .then(response => response.json())
      .then(json => json.reduce( (map, obj) => { return map.set(obj.pk, immutable.fromJS(obj)); }, immutable.Map({}))) 
      .then(immutableMap => {
        dispatch(updateAudits(immutableMap))
      })
      .then( () => dispatch(updatePendingStateIn( ['audit', 'fetchUnsentAudits'], false)))
      .catch( err => console.log(err) );
  }
}

function fetchCurrentAuditsExercise() {
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(updatePendingStateIn( ['audit', 'fetchAudits'], true));
    dispatch(fetchAuditExerciseStats());
    return jsonfetch('/audit/get/exercise/' + exercise)
      .then(response => response.json())
      .then(json => json.reduce( (map, obj) => { return map.set(obj.pk, immutable.fromJS(obj)); }, immutable.Map({}))) 
      .then(immutableMap => dispatch(updateAudits(immutableMap)))
      .then( () => dispatch(updatePendingStateIn( ['audit', 'fetchAudits'], false)))
      .catch( err => console.log(err) );
  }
}

function fetchAuditExerciseStats() {
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(updatePendingStateIn( ['audit', 'fetchAuditStats'], true));
    return jsonfetch('/audit/stats/exercise/' + exercise)
      .then(response => response.json())
      .then(json => dispatch(setAuditExerciseStats(exercise, json)))
      .then( () => dispatch(updatePendingStateIn( ['audit', 'fetchAuditStats'], false)))
      .catch( err => console.log(err) );
  }
}

function sendAudit(auditPk, bcc) {
  return dispatch => {
    var payload = { 'bcc': bcc };
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
    return jsonfetch('/audit/send/' + auditPk + '/', fetchconfig)
      .then( res => res.json() )
      .catch(err => console.dir(err))
  }
}

function deleteAudit(auditPk) {
  return dispatch => {
    var fetchconfig = {
      method: "POST",
    }
    return jsonfetch('/audit/delete/' + auditPk + '/', fetchconfig)
      .then( res => res.json() )
      .catch(err => console.dir(err))
  }
}

function saveAudit(auditPk, auditData) {
  return dispatch => {
    var selectedData = auditData.filter(keyIn('pk','message', 'subject', 'published', 'revision_needed', 'force_passed')).toJS();
    var payload = {
      'audit': selectedData
    };
    var postData = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: postData
    }
    return jsonfetch('/audit/update/' + auditPk + '/', fetchconfig)
      .then( res => res.json() )
  }
}

function fetchNewAudit(exercise) {
  return dispatch => {
    dispatch(updatePendingStateIn( ['audit', 'newAudit'], true));
    return jsonfetch('/audit/new/exercise/' + exercise)
      .then( () => dispatch(fetchCurrentAuditsExercise()) )
      .then( () => dispatch(updatePendingStateIn( ['audit', 'audits'], false)))
      .catch( err => console.log(err) );
  }
}

function addAudit(exercise, studentPk) {
  return dispatch => {
    var payload = {
      'audit': {
        'exercise': exercise,
        'student': studentPk,
        'subject': 'Kontroll'
      }
    };
    var postData = JSON.stringify(payload);
    var fetchconfig = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: postData
    }
    return jsonfetch('/audit/add/', fetchconfig)
      .then( res => res.json() )
      .catch( err => console.dir(err) );
  }
}

export {
  fetchUnsentAudits,
  fetchCurrentAuditsExercise,
  fetchAuditExerciseStats,
  saveAudit,
  sendAudit,
  deleteAudit,
  fetchNewAudit,
  addAudit,
  uploadAuditResponseFile,
  deleteAuditResponseFile,
}
