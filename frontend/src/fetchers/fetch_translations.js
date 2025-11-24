// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import { jsonfetch, sendFrontendLog } from '../fetch_backend.js';
import { updateTranslations, updateExerciseXML } from '../actions.js';
import { fetchExerciseXML, handleMessages } from '../fetchers.js';

// Track which (altkey, language) pairs were notified to avoid duplicates
const notifiedAltkeyLanguage = new Set();

function translateExercise(exercise, language, action) {
  // USE saveExercise below as model to only translate working copy
  // console.log("FETCHERS: translateExercise: ",  exercise ,language,action)
  var lang = language;
  return (dispatch, getState) => {
    var state = getState();
    var xml = state.getIn(['exerciseState', exercise, 'activeXML']);
    var payload = {
      exercise: exercise,
      xml: xml,
      language: lang
    };
    var data = JSON.stringify(payload);
    var fetchconfig = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data
    };
    return jsonfetch('/exercise/' + exercise + '/' + action + '/' + lang, fetchconfig)
      .then((res) => res.json())
      .then((json) => handleMessages(json))
      .then(() => dispatch(updateExerciseXML(exercise, '')))
      .then(() => dispatch(fetchExerciseXML(exercise)))
      .catch((err) => {
        console.dir(err);
        sendFrontendLog('error', 'translateExercise failed', { exercise, language: lang, action, error: String(err) });
      });
  };
}

function fetchTranslationDict(coursePk, language = '') {
  //{{{
  // console.log("FETCHERS: fetchtranslationdict")
  return (dispatch) => {
    return jsonfetch('/course/' + coursePk + '/translationdict/' + language)
      .then((response) => response.json())
      .then((json) => dispatch(updateTranslations(json, coursePk)))
      .catch((err) => {
        console.log(err);
        sendFrontendLog('error', 'fetchTranslationDict failed', { coursePk, language, error: String(err) });
      });
  };
}

function notifyMissingString(string_, altkey, course_pk, language) {
  //{{{
  // Ensure we only notify once per unique (altkey, language)
  const pairKey = `${altkey || ''}::${language || ''}`;
  if (!altkey || notifiedAltkeyLanguage.has(pairKey)) {
    //console.log('OLD PAIRKEY ', pairKey);
    sendFrontendLog('info', 'notifyMissingString skipped', { pairKey, altkey, language });
    return () => Promise.resolve();
  }
  notifiedAltkeyLanguage.add(pairKey);
  //console.log('NEW PAIRKEY ', pairKey);
  sendFrontendLog('info', 'notifyMissingString created', { pairKey, altkey, language });

  var payload = {
    altkey: altkey,
    string_: string_,
    language: language
  };
  var data = JSON.stringify(payload);
  var fetchconfig = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: data
  };
  return (dispatch) => {
    return (
      jsonfetch('/course/' + course_pk + '/notifymissingstring/' + language, fetchconfig)
        .then((response) => response.json())
        //then( json => dispatch(updateTranslations( json)))
        .catch((err) => {
          console.log(err);
          sendFrontendLog('error', 'notifyMissingString failed', { course_pk, altkey, language, error: String(err) });
        })
    );
  };
}

export { translateExercise, notifyMissingString, fetchTranslationDict };
