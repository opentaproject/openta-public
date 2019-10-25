import _ from 'lodash';

import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updatePendingStateIn,
    updateTask
} from '../actions.js';

import {
  fetchTaskProgress
} from '../fetchers.js';

function uploadProgress(dispatch, evt, courseKey) {
  if(evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['course', courseKey, 'canvasGradebookUploadProgress'], evt.loaded / evt.total));
  }
  else if(evt.position && evt.totalSize && evt.totalSize > 0) {
      return dispatch(updatePendingStateIn(['course', courseKey, 'canvasGradebookUploadProgress'], evt.position / evt.totalSize));
  }
}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function uploadCanvasGradebook(courseKey, file) {
  return dispatch => {
      if (!file ) return;
      var fd = new FormData();
      fd.append('file', file);
      var xhr = new XMLHttpRequest();
      xhr.responseType = 'json';
      xhr.open("POST", SUBPATH + "/course/" + courseKey + '/lti/canvasgradebook/');
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
      xhr.setRequestHeader('Accept', 'application/json');
      if(xhr.upload)
        xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, courseKey);
      xhr.onload = () => {
        var task = xhr.response;
        dispatch(updatePendingStateIn(["course", courseKey, "canvasGradebookUploadPending"], false));
        dispatch(updatePendingStateIn(["course", courseKey, "canvasGradebookUploadProgress"], 1.0));
        dispatch(updatePendingStateIn(["course", courseKey, "canvasGradebookTask"], task.task_id));
        // dispatch(updatePendingStateIn(["course", courseKey, "canvasGradebookUploadMessages"], messages));
        dispatch(updateTask(task.task_id, {
            progress: 0,
            done: false
        }));
        dispatch(fetchTaskProgress(task.task_id, undefined, undefined));
      };
      xhr.send(fd);
      dispatch(updatePendingStateIn(['course', courseKey, 'canvasGradebookUploadPending'], true));
    }
}

export {uploadCanvasGradebook};