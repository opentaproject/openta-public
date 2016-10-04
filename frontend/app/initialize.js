import 'whatwg-fetch';
import 'babel-polyfill';
import ReactDOM from 'react-dom';
import React from 'react';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware, compose } from 'redux';
import thunk from 'redux-thunk';
import counterApp from './reducers';
import App from 'components/App';
import { fetchExercises,fetchExerciseTree, fetchLoginStatus, updatePendingStateIn } from './fetchers';

//const store = createStore(counterApp, module.hot && module.hot.data && module.hot.data.counter || { exercises: ['test'] });
//const store = createStore(counterApp, applyMiddleware(thunk));
const store = createStore(counterApp, compose(applyMiddleware(thunk), window.devToolsExtension ? window.devToolsExtension() : f => f));
store.dispatch( fetchExercises() );
store.dispatch( fetchExerciseTree() );
store.dispatch( fetchLoginStatus() );
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
  ReactDOM.render(
    <Provider store={store}>
      <App />
    </Provider>,
    document.querySelector('#app')
  );
};

if (document.readyState !== 'complete') {
  document.addEventListener('DOMContentLoaded', load);
} else {
  load();
}
