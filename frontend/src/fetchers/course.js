// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import _ from 'lodash';
import immutable from 'immutable';
import { jsonfetch, CSRF_TOKEN, sendFrontendLog } from '../fetch_backend.js';
import { SUBPATH } from '../settings.js';

import { updateCourse, updateCourses, updatePendingStateIn } from '../actions.js';

import { fetchExercises, fetchExerciseTree } from '../fetchers.js';

function fetchCourse(coursePk) {
  return (dispatch) => {
    return jsonfetch('/course/' + coursePk + '/')
      .then((res) => res.json())
      .then((json) => dispatch(updateCourse(json)))
      .catch((err) => {
        console.warn('Failed to fetch course', coursePk, err);
        sendFrontendLog('error', 'fetchCourse failed', { coursePk, error: String(err) });
      });
  };
}

function fetchCourses() {
  return (dispatch) => {
    return jsonfetch('/courses/')
      .then((res) => res.json())
      .then((json) =>
        json.reduce((map, obj) => {
          return map.set(obj.pk, immutable.fromJS(obj));
        }, immutable.Map({}))
      )
      .then((json) => dispatch(updateCourses(json)))
      .catch((err) => {
        console.warn('Failed to fetch courses', err);
        sendFrontendLog('error', 'fetchCourses failed', { error: String(err) });
      });
  };
}

function uploadProgress(dispatch, evt, courseKey) {
  if (evt.loaded && evt.total && evt.total > 0) {
    return dispatch(updatePendingStateIn(['course', courseKey, 'UploadProgress'], evt.loaded / evt.total));
  } else if (evt.position && evt.totalSize && evt.totalSize > 0) {
    return dispatch(updatePendingStateIn(['course', courseKey, 'UploadProgress'], evt.position / evt.totalSize));
  }
}

var throttleUploadProgress = _.throttle(uploadProgress, 300);

function uploadZip(courseKey, file, destination) {
  return (dispatch) => {
    if (!file) {
      return;
    }
    console.log('DESTIONATION = ', destination);
    console.log('file = = ', file);
    console.log('courseKey = = ', courseKey);
    var fd = new FormData();
    fd.append('file', file);
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.open('POST', SUBPATH + '/course/' + courseKey + '/uploadzip/');
    xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.setRequestHeader('X-Frontend-Message', 'graceful-errors');
    if (xhr.upload) {
      xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, courseKey);
    }
    xhr.onload = () => {
      dispatch(updatePendingStateIn(['course', courseKey, 'UploadPending'], false));
      dispatch(updatePendingStateIn(['course', courseKey, 'UploadProgress'], 1.0));
      dispatch(updatePendingStateIn(['course', courseKey, 'UploadMessages'], xhr.response));
      //dispatch(fetchExercises(courseKey));
      //dispatch(fetchExerciseTree(courseKey));
      //dispatch(fetchAssets());
    };
    xhr.send(fd);
    dispatch(updatePendingStateIn(['course', courseKey, 'UploadPending'], true));
  };
}

function uploadExercises(courseKey, file) {
  return (dispatch) => {
    if (!file) {
      return;
    }
    var fd = new FormData();
    fd.append('file', file);
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.open('POST', SUBPATH + '/course/' + courseKey + '/uploadexercises/');
    xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.setRequestHeader('X-Frontend-Message', 'graceful-errors');
    if (xhr.upload) {
      xhr.upload.onprogress = (evt) => throttleUploadProgress(dispatch, evt, courseKey);
    }
    xhr.onload = () => {
      dispatch(updatePendingStateIn(['course', courseKey, 'UploadPending'], false));
      dispatch(updatePendingStateIn(['course', courseKey, 'UploadProgress'], 1.0));
      dispatch(updatePendingStateIn(['course', courseKey, 'UploadMessages'], xhr.response));
      dispatch(fetchExercises(courseKey));
      dispatch(fetchExerciseTree(courseKey));
      //dispatch(fetchAssets());
    };
    xhr.send(fd);
    dispatch(updatePendingStateIn(['course', courseKey, 'UploadPending'], true));
  };
}

export { fetchCourse, fetchCourses, uploadExercises, uploadZip };
