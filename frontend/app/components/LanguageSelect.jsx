import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import T from './Translation.jsx';

import {
  updateLanguage
} from '../actions.js';

const BaseLanguageSelect = ({languages, lang, onLanguageChange}) => {
  if(languages == null)
    return (<span/>);
  var langChoices = languages.map(language =>
    <li key={language}>
      <a style={{padding:"0px 5px"}} onClick={() => onLanguageChange(language)}>
        {language}
      </a>
    </li>);
  return <div className="uk-button-dropdown" data-uk-dropdown="{mode:'click'}">
    <button className="uk-button uk-button-mini uk-button-success">
      {lang}
      <i className="uk-margin-small-left uk-icon-caret-down"></i>
    </button>
    <div className="uk-dropdown uk-dropdown-small uk-dropdown-bottom" style={{minWidth:'0'}}>
      <ul className="uk-nav uk-nav-dropdown" style={{padding:'0'}}>
        <li key="header" className="uk-nav-header"><T>Language</T></li>
        {langChoices}
      </ul>
    </div>
  </div>;
}

const mapDispatchToProps = dispatch => {
    return {
        onLanguageChange: (language) => {
            dispatch(updateLanguage(language));
        }
    }
}

const mapStateToProps = (state) => {
    return {
      languages: state.getIn(['course', 'languages']),
      lang: state.get('lang', state.getIn(['course', 'languages', 0])),
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseLanguageSelect);
