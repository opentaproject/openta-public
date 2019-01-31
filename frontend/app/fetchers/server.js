import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updatePendingStateIn,
    updateTask
} from '../actions.js';

import {fetchCourses, fetchTaskProgress} from '../fetchers.js';

function uploadProgress(dispatch, evt) {
  if(evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['server', 'uploadProgress'], evt.loaded / evt.total));
  }
  else if(evt.position && evt.totalSize && evt.totalSize > 0) {
      return dispatch(updatePendingStateIn(['server', 'uploadProgress'], evt.position / evt.totalSize));
  }
}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function uploadServer(file) {
  return dispatch => {
      if (!file ) return;
      var fd = new FormData();
      fd.append('file', file);
      var xhr = new XMLHttpRequest();
      xhr.responseType = 'json';
      xhr.open("POST", SUBPATH + "/server/import/");
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
      xhr.setRequestHeader('Accept', 'application/json');
      if(xhr.upload)
        xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt);
      xhr.onload = () => {
        dispatch(updatePendingStateIn(["server", "uploadPending"], false));
        dispatch(updatePendingStateIn(["server", "uploadProgress"], 1.0));
        dispatch(updatePendingStateIn(["server", "processProgress"], 0.0));
        //dispatch(updatePendingStateIn(["server", "uploadMessages"], xhr.response));
        dispatch(updateTask(xhr.response.task_id, {
            progress: 0,
            done: false
        }));
        //setTimeout(() => {dispatch(fetchTaskProgress(json.task_id, completeAction, progressAction));}, 1000);
        ;
        dispatch(fetchTaskProgress(xhr.response.task_id, undefined,
            (progress, status) => updatePendingStateIn(["server", "processStatus"], status)
        ));
      };
      xhr.send(fd);
      dispatch(updatePendingStateIn(['server', 'uploadPending'], true));
    }
}

export { uploadServer };