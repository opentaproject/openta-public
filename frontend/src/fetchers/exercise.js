// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import { jsonfetch, sendFrontendLog } from '../fetch_backend.js';

import {
  setExerciseHistory,
  updateExerciseActiveXML,
  updateExerciseXML,
  updatePendingStateIn,
  updateSelectedExercisesMeta
} from '../actions.js';

function fetchAddExercise(path, name, course_pk) {
  return (dispatch) => {
    var payload = {
      path: '/' + path.join('/'),
      course_pk: course_pk,
      name: name
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    return jsonfetch('/exercises/add/', fetchconfig)
      .then((res) => res.json())
      .then((json) => {
        if ('error' in json) {
          UIkit.notify(json.error, { timeout: 10000, status: 'danger' });
        }
      })
      .catch((err) => {
        console.dir(err);
        sendFrontendLog('error', 'fetchAddExercise failed', { path, name, course_pk, error: String(err) });
      });
  };
}

function fetchMoveExercise(exercises, path) {
  console.log('fetchMoveExercise', exercises, path);
  return (dispatch) => {
    var payload = {
      new_folder: path,
      exercises: exercises
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    return jsonfetch('/exercise/move', fetchconfig)
    .then((res) => res.json())
      .then((json) => {
        if ('error' in json) {
          UIkit.notify(json.error, { timeout: 10000, status: 'danger' });
        }
      })
      .catch((err) => {
        console.dir(err);
        sendFrontendLog('error', 'fetchMoveExercise failed', { exercises, path, error: String(err) });
      });

  };
}

function fetchExerciseHandle(exercises, path, action) {
  return (dispatch) => {
    var payload = {
      path: path,
      exercises: exercises,
      action
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    return jsonfetch('/exercise/handle', fetchconfig)
     .then((res) => res.json())
      .then((json) => {
        if ('error' in json) {
          UIkit.notify(json.error, { timeout: 10000, status: 'danger' });
        }
      })
      .catch((err) => {
        console.dir(err);
        sendFrontendLog('error', 'fetchExerciseHandle failed', { exercises, path, action, error: String(err) });
      });


  };
}

function fetchSetSelectedExercises(selectedExercises) {
  if (!selectedExercises) {
    selectedExercises = [];
  }
  return (dispatch) => {
    var payload = {
      selectedExercises: selectedExercises
    };
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };

    return jsonfetch('/exercise/set_selected/selected_exercises', fetchconfig)
      .then((res) => res.json())
      .then((json) => dispatch(updateSelectedExercisesMeta(json)));
  };
}


function fetchDeleteExercise(exerciseKey) {
  return (dispatch) => {
    var fetchconfig = {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    };
    return jsonfetch('/exercise/' + exerciseKey + '/delete', fetchconfig)
         .then((res) => res.json())
      .then((json) => {
        if ('error' in json) {
          UIkit.notify(json.error, { timeout: 10000, status: 'danger' });
        }
      })
      .catch((err) => console.dir(err));


  };
}

function fetchExerciseHistoryList(exerciseKey) {
  return (dispatch) => {
    return jsonfetch('/exercise/' + exerciseKey + '/history')
      .then((res) => res.json())
      .then((json) => dispatch(setExerciseHistory(exerciseKey, json)))
      .catch((err) => {
        console.warn('Failed to fetch history list', exerciseKey, err);
        sendFrontendLog('error', 'fetchExerciseHistoryList failed', { exerciseKey, error: String(err) });
      });
  };
}

function fetchExerciseXMLHistory(exercise, name) {
  return (dispatch) => {
    dispatch(updatePendingStateIn(['exercises', exercise, 'loadingXML'], true));
    return jsonfetch('/exercise/' + exercise + '/history/' + name + '/xml')
      .then((res) => {
        dispatch(updatePendingStateIn(['exercises', exercise, 'loadingXML'], false));
        return res;
      })
      .then((res) => res.json())
      .then((json) => {
        if ('error' in json) {
          throw json.error;
        } else {
          return json;
        }
      })
      .then((json) => json.xml)
      .then((xml) => {
        dispatch(updateExerciseActiveXML(exercise, xml));
        return dispatch(updateExerciseXML(exercise, xml));
      })
      .catch((err) => {
        console.dir(err);
        sendFrontendLog('error', 'fetchExerciseXMLHistory failed', { exercise, name, error: String(err) });
      });
  };
}

export {
  fetchAddExercise,
  fetchExerciseHistoryList,
  fetchExerciseXMLHistory,
  fetchDeleteExercise,
  fetchMoveExercise,
  fetchSetSelectedExercises,
  fetchExerciseHandle
};
