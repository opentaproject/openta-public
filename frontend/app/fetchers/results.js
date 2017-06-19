import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updateCustomResults,
} from '../actions.js';

function fetchCustomResultsProgress(taskId) {
    return dispatch => {
        return jsonfetch('/queuetask/' + taskId)
            .then( res => res.json() )
            .then( json => {
                dispatch(updateCustomResults({
                    progress: json.progress,
                    done: json.done
                }));
                if(!json.done && json.status == 'Working')
                    setTimeout(() => {dispatch(fetchCustomResultsProgress(taskId));}, 1000);
            });
    };
}

function fetchCustomResults(exercises) {
    return dispatch => {
        var payload = {
            exercises: exercises
        };
        var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        };
        return jsonfetch('/statistics/customresult', fetchconfig)
            .then( res => res.json() )
            .then( json => {
                dispatch(updateCustomResults({taskId: json.task_id}));
                setTimeout(() => {dispatch(fetchCustomResultsProgress(json.task_id));}, 1000);
            })
            .catch(err => console.dir(err));
    };
}

export { fetchCustomResults };
