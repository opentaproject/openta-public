import { getcookie } from './cookies';
import immutable from 'immutable';
import { store } from './store';

var CSRF_TOKEN_NAME = getcookie('csrf_cookie_name') ? getcookie('csrf_cookie_name')[0] : 'csrftoken'; // Duplicate CSRF tokens if several sites
var CSRF_TOKEN = getcookie(CSRF_TOKEN_NAME)[0];

function jsonfetch(url, options = {}) {
  const state = store.getState();
  var lang = state.get('lang', state.getIn(['course', 'languages', 0], 'en'));
  var defaults = {
    headers: {
      'X-CSRFToken': CSRF_TOKEN,
      Accept: 'application/json',
      'Accept-Language': lang,
      // Inform backend that frontend uses tolerant error handling
      'X-Frontend-Message': 'graceful-errors'
    },
    credentials: 'same-origin'
  };
  var _opts = immutable.fromJS(defaults).mergeDeep(immutable.fromJS(options));
  if (Object.keys(options).length) {
  }
  const result = fetch(url, _opts.toJS());
  return result;
}

export { jsonfetch, CSRF_TOKEN };

// Lightweight client log reporting to backend
function sendFrontendLog(level, message, context = {}) {
  console.log("SEND_FRONTEND_LOG")
  try {
    const payload = {
      level,
      message,
      context,
      ts: new Date().toISOString()
    };
    const fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    };
    // Fire-and-forget; swallow errors to not cascade
    return jsonfetch('/frontend_log/', fetchconfig).catch(() => {});
  } catch (_) {
    return Promise.resolve();
  }
}

export { sendFrontendLog };
