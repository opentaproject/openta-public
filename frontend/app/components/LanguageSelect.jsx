import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

import {
  updateLanguage
} from '../actions.js';

const BaseLanguageSelect = ({languages}) => {
  if(languages == null)
    return (<span/>);
  var langChoices = languages.map(language => <span key={language}>{language}</span>);
  return <span>{langChoices}</span>;
}

const mapDispatchToProps = dispatch => {
    return {
        onLanguageChange: (langauge) => {
            dispatch(updateLanguage(language));
        }
    }
}

const mapStateToProps = (state) => {
    return {
      languages: state.getIn(['course', 'languages']),
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseLanguageSelect);
