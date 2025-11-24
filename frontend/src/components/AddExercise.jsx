// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import { updatePendingStateIn, fetchAddExercise, fetchExerciseTree } from '../fetchers.js';

class BaseAddExercise extends Component {
  constructor() {
    super();
    this.state = {
      name: ''
    };
  }
  handleNameChange = (e) => {
    this.setState({ name: e.target.value });
  };

  handleAdd = () => {
    if (this.state.name.trim() !== '') {
      this.props.onExerciseAdd(this.props.path, this.state.name, this.props.coursePk);
    }
  };
  handleKeypress = (e) => {
    if (e.key == 'Enter') {
      this.handleAdd();
    }
  };

  render() {
    const onExerciseAdd = this.props.onExerciseAdd;
    const pendingExerciseAdd = this.props.pendingExerciseAdd;
    const path = this.props.path;

    if (!this.props.author) {
      return <span />;
    }
    return (
      <li key="addExercise" className="course-exercise-item">
        {!pendingExerciseAdd && (
          <div className="uk-thumbnail exercise-unpublished">
            <div className="uk-placeholder uk-margin-remove uk-padding-remove">
              <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-small-left uk-margin-small-right uk-margin-small-bottom uk-margin-small-top">
                <div>
                  <a className={'exercise-a uk-margin-small-right'} onClick={(ev) => this.handleAdd()}>
                    <i className="uk-icon uk-icon-plus uk-icon-medium" />
                  </a>
                </div>
                <div>
                  <input
                    type="text"
                    placeholder={'Exercise name'}
                    className="uk-form-small uk-form-width-small"
                    style={{ height: 'auto', width: '80px' }}
                    value={this.state.name}
                    onChange={this.handleNameChange}
                    onKeyPress={this.handleKeypress}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
        {pendingExerciseAdd && <Spinner />}
        {pendingExerciseAdd === null && <i className="uk-icon uk-icon-exclamation-triangle" />}
      </li>
    );
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    onExerciseAdd: (path, name, coursePk) => {
      dispatch(updatePendingStateIn(['course', 'addExercise'], true));
      dispatch(fetchAddExercise(path, name, coursePk))
        .then(() => dispatch(fetchExerciseTree(coursePk)))
        .then(() => dispatch(updatePendingStateIn(['course', 'addExercise'], false)))
        .catch((err) => {
          console.dir(err);
          dispatch(updatePendingStateIn(['course', 'addExercise'], null));
        });
    }
  };
};

const mapStateToProps = (state) => {
  return {
    pendingExerciseAdd: state.getIn(['pendingState', 'course', 'addExercise']),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    lang: state.get('lang'),
    coursePk: state.get('activeCourse')
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseAddExercise);
