import {getcookie} from 'cookies.js'
import {SUBPATH} from 'settings.js'
import immutable from 'immutable'

var CSRF_TOKEN = getcookie('csrftoken')[0]; 

function jsonfetch(url, options = {}) {//{{{
  var defaults = {
      headers: { 
        'X-CSRFToken': CSRF_TOKEN,
        'Accept': 'application/json',
      },
      credentials: 'same-origin'
  };
  var _opts = immutable.fromJS(defaults).mergeDeep(immutable.fromJS(options));
  return fetch(SUBPATH + url, _opts.toJS());
}//}}}

export {jsonfetch, CSRF_TOKEN}
