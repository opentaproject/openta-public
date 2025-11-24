// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import { trash_folder } from '../settings.js';

import { fetchMoveExercise, fetchExerciseTree, fetchExerciseHandle } from '../fetchers.js';

import { updatePendingStateIn } from '../actions.js';

class BaseExerciseHoverMenu extends Component {
  constructor() {
    super();
    this.state = {};
  }

  handleMove = () => {};

  onCustomFolderKeyPress = (e) => {
    if (e.key == 'Enter') {
      e.preventDefault();
      UIkit.modal('#move-modal' + this.props.exerciseKey).hide();
      this.props.onExerciseMove([this.props.exerciseKey], e.target.value, this.props.coursePk);
    }
  };

  renderFolder = (exercise, folderName, content, coursePk) => {
    var subfolders = [];
    if (content.has('folders')) {
      subfolders = content
        .getIn(['folders'], immutable.Map({}))
        .keySeq()
        .sort()
        .map((name) => this.renderFolder(exercise, name, content.getIn(['folders', name, 'content']), coursePk))
        .toList();
    }

    var folderPrename = folderName.split('.')[0].split(':');
    var folderNameRender = folderPrename[folderPrename.length - 1];
    return (
      <li key={folderName}>
        <a
          onClick={() => {
            UIkit.modal('#move-modal' + this.props.exerciseKey).hide();
            this.props.onExerciseMove([exercise], content.get('path').join('/'), coursePk);
          }}
          className="uk-modal-close"
        >
          {folderNameRender}
        </a>
        <ul className="uk-list">{subfolders}</ul>
      </li>
    );
  };

  render() {
    const onExerciseMove = this.props.onExerciseMove;
    const pendingExerciseMove = this.props.pendingExerciseMove;
    const exercise = this.props.exerciseKey;
    const allFolders = this.renderFolder(exercise, '/', this.props.exerciseTree, this.props.coursePk);
    const createtrash =
      this.props.exerciseTree
        .getIn(['folders'], immutable.List([]))
        .keySeq()
        .filter((item) => trash_folder == item)
        .toList().size == 0;
    const trash_folder_name = trash_folder.split(':').pop();
    var trashdom = createtrash ? (
      <ul>
        {' '}
        <li key={trash_folder}>
          {' '}
          <a
            title={'ztrash'}
            onClick={(e) =>
              this.props.onExerciseMove(
                this.props.selected ? this.props.selectedExercises : [this.props.exerciseKey],
                trash_folder,
                this.props.coursePk
              )
            }
          >
            {' '}
            {trash_folder_name}{' '}
          </a>{' '}
        </li>{' '}
      </ul>
    ) : (
      ''
    );
    if (!this.props.author) {
      return <span />;
    }
    return (
      <span>
        <a href={'#move-modal' + exercise} data-uk-modal>
          <i className="uk-icon uk-icon-arrows uk-margin-small-right" />
          Move
        </a>
        <div id={'move-modal' + exercise} className="uk-modal">
          <div className="uk-modal-dialog" style={{ width: '300px' }}>
            <a className="uk-modal-close uk-close" />
            <div className="uk-flex uk-flex-column uk-flex-center">
              <ul>
                <li>
                  {' '}
                  <a
                    onClick={() => {
                      this.props.onExerciseClone(exercise, 'dummypath', this.props.coursePk);
                    }}
                  >
                    {' '}
                    Clone{' '}
                  </a>{' '}
                </li>
                <li>
                  {' '}
                  Move <span className="uk-text uk-text-warning"> {this.props.exercisename} </span> to folder:
                  <ul className="uk-list">
                    {allFolders}
                    {trashdom}
                  </ul>
                  <input className="uk-form-small" type="text" onKeyPress={this.onCustomFolderKeyPress} />
                </li>
              </ul>
            </div>
          </div>
        </div>
      </span>
    );
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    onExerciseMove: (exercises, path, coursePk) => {
      dispatch(updatePendingStateIn(['course', 'move'], true));
      dispatch(fetchMoveExercise(exercises, path))
        .then(() => dispatch(fetchExerciseTree(coursePk)))
        .then(() => dispatch(updatePendingStateIn(['course', 'move'], false)))
        .catch((err) => {
          console.dir(err);
          dispatch(updatePendingStateIn(['course', 'move'], null));
        });
    },
    onExerciseClone: (exercise, path, coursePk) => {
      dispatch(updatePendingStateIn(['course', 'move'], true));
      dispatch(fetchExerciseHandle([exercise], path, 'clone'))
        .then(() => dispatch(fetchExerciseTree(coursePk)))
        .then(() => dispatch(updatePendingStateIn(['course', 'move'], false)))
        .catch((err) => {
          console.dir(err);
          dispatch(updatePendingStateIn(['course', 'move'], null));
        });
    }
  };
};

const mapStateToProps = (state, ownProps) => {
  const exerciseKey = ownProps.exerciseKey;
  return {
    exerciseTree: state.getIn(['exerciseTree']),
    pendingExerciseMove: state.getIn(['pendingState', 'course', 'addExercise']),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    coursePk: state.get('activeCourse'),
    selectedExercises: state.getIn(['selectedExercises'], []),
    selected: state.getIn(['selectedExercises'], null) == null ? false : state.getIn(['selectedExercises']).length > 0
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseHoverMenu);
