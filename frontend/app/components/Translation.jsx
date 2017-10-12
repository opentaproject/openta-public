import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import t from '../translations.js';
import immutable from 'immutable';

const BaseTranslation = ({children, dict, language}) => {
 return <span>{t(children, dict, language)}</span>;
}

BaseTranslation.defaultProps = {
  dict: undefined
};

const mapStateToProps = (state) => {
  const defaultLanguage = state.getIn(['course', 'languages', 0], 'en')
    return {
      language: state.get('lang', defaultLanguage)
    };
}

export default connect(mapStateToProps)(BaseTranslation);
