import {getcookie} from 'cookies.js';
import {SUBPATH} from 'settings.js';
import immutable from 'immutable';
import {store} from 'store.js';

var CSRF_TOKEN_NAME = getcookie('csrf_cookie_name') ? getcookie('csrf_cookie_name')[0] : 'csrftoken' // Duplicate CSRF tokens if several sites
var CSRF_TOKEN = getcookie(CSRF_TOKEN_NAME)[0];

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
    if ( Object.keys(options).length   ){
      }
    return fetch(SUBPATH + url, _opts.toJS());
}

export {jsonfetch, CSRF_TOKEN}
