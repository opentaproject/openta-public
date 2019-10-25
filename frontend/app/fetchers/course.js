import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updateCourse,
    updateCourses,
    updatePendingStateIn
} from '../actions.js';

import {
    fetchExercises,
    fetchExerciseTree
} from '../fetchers.js';

function fetchCourse(coursePk) {
    return dispatch => {
        return jsonfetch('/course/' + coursePk + '/')
            .then(res => res.json())
            .then(json => dispatch(updateCourse(json)));
    };
}

function fetchCourses() {
    return dispatch => {
        return jsonfetch('/courses/')
            .then(res => res.json())
            .then(json => json.reduce( (map, obj) => { return map.set(obj.pk, immutable.fromJS(obj)); }, immutable.Map({})))
            .then(json => dispatch(updateCourses(json)));
    };
}

function uploadProgress(dispatch, evt, courseKey) {
  if(evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['course', courseKey, 'exercisesUploadProgress'], evt.loaded / evt.total));
  }
  else if(evt.position && evt.totalSize && evt.totalSize > 0) {
      return dispatch(updatePendingStateIn(['course', courseKey, 'exercisesUploadProgress'], evt.position / evt.totalSize));
  }
}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function uploadExercises(courseKey, file) {
  return dispatch => {
      if (!file ) return;
      var fd = new FormData();
      fd.append('file', file);
      var xhr = new XMLHttpRequest();
      xhr.responseType = 'json';
      xhr.open("POST", SUBPATH + "/course/" + courseKey + '/uploadexercises/');
      xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
      xhr.setRequestHeader('Accept', 'application/json');
      if(xhr.upload)
        xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, courseKey);
      xhr.onload = () => {
        dispatch(updatePendingStateIn(["course", courseKey, "exercisesUploadPending"], false));
        dispatch(updatePendingStateIn(["course", courseKey, "exercisesUploadProgress"], 1.0));
        dispatch(updatePendingStateIn(["course", courseKey, "exercisesUploadMessages"], xhr.response));
        dispatch(fetchExercises(courseKey));
        dispatch(fetchExerciseTree(courseKey));
        //dispatch(fetchAssets());
      };
      xhr.send(fd);
      dispatch(updatePendingStateIn(['course', courseKey, 'exercisesUploadPending'], true));
    }
} 

export { fetchCourse, fetchCourses, uploadExercises };
