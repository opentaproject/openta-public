import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';
import {enqueueTask} from '../fetchers/tasks.js';


import {
    updatePendingStateIn,
} from '../actions.js';


import {
    setExerciseRegradeResults,
    updateRegradeResults,
} from '../actions/regrade.js';

function fetchExerciseRegradeResults() {
  console.log("fetchExerciseRegradeResults")
  return (dispatch, getState) => {
    var state = getState();
    var exercise = state.get('activeExercise');
    dispatch(setExerciseRegradeResults(exercise,  immutable.List([])) )
    dispatch(updatePendingStateIn( ['regradeResults'], true));
    var taskOptions = {
      progressAction: (progress,status) => dispatch => { dispatch(updatePendingStateIn(['regradeResults'], progress));
                                                  dispatch(updatePendingStateIn(['regradePreview','preview'], status));
                                                  },
      completeAction: (data) => dispatch => {
        dispatch(updateRegradeResults(exercise,data));
        dispatch(updatePendingStateIn(['regradeResults'], false));
      }
    };

   return dispatch(enqueueTask('/exercise/' + exercise + '/regrade_resultsasync', taskOptions))
      .catch(err =>  dispatch(updatePendingStateIn( ['regradeResults'], false)))


 //return jsonfetch('/exercise/' + exercise + '/regraderesults')
 //      .then(response => response.json())
 //     .then( json => dispatch(setExerciseRegradeResults(exercise, json)))
 //     .then( () => dispatch(updatePendingStateIn( ['regradeResults'], false)))
 //     .catch( err => console.log(err) );
  }
 }

export { fetchExerciseRegradeResults }
