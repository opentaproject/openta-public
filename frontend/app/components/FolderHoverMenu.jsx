import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import {navigateMenuArray} from '../menu.js';

import {
  fetchRenameFolder,
  fetchExerciseTree
} from '../fetchers.js';

import {
  updatePendingStateIn,
  updateExerciseTreeUI
} from '../actions.js';

class BaseFolderHoverMenu extends Component {
  constructor() {
    super();
    this.state = { 
      folderName: ''
    }
  }

  onRenameClick = () => {
    this.setState({folderName: this.props.folderPath.last()})
  }

  onFolderChange = (e) => {
    this.setState({ folderName: e.target.value });
  }

  onFolderKeyPress = (e) => {
    if(e.key == 'Enter'){
      e.preventDefault();
      var id = this.props.folderPath.join('/').replace(/\W/g,'_');
      UIkit.modal("#rename-folder-modal" + id).hide();
      this.props.onFolderRename(this.props.folderPath, e.target.value);
    }
  }

  render() {
    var id = this.props.folderPath.join('/').replace(/\W/g,'_');
    if(!this.props.author)
      return (<span/>);
    return (
      <span>
        <a href={"#rename-folder-modal" + id} data-uk-modal onClick={this.onRenameClick}>
          <i className="uk-icon uk-icon-edit uk-margin-small-right"/>Rename
        </a>
        <div id={"rename-folder-modal" + id} className="uk-modal">
          <div className="uk-modal-dialog" style={{width: '300px'}}>
            <a className="uk-modal-close uk-close"></a>
            <div className="uk-flex uk-flex-column uk-flex-center">
              <div>Rename {this.props.folderPath.last()}</div>
            <input className="uk-form-small uk-text-small" type="text" onChange={this.onFolderChange} onKeyPress={this.onFolderKeyPress} value={this.state.folderName}/>
            </div>
          </div>
        </div>
      </span>
    );
  }
}

const mapDispatchToProps = dispatch => {
  return {
    onFolderRename: (path, newName) => {
      var fullPath = path.push('$pending$')
      var updated = immutable.Map({}).setIn(fullPath, true)
      dispatch(updateExerciseTreeUI(updated))
      dispatch(fetchRenameFolder(path, newName))
                             .then(() => dispatch(fetchExerciseTree()))
                             .then( () => {
                               var updated = immutable.Map({}).setIn(fullPath, false);
                               return dispatch(updateExerciseTreeUI(updated));
                             })
                             .catch( err => {
                               console.dir(err);
                               var updated = immutable.Map({}).setIn(fullPath, null);
                               return dispatch(updateExerciseTreeUI(updated));
                             })
    }
  }
}

const mapStateToProps = (state, ownProps) => {
  const exerciseKey = ownProps.exerciseKey;
  return {
    exerciseTree: state.getIn(['exerciseTree']),
    author: state.getIn(['login', 'groups'],immutable.List([])).includes('Author')
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseFolderHoverMenu);
