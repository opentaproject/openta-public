import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updateExerciseState,
    updatePendingStateIn
} from '../actions.js';

import {handleMessages} from '../fetchers.js';

function fetchAssets(exercise = null) {
    return (dispatch, getState) => {
        var state = getState();
        if(exercise === null)
            exercise = state.get('activeExercise');
        return jsonfetch('/exercise/' + exercise + '/listassets')
            .then( res => res.json() )
            .then( json => {
                const data = {
                    'assets': json
                };
                return dispatch(updateExerciseState(exercise, data));
            });
    };
}

function uploadProgress(dispatch, evt, exerciseKey) {//{{{
  if(evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['exercise', exerciseKey, 'assetUploadProgress'], evt.loaded / evt.total));
  }
  else if(evt.position && evt.totalSize && evt.totalSize > 0) {
      return dispatch(updatePendingStateIn(['exercise', exerciseKey, 'assetUploadProgress'], evt.position / evt.totalSize));
  }
}//}}}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function uploadAsset(exerciseKey, file) {
  return dispatch => {
    return new Promise((resolve, reject) => {
      if (!file) return;
      var fd = new FormData();
      fd.append("file", file);
      var xhr = new XMLHttpRequest();
      xhr.open("POST", SUBPATH + "/exercise/" + exerciseKey + "/uploadasset");
      xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
      xhr.setRequestHeader("Accept", "application/json");
      if (xhr.upload) xhr.upload.onprogress = evt => throttleUploadProgress(dispatch, evt, exerciseKey);
      xhr.onload = () => {
        dispatch(updatePendingStateIn(["exercise", exerciseKey, "assetUploadPending"], false));
        dispatch(updatePendingStateIn(["exercise", exerciseKey, "assetUploadProgress"], 1.0));
        dispatch(fetchAssets());
        resolve(handleMessages(JSON.parse(xhr.response)));
      };
      xhr.onerror = () => reject(handleMessages(JSON.parse(xhr.response)));
      xhr.send(fd);
      dispatch(updatePendingStateIn(["exercise", exerciseKey, "assetUploadPending"], true));
    });
  };
}

function deleteAsset(exerciseKey, asset) {
    return dispatch => {
        var fetchconfig = {
            method: "DELETE"
        };
        return jsonfetch("/exercise/" + exerciseKey + "/asset/" + asset + "/delete", fetchconfig);
    };
}

export { fetchAssets, uploadAsset, deleteAsset }
