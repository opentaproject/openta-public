// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { PureComponent } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import { trash_folder } from '../settings.js';

import { fetchExerciseTree } from '../fetchers.js';

import { fetchFolderRename, fetchFolderHandle } from '../fetchers/folder.js';

import { updatePendingStateIn } from '../actions.js';

var unstableKey = 0;
const nextUnstableKey = () => unstableKey++;

function renderFolder(folderPath, folderName, content, coursePk, fcn) {
  var subfolders = [];
  if (content.has('folders')) {
    subfolders = content
      .getIn(['folders'], immutable.Map({}))
      .keySeq()
      .sort()
      .map((name) => renderFolder(folderPath, name, content.getIn(['folders', name, 'content']), coursePk, fcn))
      .toList();
  }

  var folderPrename = folderName.split('.')[0].split(':');
  var folderNameRender = folderPrename[folderPrename.length - 1];
  var folder_key = nextUnstableKey();
  return (
    <li key={folderName}>
      <a
        title={'ABCDEFG'}
        onClick={() => {
          UIkit.modal('#move-modal-ABC' + folder_key).hide();
          fcn(folderPath, content.get('path').join('/'), coursePk);
        }}
        className="uk-modal-close"
      >
        {folderNameRender}
      </a>
      <ul key={folder_key + 'folder_key'} className="uk-list">
        {subfolders}
      </ul>
    </li>
  );
}

class BaseFolderButtonCapture extends PureComponent {
  constructor() {
    super();
    this.state = { count: 0 };
    this.onCustomFolderKeyPress = this.onCustomFolderKeyPress.bind(this);
  }

  //handleChange = (e,exerciseKey) => {
  //   this.setState({'button': e.buttons}) // THIS DOES NOTHING BUT TRIGGER render
  //   console.log("HANDLE CHANGE IN FOLDER BUTTON CAPTURE")
  //   if (  1 == e.buttons ){
  //     return  this.props.children.props.onClick()
  //     }
  //   if ( 2 == e.buttons ){
  //     console.log("RIGHT BUTTON CLICKED")
  //     }
  //   }

  onCustomFolderKeyPress = (e) => {
    //var folder_key = slugify( ( this.props.folderPath.join('-')).split(':').join('-') );
    var folder_key = nextUnstableKey();
    var rel = JSON.parse(JSON.stringify(this.props.folderPath)).pop();
    if (e.key == 'Enter') {
      e.preventDefault();
      var new_path = e.target.value.toString();
      if (new_path.charAt(0) == '/') {
        var new_path = new_path.substr(1);
      } else {
        if (new_path.charAt(new_path.length - 1) == '.') {
          new_path = new_path + '/' + rel;
        }
        var base = JSON.parse(JSON.stringify(this.props.folderPath));
        var new_path = '/' + base.join('/') + '/../' + new_path;
      }
      UIkit.modal('#move-modal-ABC-1' + folder_key).hide();
      this.props.onFolderRename(this.props.folderPath, new_path, this.props.coursePk);
    }
  };

  render() {
    const onFolderRename = this.props.onFolderRename;
    const folderPath = this.props.folderPath;
    const content = this.props.content;
    const allFolders = renderFolder(
      folderPath,
      '/',
      this.props.exerciseTree,
      this.props.coursePk,
      this.props.onFolderRename
    );
    const createtrash =
      this.props.exerciseTree
        .getIn(['folders'], immutable.List([]))
        .keySeq()
        .filter((item) => trash_folder == item)
        .toList().size == 0;
    //var folder_key = slugify( ( this.props.folderPath.join('-')).split(':').join('-') );
    var folder_key = nextUnstableKey();
    if (!this.props.author) {
      return <span />;
    }
    var istrash = 'z:Trash' == folderPath.join('/');
    var coursePk = this.props.coursePk;
    var onEmptyTrash = this.props.onEmptyTrash;

    return (
      <span key={folder_key + 'hover'}>
        <a href={'#move-modal-ABC-2' + folder_key} data-uk-modal>
          {this.props.children}
        </a>
        <div id={'move-modal-ABC-2' + folder_key} className="uk-modal">
          <div className="uk-modal-dialog" style={{ width: '300px' }}>
            <a className="uk-modal-close uk-close" />
            <div className="uk-flex uk-flex-column uk-flex-center">
              {!istrash && (
                <div>
                  <h3>move {'/' + folderPath.join('/')} to </h3>
                  <ul className="uk-list">{allFolders}</ul>
                  <input className="uk-form-small" type="text" onKeyPress={this.onCustomFolderKeyPress} />
                </div>
              )}
              {istrash && (
                <div>
                  {' '}
                  <a
                    id="js-modal-prompt"
                    href="#"
                    className="uk-modal-close"
                    onClick={() => {
                      UIkit.modal.confirm(
                        'Are you sure? This cannot be undone!',
                        function () {
                          console.log('HIT YES', { coursePk });
                          {
                            onEmptyTrash(coursePk);
                          }
                        },
                        function () {
                          console.log('HIT NO ', { coursePk });
                          {
                            return { success: 'did nothing' };
                          }
                        },
                        { labels: { Ok: 'Proceed to delete trash', Cancel: 'Cancel' } }
                      );
                    }}
                  >
                    {' '}
                    <h3> Empty Trash </h3>{' '}
                  </a>{' '}
                </div>
              )}
            </div>
          </div>
        </div>
      </span>
    );
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    onEmptyTrash: (coursePk) => {
      dispatch(fetchFolderHandle('z:Trash', coursePk, 'emptyTrash'))
        .then(() => dispatch(updatePendingStateIn(['course', 'movingFolder'], true)))
        .then(() => dispatch(fetchExerciseTree(coursePk)))
        .then(() => dispatch(updatePendingStateIn(['course', 'movingFolder'], false)))
        .catch((err) => {
          console.dir(err);
          dispatch(updatePendingStateIn(['course', 'error'], null));
        });
    },

    onFolderRename: (folderPath, path, coursePk) => {
      var folderpath = folderPath.join('/');
      var last = [folderpath.split('/').pop()];
      if (last == undefined) {
        last = [''];
      }
      last = last.join('/');
      if (path[0] == '/') {
        last = '';
      }
      var new_path = (path + '/' + last).trimLeft('/');
      dispatch(fetchFolderRename(folderPath, new_path, coursePk))
        .then(() => dispatch(updatePendingStateIn(['course', 'movingFolder'], true)))
        .then(() => dispatch(fetchExerciseTree(coursePk)))
        .then(() => dispatch(updatePendingStateIn(['course', 'movingFolder'], false)))
        .catch((err) => {
          console.dir(err);
          dispatch(updatePendingStateIn(['course', 'error'], null));
        });
    }
  };
};

const mapStateToProps = (state, ownProps) => {
  const folderPath = ownProps.folderPath;
  return {
    selected: state.getIn(['selectedExercises']) == undefined ? false : state.getIn(['selectedExercises']).length > 0,
    exerciseTree: state.getIn(['exerciseTree']),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    coursePk: state.get('activeCourse')
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseFolderButtonCapture);
