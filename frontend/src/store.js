// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import { createStore, applyMiddleware } from 'redux';
import thunk from 'redux-thunk';
import reducer from './reducers';
import { use_devtools, enhancer } from './settings';

//jconst store = createStore(reducer, compose(applyMiddleware(thunk), window.devToolsExtension ? window.devToolsExtension() : f => f));
// const store = createStore(reducer, compose(applyMiddleware(thunk), window.__REDUX_DEVTOOLS_EXTENSION ? window.__REDUX_DEVTOOLS_EXTENSION() : f => f));
// console.log("devtools = ", use_devtools)
if (use_devtools) {
  var store = createStore(reducer /* preloadedState, */, enhancer);
} else {
  var store = createStore(reducer, applyMiddleware(thunk));
}

// Persist exerciseTreeUI to localStorage when it changes
try {
  let prev = store.getState().get('exerciseTreeUI');
  store.subscribe(() => {
    const next = store.getState().get('exerciseTreeUI');
    if (next !== prev) {
      prev = next;
      try {
        const plain = next ? next.toJS() : {};
        localStorage.setItem('exerciseTreeUI', JSON.stringify(plain));
      } catch (_) {
        /* ignore */
      }
    }
  });
} catch (_) {
  // ignore environments without localStorage
}

export { store };
