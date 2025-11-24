import immutable from 'immutable';
import { notifyMissingString } from './fetchers/fetch_translations.js';
import { getkey } from './getkey.js';
import { store } from './store';

/**
 * Translates a string using global translationDict or the provided optional dict. If language is not specified it is read for the redux store.
 * @param {string} string String to be translated.
 * @param {immutable.Map} dict Override global translations.
 * @param {string} language Override store language.
 * @return {string} Translated string.
 */
//function getkey(string ){
//    var altkey = string.replace(/\s+/g,'')
//    var ret =  md5(altkey).substring(0,5)
//    //console.log(string, ret )
//    return ret
//    }

const t = (string, dict = undefined) => {
  if (string == '') {
    return '';
  }
  const state = store.getState();
  var activeCourse = state.getIn(['activeCourse']);
  var use_auto_translation = state.getIn(['courses', activeCourse, 'use_auto_translation']);
  if (!use_auto_translation) {
    return string;
  }
  var stringin = string;
  var stringout = string;
  var languages = state.getIn(['course', 'languages'], null);
  var admin = state.getIn(['login', 'groups'], immutable.List([])).includes('Admin');
  if (languages == undefined || languages == null) {
    return string;
  }
  if (languages.size == undefined || languages.size < 1) {
    return string;
  }
  var language = state.get('lang');
  //console.log("LANGUAGE = ", language)
  var lang = language;
  var altkey = getkey(stringin); // md5( stringin.replace(/\s+/g,'') ).substring(0,5) // THIS MUST MATHC TRANSLATIONS

  //console.log("KEY = ", key  )
  //console.log("USE_AUTO_TRANSLATE", use_auto_translation)
  var translationDict = state.getIn(['translations']); // THIS SHOULD BE REDUNDANT: comes in via python API
  var stringout = state.getIn(['translations', altkey, lang], false);
  var go1 = !state.getIn(['pendingState', 'course', 'loadingExercises']);
  var go2 = !state.getIn(['pendingState', 'course', 'loadingExerciseTree']);
  // console.log("GO1 = ", go1, "GO2 = ", go2 , "translationDict", translationDict.toJS()  , "stringout", stringout )
  if (stringout == false && go1 && go2 && translationDict) {
    stringout = stringin;
    if (!state.getIn(['translations', altkey], false) ) {
      var course = state.get('activeCourse');
      //console.log("translations: ", go1 , go2, language, altkey , stringin )
      store.dispatch(notifyMissingString(stringin, altkey, course, language));
    }
  }
  return stringout;
};

export default t;
