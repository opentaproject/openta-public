import ReactDOM from 'react-dom/client';
import React from 'react';
import { Provider } from 'react-redux';
import 'whatwg-fetch';
import App from './components/App';
import { getcookie } from './cookies';
import {
  fetchCourse,
  fetchCourses,
  fetchExercise,
  fetchExercises,
  fetchExerciseTree,
  fetchLoginStatus,
  updatePendingStateIn
} from './fetchers';
import { fetchTranslationDict } from './fetchers/fetch_translations';

import {
  setActiveCourse,
  setActivityRange,
  setIFramed,
  setOpenTAVersion,
  setTimezone,
  updateDisplayStyle,
  updateExerciseFilter,
  updateLanguage
} from './actions';
import { jsonfetch } from './fetch_backend';
import { menuPositionUnder, navigateMenuArray } from './menu';
import { language_code, subdomain, SUBPATH, username, env_source, adobe_id  , answer_delay , user_permissions} from './settings';
import { store } from './store';

store.dispatch(fetchLoginStatus(globalInit.coursePk));

var language = language_code;
if (getcookie('lang') !== undefined) {
  if (getcookie('lang')[0] !== '""') {
    var cookielang = getcookie('lang')[0];
    language = cookielang;
    store.dispatch(updateLanguage(cookielang));
  }
}

// if (module.hot) {
//   module.hot.accept('./reducers', () => {
//     store.replaceReducer(require('./reducers').default);
//   });
//   module.hot.accept();

//   module.hot.dispose((data) => {
//     data.counter = store.getState();
//     [].slice.apply(document.querySelector('#app').children).forEach(function (c) {
//       c.remove();
//     });
//   });
// }

const load = () => {
  if (window.__APP_LOADED__) {
    return;
  }
  window.__APP_LOADED__ = true;
  // var cookiesEnabled = getcookie('cookieTest');
  // if (!(cookiesEnabled !== undefined && cookiesEnabled[0] == 'enabled')) {
  //   ReactDOM.render(<CookiesNotEnabled help_url={help_url} />, document.querySelector('#app'));
  //   return;
  // }

  store.dispatch(updatePendingStateIn(['course', 'loadingExercises'], true));
  store.dispatch(fetchTranslationDict(globalInit.coursePk, language));
  var defaultfilter = {
    required_exercises: true,
    optional_exercises: true,
    bonus_exercises: true,
    // 'all_exercises' : false ,
    //'published_exercises': true ,
    unpublished_exercises: false,
    'FROM INITIALIZE': true
  };
  var ck = getcookie('exercisefilter')[0];
  if (ck) {
    var items = unescape(ck).split(';');
    defaultfilter = {};
    for (var item in items) {
      defaultfilter[items[item]] = true;
    }
  }
  store.dispatch(updateExerciseFilter(defaultfilter));
  var ck = getcookie('DisplayStyle');
  if (ck == undefined) {
    var displaystyle = 'horisontal';
  } else if (ck == []) {
    var displaystyle = 'horisontal';
  } else {
    var displaystyle = ck[0];
  }

  var activity_range = getcookie('activity_range');
  if (activity_range == '') {
    activity_range = 'all';
  }

  store.dispatch(updateDisplayStyle(displaystyle));
  store.dispatch(setTimezone(globalInit.timezone));
  store.dispatch(setOpenTAVersion(globalInit.openTAVersion));
  store.dispatch(setActiveCourse(globalInit.coursePk));
  store.dispatch(fetchExercises(globalInit.coursePk));
  store.dispatch(fetchExerciseTree(globalInit.coursePk));
  store.dispatch(fetchCourse(globalInit.coursePk));
  store.dispatch(fetchCourses());
  store.dispatch(setActivityRange(activity_range));

  var iframed = window.self !== window.top;
  store.dispatch(setIFramed(iframed));
  var hash = window.location.hash;
  if (hash.length > 0) {
    var location = hash.substring(1);
    var larray = location.split('/');
    if (larray[0] == 'exercise' && larray.length >= 1) {
      store.dispatch(navigateMenuArray(['activeExercise', 'student']));
      store.dispatch(fetchLoginStatus(globalInit.coursePk)).then(() => store.dispatch(fetchExercise(larray[1], true)));
    }
  }
  if (window.history && history.pushState) {
    // Normalize the current entry, then add a single guard entry
    try {
      history.replaceState({}, '', SUBPATH);
      history.pushState({}, '', SUBPATH);
    } catch (_) {}
  }
  // Some browsers (Safari) fire an initial popstate on load; ignore that one
  let ignoredInitialPop = false;
  window.onpopstate = function (event) {
    if (!ignoredInitialPop && (event == null || event.state == null)) {
      ignoredInitialPop = true;
      return;
    }
    try {
      history.pushState({}, '', SUBPATH);
    } catch (_) {}
    store.dispatch((dispatch, getState) => {
      var state = getState();
      if (state.activeExercise !== '' && menuPositionUnder(state.get('menuPath'), ['activeExercise'])) {
        dispatch(navigateMenuArray([]));
      }
    });
  };

  {
    /* (function checkLogin(){
        const delay = 240000;
        const delayS = Math.round(delay / 1000.0);
        setTimeout(function() {
            jsonfetch('/loggedin/')
                .then(res => {
                    if(res.status >= 300){
                        UIkit.notify('Logged out, please reload page.', {timeout: delay, status: 'danger'});
                    }
                })
                .catch( err => {
                    UIkit.notify('Connection lost, retrying in ' + delayS + 's.', {timeout: delay, status: 'danger'});
                });
            checkLogin();
        }, delay);
    })();
    */
  }

  (function checkLogin() {
    const delay = 240000;
    const delayS = Math.round(delay / 1000.0);
    setTimeout(function () {
      jsonfetch('/health/' + subdomain + '/' + username)
        .then((res) => {
          if (res.status >= 300) {
            UIkit.notify('Logged out, please reload page.', { timeout: delay, status: 'danger' });
          }
        })
        .catch(() => {
          UIkit.notify('Connection lost, retrying in ' + delayS + 's.', { timeout: delay, status: 'danger' });
        });
      checkLogin();
    }, delay);
  })();

  // ReactDOM.render( <Provider store={store}> <App /> </Provider>, document.querySelector('#app')); // React17 syntax
  ReactDOM.createRoot(document.querySelector('#app')).render(
    <Provider store={store}>
      {' '}
      <App />{' '}
    </Provider>
  ); // React18
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', load, { once: true });
} else {
  load();
}
