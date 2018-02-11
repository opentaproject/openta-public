import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import {navigateMenuArray} from '../menu.js';

import {
  fetchMoveExercise,
  fetchExerciseTree
} from '../fetchers.js';

import {
  updatePendingStateIn,
} from '../actions.js';

class BaseExerciseHoverMenu extends Component {
    constructor() {
        super();
        this.state = {
        }
    }

    handleMove = () => {
    }

    onCustomFolderKeyPress = (e) => {
        if(e.key == 'Enter'){
            e.preventDefault();
            UIkit.modal("#move-modal" + this.props.exerciseKey).hide();
            this.props.onExerciseMove(this.props.exerciseKey, e.target.value);
        }
    }

    renderFolder = (exercise, folderName, content, coursePk) => {
        var subfolders = []
        if (content.has("folders")) {
          subfolders = content
            .getIn(["folders"], immutable.Map({}))
            .keySeq()
            .sort()
            .map(name =>
              this.renderFolder(
                exercise,
                name,
                content.getIn(["folders", name, "content"]),
                coursePk
              )
            )
            .toList();
        }

        var folderPrename = folderName.split('.')[0].split(':');
        var folderNameRender = folderPrename[folderPrename.length - 1]
        return (
            <li key={folderName}>
              <a onClick={() => {
                  UIkit.modal("#move-modal" + this.props.exerciseKey).hide();
                  this.props.onExerciseMove(exercise, content.get('path').join('/'), coursePk);
                }} className="uk-modal-close">
                    {folderNameRender}
                </a>
                <ul className="uk-list">
                    { subfolders }
                </ul>
            </li>
        );
    }

    render() {
        const onExerciseMove = this.props.onExerciseMove;
        const pendingExerciseMove = this.props.pendingExerciseMove;
        const exercise = this.props.exerciseKey;
        const allFolders = this.renderFolder(exercise, "", this.props.exerciseTree, this.props.coursePk);

        if(!this.props.author)
            return (<span/>);
        return <span>
            <a href={"#move-modal" + exercise} data-uk-modal>
              <i className="uk-icon uk-icon-arrows uk-margin-small-right" />Move
            </a>
            <div id={"move-modal" + exercise} className="uk-modal">
              <div className="uk-modal-dialog" style={{ width: "300px" }}>
                <a className="uk-modal-close uk-close" />
                <div className="uk-flex uk-flex-column uk-flex-center">
                  <ul className="uk-list">{allFolders}</ul>
                  <input className="uk-form-small" type="text" onKeyPress={this.onCustomFolderKeyPress} />
                </div>
              </div>
            </div>
          </span>;
    }
}

const mapDispatchToProps = dispatch => {
    return {
        onExerciseMove: (exercise, path, coursePk) => {
            dispatch(updatePendingStateIn(['course', 'move'], true))
            dispatch(fetchMoveExercise(exercise, path))
                .then(() => dispatch(fetchExerciseTree(coursePk)))
                .then( () => dispatch(updatePendingStateIn(['course', 'move'], false)))
                .catch( err => {
                    console.dir(err);
                    dispatch(updatePendingStateIn(['course', 'move'], null))
                })
        }
    }
}

const mapStateToProps = (state, ownProps) => {
    const exerciseKey = ownProps.exerciseKey;
    return {
        exerciseTree: state.getIn(['exerciseTree']),
        pendingExerciseMove: state.getIn(['pendingState', 'course', 'addExercise']),
        author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author'),
        coursePk: state.getIn(['login', 'course_pk'])
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseHoverMenu);
