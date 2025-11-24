// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import DOMPurify from 'dompurify';
import { connect } from 'react-redux';

import { throttleParseXML } from './AuthorExercise.jsx';

import {
  setSavePendingState,
  setResetPendingState,
  updatePendingStateIn,
  setExerciseModifiedState
} from '../actions.js';

import { fetchSameFolder } from '../fetchers.js';

import { translateExercise } from '../fetchers/fetch_translations.js';

class BaseAutoTranslate extends Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    // const items = this.props.history.sort( (a,b) => b.get('modified') - a.get('modified')).map(this.renderItem);
    const languages = this.props.languages;
    const exercise = this.props.exercise;
    const subdomain = this.props.subdomain;
    const action = this.props.action;
    const titlechoices = {
      translate: ' default => lang ',
      changedefaultlanguage: 'lang => default',
      remove: '<b><del>  lang </del><b>'
    };
    const explanations = {
      translate: ' translate default to lang',
      changedefaultlanguage: 'change lang to default',
      remove: 'REMOVE  lang '
    };
    var title = titlechoices[action];
    var explain = explanations[action];
    var langChoices = languages.map((language) => (
      <tr className="uk-text-center" key={language}>
        <td>
          <a
            className="uk-dropdown-close"
            style={{ padding: '0px 5px' }}
            onClick={() => this.props.onItemClick(exercise, language, subdomain, action)}
          >
            <span className={language == this.props.lang ? 'uk-text-bold' : ''}>{language}</span>
          </a>
        </td>
      </tr>
    ));

    return (
      <div data-uk-dropdown="{mode:'click'}">
        <span className="uk-button uk-button-small " title={explain} data-uk-tooltip>
          <span dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(title) }} />
        </span>
        <div className="uk-dropdown" style={{ width: 'auto' }}>
          {langChoices.size == 0 && <span>Empty</span>}
          <table className="uk-table uk-table-condensed uk-margin-remove uk-table-hover">
            <tbody>{langChoices}</tbody>
          </table>
        </div>
      </div>
    );
  }
}

const handleItemClick = (exercise, language, subdomain, action) => (dispatch) => {
  console.log('CLICKED language = ', language);
  dispatch(setExerciseModifiedState(exercise, true));
  dispatch(setResetPendingState(exercise, true));
  dispatch(updatePendingStateIn(['exercises', exercise, 'loadingJSON'], true));
  dispatch(setSavePendingState(exercise, true));
  throttleParseXML.cancel(); //Cancel possibly queued XML parsing updates
  console.log('NOW DO DISPATCHES');
  return dispatch(translateExercise(exercise, language, action))
    .then(() => dispatch(setResetPendingState(exercise, false)))
    .then(() => dispatch(setExerciseModifiedState(exercise, false)))
    .then(() => dispatch(updatePendingStateIn(['exercises', exercise, 'loadingJSON'], false)))
    .then(() => dispatch(setSavePendingState(exercise, false)))
    .then(() => dispatch(fetchSameFolder(exercise, subdomain)));
};

const mapDispatchToProps = (dispatch) => {
  return {
    onItemClick: (exercise, language, subdomain, action) =>
      dispatch(handleItemClick(exercise, language, subdomain, action))
  };
};

const mapStateToProps = (state) => {
  const activeExercise = state.get('activeExercise');
  const activeCourse = state.get('activeCourse');
  const use_auto_translation = state.getIn(['courses', activeCourse, 'use_auto_translation']);

  return {
    exercise: activeExercise,
    languages: state.getIn(['course', 'languages']),
    lang: state.get('lang', state.getIn(['course', 'languages', 0])),
    subdomain: state.get('subdomain', ''),
    use_auto_translation: use_auto_translation
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseAutoTranslate);
