import 'whatwg-fetch';
import 'babel-polyfill';
import ReactDOM from 'react-dom';
import React from 'react';
import { Provider } from 'react-redux';
import App from 'components/App';
import CookiesNotEnabled from 'components/CookiesNotEnabled';
import {getcookie} from 'cookies.js'
import {
    fetchExercises,
    fetchExerciseTree,
    fetchLoginStatus,
    updatePendingStateIn,
    fetchExercise,
    fetchCourse,
    fetchCourses,
} from './fetchers';
import {
    updateLanguage,
    setTimezone,
    setIFramed,
    setOpenTAVersion,
    } from './actions.js'
import {
  updateActiveExercise,
  setActiveCourse,
  updateExerciseFilter,
  updateDisplayStyle,
} from './actions.js';
import { navigateMenuArray, menuPositionUnder } from './menu.js';
import { SUBPATH ,help_url } from './settings.js';
import {jsonfetch, CSRF_TOKEN} from './fetch_backend.js';
import {store} from 'store.js';


if( getcookie('lang') !== undefined ){
    if( getcookie('lang')[0] !== '""'  ){
          var cookielang = getcookie('lang')[0]
          store.dispatch(updateLanguage( cookielang ) )
      }
   }

store.dispatch( setTimezone(globalInit.timezone) );
store.dispatch( setOpenTAVersion(globalInit.openTAVersion) );
store.dispatch( setActiveCourse(globalInit.coursePk) );
store.dispatch( fetchExercises(globalInit.coursePk) );
store.dispatch( fetchExerciseTree(globalInit.coursePk) );
store.dispatch( fetchLoginStatus(globalInit.coursePk) );
store.dispatch( fetchCourse(globalInit.coursePk) );
store.dispatch( fetchCourses() );
store.dispatch(updatePendingStateIn( ['course', 'loadingExercises'], true));







if (module.hot) {
  module.hot.accept('./reducers', () => {
    store.replaceReducer(require('./reducers').default);
  });
  module.hot.accept();

  module.hot.dispose((data) => {
    data.counter = store.getState();
    [].slice.apply(document.querySelector('#app').children).forEach(function(c) { c.remove() });
  });
}

const load = () => {
  var cookiesEnabled = getcookie('cookieTest');
  if (  !(cookiesEnabled !== undefined && cookiesEnabled[0] == 'enabled')) {
    ReactDOM.render( <CookiesNotEnabled help_url={help_url} />, document.querySelector('#app'));
    return;
  }

   var defaultfilter =  {
            'required_exercises' : true, 
            'optional_exercises': true, 
            'bonus_exercises': true, 
            'unpublished_exercises': false,
            }
 if( getcookie('exercisefilter') !== undefined ){
           var ck =   getcookie('exercisefilter') 
           var items =  unescape( ck[0] ).split(';')
           defaultfilter = {}
           for ( var item in items ){
              defaultfilter[ items[item] ] = true
              }
          }
  store.dispatch(updateExerciseFilter(  defaultfilter) );
  store.dispatch( fetchExerciseTree(globalInit.coursePk) );


  var ck = getcookie( 'DisplayStyle')
  if( ck == undefined   ){
      var displaystyle = 'horisontal' 
    } else if(  ck == [] ){
      var displaystyle = 'horisontal' 
      } else { var displaystyle = ck[0] 
      }
  
  store.dispatch(updateDisplayStyle(displaystyle))
  store.dispatch( setTimezone(globalInit.timezone) );
  store.dispatch( setOpenTAVersion(globalInit.openTAVersion) );
  store.dispatch( setActiveCourse(globalInit.coursePk) );
  store.dispatch( fetchExercises(globalInit.coursePk) );
  store.dispatch( fetchExerciseTree(globalInit.coursePk) );
  store.dispatch( fetchLoginStatus(globalInit.coursePk) );
  store.dispatch( fetchCourse(globalInit.coursePk) );
  store.dispatch( fetchCourses() );
  store.dispatch(updatePendingStateIn( ['course', 'loadingExercises'], true));


  var iframed = ( window.self !== window.top )
  store.dispatch(setIFramed(iframed));
  var hash = window.location.hash;
  if(hash.length > 0) {
    var location = hash.substring(1);
    var larray = location.split('/');
    if(larray[0] == 'exercise' && larray.length >= 1) {
      store.dispatch(navigateMenuArray(['activeExercise', 'student']));
      store.dispatch( fetchLoginStatus(globalInit.coursePk) )
        .then(() => store.dispatch(fetchExercise(larray[1], true)));
    }
  }
  if(window.history && history.pushState) {
    history.pushState({}, "", SUBPATH);
    history.pushState({}, "", SUBPATH);
  }
  window.onpopstate = function(event) {
    history.pushState({}, "", SUBPATH);
    store.dispatch( (dispatch, getState) => {
        var state = getState();
        if(state.activeExercise !== "" && menuPositionUnder(state.get('menuPath'), ['activeExercise'])) {
          //dispatch(updateActiveExercise(""));
          dispatch(navigateMenuArray([]));
        }
      }
                  );
  };
    (function checkLogin(){
        const delay = 20000;
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
  ReactDOM.render(
    <Provider store={store}>
      <App/>
    </Provider>,
    document.querySelector('#app')
  );
};

if (document.readyState !== 'complete') {
  document.addEventListener('DOMContentLoaded', load);
} else {
  load();
}
