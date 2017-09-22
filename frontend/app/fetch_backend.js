import {getcookie} from 'cookies.js';
import {SUBPATH} from 'settings.js';
import immutable from 'immutable';
import {store} from 'store.js';

var CSRF_TOKEN = getcookie('csrftoken')[0];

function jsonfetch(url, options = {}) {//{{{
    var lang = store.getState().get('language', 'en');
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
}//}}}

export {jsonfetch, CSRF_TOKEN}
