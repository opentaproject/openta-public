import immutable from 'immutable';
import {store} from 'store.js';

const translationDict = immutable.fromJS({
    'Reviewed': {
        'en': 'Audited',
        'sv': 'Granskad'
    },
    'unchecked': {
        'en': 'not graded',
        'sv': 'ej rättad'
    },
    ' STOP GUESSING!': {
        'en': ' STOP GUESSING!',
        'sv': ' SLUTA GISSA!'
    },
    'CORRECT FIRST TIME!': {
        'en': 'CORRECT ON THE FIRST ATTEMPT!',
        'sv': 'KORREKT PÅ FÖRSTA FÖRSÖKET!'
    },
    'Language': {
        'en': 'Language',
        'sv': 'Språk'
    },
    'NUMERICAL': {
        'en': 'NUMERICAL',
        'sv': 'NUMERISK'
    },
    'attempts': {
        'en': 'attempts',
        'sv': 'försök'
    },
    'previous': {
        'en': 'previous',
        'sv': 'föregående'
    },

    'in terms of': {
        'en': 'in terms of',
        'sv': 'i termer av'
    },
    'Exercise name': {
        'en': 'Exercise name',
        'sv': 'Uppgiftsnamn'
    },
    ' is correct.': {
        'en': ' is correct.',
        'sv': ' är korrekt.'
    },
    ' is not correct.': {
        'en': ' is incorrect.',
        'sv': ' är inte korrekt.'
    },
    'Unpublished': {
        'en': 'Unpublished',
        'sv': 'Opublicerad'
    }
});

/**
 * Translates a string using global translationDict or the provided optional dict. If language is not specified it is read for the redux store.
 * @param {string} string String to be translated.
 * @param {immutable.Map} dict Override global translations.
 * @param {string} language Override store language.
 * @return {string} Translated string.
 */
function t(string, dict=undefined, language=undefined) {
    if(language === undefined) {
        const state = store.getState();
        language = state.get('lang', state.getIn(['course', 'languages', 0], 'en'));
    }
    var languageVersions = immutable.Map({});
    if(translationDict.has(string)) {
        languageVersions = translationDict.get(string);
    }
    if(dict !== undefined && Object.keys(dict).length !== 0){
        languageVersions = dict;
    }
    if(languageVersions.has(language)) {
        string = languageVersions.get(language);
    }
    return string;
}

export default t;
