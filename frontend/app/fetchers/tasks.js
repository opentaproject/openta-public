import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updateTask,
} from '../actions.js';

function fetchTaskProgress(taskId, completeAction) {
    return dispatch => {
        return jsonfetch('/queuetask/' + taskId)
            .then( res => res.json() )
            .then( json => {
                dispatch(updateTask(taskId, {
                    progress: json.progress,
                    done: json.done
                }));
                if(json.done) {
                    jsonfetch('/queuetask/' + taskId + '/result')
                        .then( res => res.json())
                        .then( json => {
                            if(completeAction !== undefined)
                                dispatch(completeAction(json));
                        })
                        .catch( err => {
                            console.dir(err);
                                dispatch(updateTask(taskId, {
                                    status: "error",
                                    error: err
                                }));
                        });
                }
                if(!json.done && json.status == 'Working')
                    setTimeout(() => {dispatch(fetchTaskProgress(taskId, completeAction));}, 1000);
            })
            .catch( err => console.dir(err) );
    };
}

function enqueueTask(url, data, completeAction) {
    return dispatch => {
        var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        };
        return jsonfetch(url, fetchconfig)
            .then( res => res.json() )
            .then( json => {
                setTimeout(() => {dispatch(fetchTaskProgress(json.task_id, completeAction));}, 1000);
                return json.task_id;
            })
            .catch(err => console.dir(err));
    };
}

export { enqueueTask };
