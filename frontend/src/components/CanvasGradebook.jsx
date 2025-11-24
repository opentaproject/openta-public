// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Alert from './Alert.jsx';
import { SUBPATH } from '../settings.js';
import { updatePendingStateIn, uploadCanvasGradebook } from '../fetchers.js';

class BaseCanvasGradebook extends Component {
  renderUploadProgress = () => (
    <span className="uk-margin-top">
      Upload progress
      <span className="uk-button uk-margin-left">
        <div
          className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove"
          style={{ width: '100px' }}
        >
          <div className="uk-progress-bar" style={{ width: this.props.uploadProgress * 100 + '%' }}></div>
        </div>
      </span>
    </span>
  );

  renderProcessingProgress = () => (
    <span className="uk-margin-top">
      Processing progress
      <span className="uk-button uk-margin-left">
        <div
          className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove"
          style={{ width: '100px' }}
        >
          <div className="uk-progress-bar" style={{ width: this.props.processingProgress * 100 + '%' }}></div>
        </div>
      </span>
    </span>
  );

  renderUpload = () => {
    return (
      <span className="uk-margin-left uk-margin-top">
        <div className="uk-form-file">
          <a type="file" className={'uk-button'}>
            <i className="uk-icon-file-zip-o" title="file" /> Upload Canvas gradesheet
          </a>
          <input type="file" onChange={(e) => this.props.onUpload(e, this.props.activeCourse)} />
        </div>
      </span>
    );
  };

  renderDownloadResult = (taskId) => {
    return (
      <div>
        <a href={SUBPATH + '/queuetask/' + taskId + '/resultfile'}>Download results</a>
      </div>
    );
  };

  render() {
    /*
     * List of files
     * Ability to delete
     * Ability to preview
     * Upload
     */
    var classDispatch = {
      error: 'uk-text-danger',
      info: 'uk-text-primary',
      warning: 'uk-text-warning',
      success: 'uk-text-success'
    };
    // var rows = this.props.uploadMessages.map( (item, index) => (
    //     <li className={classDispatch[item.first()]} key={index}> {item.last()}</li>
    // ));
    return (
      <div className="uk-flex uk-flex-wrap uk-margin-top">
        <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
          <div>Upload a Canvas gradebook to be amended with OpenTA results</div>
          {this.renderUpload()}
          {/* {this.props.pendingUpload && this.renderUploadProgress()}
              {!this.props.processingDone && this.renderProcessingProgress()} */}
          {this.renderUploadProgress()}
          {this.renderProcessingProgress()}
          {this.props.processingStatus !== '' && <Alert>{this.props.processingStatus}</Alert>}
          {this.props.processingDone &&
            this.props.processingStatus == 'Complete' &&
            this.renderDownloadResult(this.props.processingTaskId)}
          {/* <ul className="uk-list">{rows}</ul> */}
        </div>
      </div>
    );
  }
}

const handleUpload = (event, courseKey) => (dispatch) => {
  var file = event.target.files[0];
  dispatch(uploadCanvasGradebook(courseKey, file));
  dispatch(updatePendingStateIn(['course', courseKey, 'canvasGradebookTask'], null));
};

const mapDispatchToProps = (dispatch) => {
  return {
    onUpload: (event, courseKey) => dispatch(handleUpload(event, courseKey))
  };
};

const mapStateToProps = (state) => {
  var activeCourse = state.get('activeCourse');
  var pendingState = state.getIn(['pendingState', 'course', activeCourse], immutable.Map({}));
  var taskId = pendingState.getIn(['canvasGradebookTask']);
  return {
    activeCourse: activeCourse,
    pendingState: pendingState,
    pendingUpload: pendingState.getIn(['canvasGradebookUploadPending']),
    uploadProgress: pendingState.getIn(['canvasGradebookUploadProgress']),
    processingTaskId: taskId,
    processingProgress: state.getIn(['tasks', taskId, 'progress'], 0.0),
    processingStatus: state.getIn(['tasks', taskId, 'status'], ''),
    processingDone: state.getIn(['tasks', taskId, 'done'], false)
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseCanvasGradebook);
