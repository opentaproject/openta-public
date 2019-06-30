import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import T from './Translation.jsx';
import Cookies from 'universal-cookie';

import {
  updateLanguage
} from '../actions.js';

const BaseLanguageSelect = ({languages, lang, onLanguageChange}) => {
  if(languages == null || languages.size < 2 )
    return (<span/>);
  var langChoices = languages.map(language =>
    <li className="uk-text-center" key={language}>
      <a className="uk-dropdown-close" style={{padding:"0px 5px"}} onClick={() => onLanguageChange(language)}>
        <span className={language == lang ? 'uk-text-bold' : ''}>{language}</span>
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
            var cookies = new Cookies()
            cookies.set('lang',language,{path : '/'} )
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
