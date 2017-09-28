import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import translationDict from '../translations.js';

const BaseTranslation = ({children, dict, language}) => {
  var languageVersions = {}
  if(translationDict.has(children)) {
    languageVersions = translationDict.get(children);
  }
  if(dict !== undefined)
    languageVersions = dict;
  if(languageVersions.has(language)) {
    return <span>{languageVersions.get(language)}</span>;
  } else {
    return <span>{children}</span>;
  }
}

BaseTranslation.defaultProps = {
  dict: undefined
};

const mapStateToProps = (state) => {
  const defaultLanguage = state.getIn(['login', 'language'], 'en')
    return {
      language: state.get('lang', defaultLanguage)
    };
}

export default connect(mapStateToProps)(BaseTranslation);
