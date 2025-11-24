import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import slugify from 'slugify';

import { fetchExerciseTree } from '../fetchers.js';

import { fetchFolderRename } from '../fetchers/folder.js';

import { updatePendingStateIn } from '../actions.js';

class BaseFolderHoverMenu extends Component {
  constructor() {
    super();
    this.state = {};
  }

  handleMoveExercisesHere = (e) => {
    console.log('handleMoveExercisesHere', e);
  };

  onCustomFolderKeyPress = (e) => {
    console.log('onCustomFolderKeyPress selected = ', this.props.selected);
    var folder_key = slugify(this.props.folderPath.join('-').split(':').join('-'));
    var rel = JSON.parse(JSON.stringify(this.props.folderPath)).pop();
    if (e.key == 'Enter') {
      e.preventDefault();
      var new_path = e.target.value.toString();
      console.log('new_path = ', new_path);
      if (new_path.charAt(0) == '/') {
        console.log('STRIP FIST CHAR');
        var new_path = new_path.substr(1);
      } else {
        console.log('SO DEAL WITH RELATIVE PATH ', new_path);
        if (new_path.charAt(new_path.length - 1) == '.') {
          console.log('new_path ends with .');
          console.log('REL = ', rel);
          new_path = new_path + '/' + rel;
        }
        var base = JSON.parse(JSON.stringify(this.props.folderPath));
        console.log('BASE ', base);
        var new_path = '/' + base.join('/') + '/../' + new_path;
        console.log('AND NEWPATH ', new_path);
      }
      console.log('new_path = ', new_path);
      UIkit.modal('#move-modal-ABC' + folder_key).hide();
      this.props.onFolderRename(this.props.folderPath, new_path, this.props.coursePk);
    }
  };

  renderFolder = (folderPath, folderName, content, coursePk) => {
    var subfolders = [];
    if (content.has('folders')) {
      subfolders = content
        .getIn(['folders'], immutable.Map({}))
        .keySeq()
        .sort()
        .map((name) => this.renderFolder(folderPath, name, content.getIn(['folders', name, 'content']), coursePk))
        .toList();
    }

    var folderPrename = folderName.split('.')[0].split(':');
    var folderNameRender = folderPrename[folderPrename.length - 1];
    var folder_key = slugify(this.props.folderPath.join('-').split(':').join('-'));
    console.log('renderFolder');
    return (
      <li key={folderName}>
        <a
          onClick={() => {
            UIkit.modal('#move-modal-ABC' + folder_key).hide();
            this.props.onFolderRename(folderPath, content.get('path').join('/'), coursePk);
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
  };

  render() {
    const onFolderRename = this.props.onFolderRename;
    const pendingFolderRename = this.props.pendingFolderRename;
    const folderPath = this.props.folderPath;
    const allFolders = this.renderFolder(folderPath, '/', this.props.exerciseTree, this.props.coursePk);
    console.log("ALL_FOLDERS = ", allFolders)
    var folder_key = slugify(this.props.folderPath.join('-').split(':').join('-'));
    if (!this.props.author) {
      return <span />;
    }
    var instruction = this.props.selected ? 'Exerices Selected' : ' No exercise Selected';
    console.log('renderFolderHoverMenu instruction = ', instruction);

    return (
      <span key={folder_key + 'hover'}>
        <a href={'#move-modal-ABC' + folder_key} data-uk-modal>
          <i className="uk-icon uk-icon-arrows uk-margin-small-right" />
          {instruction}
        </a>
        <div id={'move-modal-ABC' + folder_key} className="uk-modal">
          <div className="uk-modal-dialog" style={{ width: '300px' }}>
            <a className="uk-modal-close uk-close" />
            <div className="uk-flex uk-flex-column uk-flex-center">
              <ul className="uk-list">{allFolders}</ul>
              <input className="uk-form-small" type="text" onKeyPress={this.onCustomFolderKeyPress} />
            </div>
          </div>
        </div>
      </span>
    );
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    onFolderRename: (folderPath, path, coursePk) => {
      dispatch(updatePendingStateIn(['course', 'move'], true));
      console.log('folderPath', folderPath.join('/'), ' path ', path);
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
      console.log('last = ', last);
      console.log('RENAME ', folderPath.join('/'), ' TO ', new_path);
      dispatch(fetchFolderRename(folderPath, new_path))
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
  const folderPath = ownProps.folderPath;
  return {
    selected: state.getIn(['selectedExercises']) == undefined ? false : state.getIn(['selectedExercises']).length > 0,
    exerciseTree: state.getIn(['exerciseTree']),
    pendingFolderRename: state.getIn(['pendingState', 'course', 'addFolder']),
    author: state.getIn(['login', 'groups'], immutable.List([])).includes('Author'),
    coursePk: state.get('activeCourse')
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseFolderHoverMenu);
