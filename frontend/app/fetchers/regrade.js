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
    dispatch(updatePendingStateIn( ['regradeResults',exercise], true));
    var taskOptions = {
      progressAction: (progress,status) => dispatch => { dispatch(updatePendingStateIn(['regradeResults',exercise], progress));
                                                  dispatch(updatePendingStateIn(['regradePreview',exercise,'preview'], status));
                                                  },
      completeAction: (data) => dispatch => {
        dispatch(updateRegradeResults(exercise,data));
        dispatch(updatePendingStateIn(['regradeResults',exercise], false));
      }
    };

   return dispatch(enqueueTask('/exercise/' + exercise + '/regrade_resultsasync', taskOptions))
      .catch(err =>  dispatch(updatePendingStateIn( ['regradeResults',exercise], false)))


  }
 }

function  fetchRegradeTask(exercise,yesno)  {
  console.log("FETCHERS ", exercise, yesno)
  var s = '/exercise/' + String(exercise) + '/accept_regrade/' + String( yesno )
  console.log("s = ", s )
  return (dispatch) => {
    return jsonfetch(s)
    .then( dispatch(updatePendingStateIn(['regradeResults',exercise], 'finished')) )
    .catch( err => console.log(err) );
  }
}




export { fetchExerciseRegradeResults  ,fetchRegradeTask }
