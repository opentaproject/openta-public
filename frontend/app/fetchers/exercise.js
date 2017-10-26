import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updatePendingStateIn,
    setExerciseHistory,
    updateExerciseActiveXML,
    updateExerciseXML
} from '../actions.js';

function fetchAddExercise(path, name) {
    return dispatch => {
        var payload = {
            path: '/' + path.join('/'),
            name: name
        };
        var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        };
        return jsonfetch('/exercises/add/', fetchconfig)
            .then( res => res.json() )
            .then( json => {
                if('error' in json)
                        UIkit.notify(json.error, {timeout: 10000, status: 'danger'});
            })
            .catch(err => console.dir(err));
    };
}

function fetchMoveExercise(exercise, path) {
    return dispatch => {
        var payload = {
            new_folder: path
        };
        var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        };
        return jsonfetch('/exercise/' + exercise + '/move', fetchconfig)
            .then( res => res.json() )
            .catch(err => console.dir(err));
    };
}

function fetchRenameFolder(path, newName) {
    return dispatch => {
        var payload = {
            old_folder: '/' + path.join('/'),
            new_name: newName
        };
        var fetchconfig = {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        };
        return jsonfetch('/exercises/renamefolder/', fetchconfig)
            .then( res => res.json() )
            .then( json => {
                if('error' in json)
                    throw json['error'];
                else
                    return json;
            });
    };
}

function fetchDeleteExercise(exerciseKey) {
    return dispatch => {
        var fetchconfig = {
            method: "DELETE",
            headers: { "Content-Type": "application/json" }
        };
        return jsonfetch('/exercise/' + exerciseKey + '/delete', fetchconfig)
            .then( res => res.json() )
            .catch(err => console.dir(err));
    };
}

function fetchExerciseHistoryList(exerciseKey) {
    return dispatch => {
    return jsonfetch('/exercise/' + exerciseKey + '/history')
        .then(res => res.json())
            .then(json => dispatch(setExerciseHistory(exerciseKey, json)));
    };
}

function fetchExerciseXMLHistory(exercise, name) {
    return dispatch => {
        dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingXML'], true));
        return jsonfetch('/exercise/' + exercise + '/history/' + name + '/xml')
            .then( res => {
                dispatch(updatePendingStateIn( ['exercises', exercise, 'loadingXML'], false));
                return res;
            })
            .then( res => res.json() )
            .then( json => {
                if( 'error' in json)
                    throw json.error;
                else
                    return json;
            })
            .then( json => json.xml )
            .then( xml => {
                dispatch(updateExerciseActiveXML(exercise, xml));
                return dispatch(updateExerciseXML(exercise, xml));
            })
            .catch(err => {
                console.dir(err);
            });
    };
}

export { fetchAddExercise, fetchExerciseHistoryList, fetchExerciseXMLHistory, fetchDeleteExercise, fetchMoveExercise, fetchRenameFolder }
