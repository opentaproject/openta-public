import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updateCourse,
    updateCourses,
} from '../actions.js';

function fetchCourse(coursePk) {
    return dispatch => {
        return jsonfetch('/course/' + coursePk + '/')
            .then(res => res.json())
            .then(json => dispatch(updateCourse(json)));
    };
}

function fetchCourses() {
    return dispatch => {
        return jsonfetch('/courses/')
            .then(res => res.json())
            .then(json => json.reduce( (map, obj) => { return map.set(obj.pk, immutable.fromJS(obj)); }, immutable.Map({}))) 
            .then(json => dispatch(updateCourses(json)));
    };
}

export { fetchCourse, fetchCourses };
