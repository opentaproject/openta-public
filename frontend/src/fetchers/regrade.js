// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import immutable from 'immutable';
import { jsonfetch, sendFrontendLog } from '../fetch_backend.js';
import { enqueueTask } from '../fetchers/tasks.js';

import { updatePendingStateIn } from '../actions.js';

import { setExerciseRegradeResults, updateRegradeResults } from '../actions/regrade.js';

function fetchExerciseRegradeResults(exercise_key, question_key) {
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(setExerciseRegradeResults(exercise, question_key, immutable.List([])));
    dispatch(updatePendingStateIn(['regradeResults', exercise], true));
    var taskOptions = {
      progressAction: (progress, status) => (dispatch) => {
        dispatch(updatePendingStateIn(['regradeResults', exercise], progress));
        dispatch(updatePendingStateIn(['regradePreview', exercise, 'preview'], status));
      },
      completeAction: (data) => (dispatch) => {
        dispatch(updateRegradeResults(exercise, question_key, data));
        dispatch(updatePendingStateIn(['regradeResults', exercise], false));
      }
    };

    return dispatch(enqueueTask('/exercise/' + exercise + '/regrade_resultsasync/' + question_key, taskOptions)).catch(
      (err) => {
        sendFrontendLog('error', 'fetchExerciseRegradeResults failed', { exercise, question_key, error: String(err) });
        return dispatch(updatePendingStateIn(['regradeResults', exercise], false));
      }
    );
  };
}

function fetchRegradeTask(exercise, yesno) {
  var s = '/exercise/' + String(exercise) + '/accept_regrade/' + String(yesno);
  var path = immutable.fromJS(['activeExercise', 'student']);
  return (dispatch) => {
    return (
      jsonfetch(s)
        .then((response) => response.json())
        .then(dispatch(updatePendingStateIn(['regradeResults', exercise], 'finished')))
        //.then( dispatch(updateMenuPath(path)))  // THIS CHANGES MENU PATH
        .catch((err) => {
          console.log(err);
          sendFrontendLog('error', 'fetchRegradeTask failed', { exercise, yesno, error: String(err) });
        })
    );
  };
}

export { fetchExerciseRegradeResults, fetchRegradeTask };
