import {logImmutable} from 'immutablehelpers.js';
import _ from 'lodash';
import immutable from 'immutable';
import {jsonfetch, CSRF_TOKEN} from '../fetch_backend.js';
import {SUBPATH} from '../settings.js';
import {
    updateTranslations,
    updateExerciseXML,
} from '../actions.js'
import {
    fetchExerciseXML,
    handleMessages,
    } from '../fetchers.js'

function translateExercise(exercise,language,action) { // USE saveExercise below as model to only translate working copy
    // console.log("FETCHERS: translateExercise: ",  exercise ,language,action)
    var lang =  language
    return (dispatch, getState ) => {
            var state = getState();
            var xml = state.getIn(['exerciseState', exercise, 'activeXML']);
            var payload = {
                exercise: exercise,
                xml: xml,
                language: lang
            };
            var data = JSON.stringify(payload);
            var fetchconfig = {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: data
            };
            return jsonfetch('/exercise/' + exercise + '/' + action + '/' + lang , fetchconfig)
                .then( res => res.json() )
                .then( json => handleMessages(json) )
                .then( () => dispatch(updateExerciseXML(exercise, "")) )
                .then( () => dispatch(fetchExerciseXML(exercise)) )
        };
}

function updateTranslationDict(coursePk) {//{{{ // FILL IN ALL MISSING COURSE LANGUAGES
   // console.log("FETCHERS: updatetranslationdict")
   return dispatch => {
    return  jsonfetch('/course/' + coursePk + '/updatetranslationdict/')
      // .then(response => response.json())
      // .then( json => dispatch(updateTranslations( json,coursePk )))
      .catch( err => console.log(err) );
     }
 }


function fetchTranslationDict(coursePk) {//{{{
   // console.log("FETCHERS: fetchtranslationdict")
   return dispatch => {
    return  jsonfetch('/course/' + coursePk + '/translationdict/')
      .then(response => response.json())
      .then( json => dispatch(updateTranslations( json,coursePk)))
      .catch( err => console.log(err) );
     }
 }



function notifyMissingString(string_,course_pk, language) {//{{{
  // console.log("notifyMissingString", string_, language)
  var payload = {
        string_: string_,
        language: language
            };
  var data = JSON.stringify(payload);
  var fetchconfig = {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: data
    };
   return dispatch => {
    return  jsonfetch('/course/' + course_pk + '/notifymissingstring/' + language,fetchconfig)
      .then(response => response.json())
      //.then( json => dispatch(updateTranslations( json)))
      .catch( err => console.log(err) );
     }
 }


export {translateExercise,
  notifyMissingString,
  fetchTranslationDict,
  updateTranslationDict, } ;

