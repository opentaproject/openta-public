import immutable from 'immutable';
import { jsonfetch, sendFrontendLog } from '../fetch_backend.js';
import { enqueueTask } from '../fetchers/tasks.js';

import { updatePendingStateIn } from '../actions.js';

import { setExerciseAnalyzeResults, updateAnalyzeResults } from '../actions/analyze.js';

function fetchExerciseAnalyzeResults(exercise_key, question_key) {
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(setExerciseAnalyzeResults(exercise, question_key, immutable.List([])));
    dispatch(updatePendingStateIn(['analyzeResults', exercise], true));
    var taskOptions = {
      progressAction: (progress, status) => (dispatch) => {
        dispatch(updatePendingStateIn(['analyzeResults', exercise], progress));
        dispatch(updatePendingStateIn(['analyzePreview', exercise, 'preview'], status));
      },
      completeAction: (data) => (dispatch) => {
        dispatch(updateAnalyzeResults(exercise, question_key, data));
        dispatch(updatePendingStateIn(['analyzeResults', exercise], false));
      }
    };

    return dispatch(enqueueTask('/exercise/' + exercise + '/analyze_resultsasync/' + question_key, taskOptions)).catch(
      (err) => {
        sendFrontendLog('error', 'fetchExerciseAnalyzeResults failed', { exercise, question_key, error: String(err) });
        return dispatch(updatePendingStateIn(['analyzeResults', exercise], false));
      }
    );
  };
}

function fetchAnalyzeTask(exercise, yesno) {
  var s = '/exercise/' + String(exercise) + '/accept_analyze/' + String(yesno);
  var path = immutable.fromJS(['activeExercise', 'student']);
  return (dispatch) => {
    return (
      jsonfetch(s)
        .then((response) => response.json())
        .then(dispatch(updatePendingStateIn(['analyzeResults', exercise], 'finished')))
        //.then( dispatch(updateMenuPath(path)))  // THIS CHANGES MENU PATH
        .catch((err) => {
          console.log(err);
          sendFrontendLog('error', 'fetchAnalyzeTask failed', { exercise, yesno, error: String(err) });
        })
    );
  };
}

export { fetchExerciseAnalyzeResults, fetchAnalyzeTask };
