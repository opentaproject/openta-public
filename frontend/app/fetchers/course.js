import {logImmutable, keyIn} from '../immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';

import {
    updateCourse,
} from '../actions.js';

function fetchCourse() {
    return dispatch => {
        return jsonfetch('/course/')
            .then(res => res.json())
            .then(json => dispatch(updateCourse(json)));
    };
}

export { fetchCourse };
