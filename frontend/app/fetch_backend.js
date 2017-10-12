import {getcookie} from 'cookies.js';
import {SUBPATH} from 'settings.js';
import immutable from 'immutable';
import {store} from 'store.js';

var CSRF_TOKEN = getcookie('csrftoken')[0];

function jsonfetch(url, options = {}) {
    const state = store.getState();
    var lang = state.get('lang', state.getIn(['course', 'languages', 0], 'en'));
    var defaults = {
        headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'Accept': 'application/json',
            'Accept-Language': lang
        },
        credentials: 'same-origin'
    };
    var _opts = immutable.fromJS(defaults).mergeDeep(immutable.fromJS(options));
    return fetch(SUBPATH + url, _opts.toJS());
}

export {jsonfetch, CSRF_TOKEN}
