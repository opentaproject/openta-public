import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updateTask,
} from '../actions.js';
import { handleMessages } from '../fetchers';

function fetchTaskProgress(taskId, completeAction, progressAction) {
    return dispatch => {
        return jsonfetch('/queuetask/' + taskId)
            .then( res => res.json() )
            .then( json => {
                dispatch(updateTask(taskId, {
                    progress: json.progress,
                    done: json.done,
                    status: json.status
                }));
                if(progressAction !== undefined)
                    dispatch(progressAction(json.progress, json.status));
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
                if(!json.done)
                    setTimeout(() => {dispatch(fetchTaskProgress(taskId, completeAction, progressAction));}, 1000);
            })
            .catch( err => console.dir(err) );
    };
}

function enqueueTask(url, {data, method="GET", completeAction, progressAction} = {}) {
    return dispatch => {
        var fetchconfig = {
            method: method
        };
        if(data !== undefined) {
            fetchconfig.headers = { "Content-Type": "application/json" };
            fetchconfig.body = JSON.stringify(data);
        }
        return jsonfetch(url, fetchconfig)
            .then( res => res.json() )
            .then( json => handleMessages(json) )
            .then( json => {
                dispatch(updateTask(json.task_id, {
                    progress: 0,
                    done: false
                }));
                //setTimeout(() => {dispatch(fetchTaskProgress(json.task_id, completeAction, progressAction));}, 1000);
                dispatch(fetchTaskProgress(json.task_id, completeAction, progressAction));
                return json.task_id;
            });
    };
}

export { enqueueTask, fetchTaskProgress };
