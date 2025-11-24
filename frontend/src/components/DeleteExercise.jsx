// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import { navigateMenuArray } from '../menu.js';

import { fetchDeleteExercise, fetchExerciseTree, fetchExercises } from '../fetchers.js';

import { updatePendingStateIn, updateActiveExercise } from '../actions.js';

const BaseDeleteExercise = ({ onDelete, pendingDelete, exerciseKey, author, coursePk }) => {
  if (!author) {
    return <span />;
  }
  return (
    <span
      className="uk-button uk-button-small uk-button-danger"
      title="Move exercise to trash."
      data-uk-tooltip
      onClick={() => onDelete(exerciseKey, coursePk)}
    >
      <i className="uk-icon uk-icon-trash" />
      {pendingDelete && <Spinner />}
      {pendingDelete === null && <i className="uk-icon uk-icon-exclamation-triangle" />}
    </span>
  );
};

const mapDispatchToProps = (dispatch) => {
  return {
    onDelete: (exerciseKey, coursePk) => {
      dispatch(updatePendingStateIn(['exercise', exerciseKey, 'delete'], true));
      dispatch(fetchDeleteExercise(exerciseKey))
        .then(() => dispatch(fetchExerciseTree(coursePk)))
        .then(() => dispatch(fetchExercises(coursePk)))
        .then(() => dispatch(updatePendingStateIn(['exercise', exerciseKey, 'delete'], false)))
        .then(() => dispatch(updateActiveExercise('')))
        .then(() => dispatch(navigateMenuArray([])))
        .catch((err) => {
          console.dir(err);
          dispatch(updatePendingStateIn(['exercise', exerciseKey, 'delete'], null));
        });
    }
  };
};

const mapStateToProps = (state) => {
  return {
    pendingExerciseAdd: state.getIn(['pendingState', 'course', 'addExercise']),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    exerciseKey: state.get('activeExercise'),
    coursePk: state.get('activeCourse')
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseDeleteExercise);
