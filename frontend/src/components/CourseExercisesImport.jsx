// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import { uploadExercises } from '../fetchers.js';
import Alert from "./Alert.jsx";

class BaseCourseExercisesImport extends Component {
  renderProgress = () => (
    <span className="uk-button">
      <div className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove" style={{ width: '100px' }}>
        <div className="uk-progress-bar" style={{ width: this.props.uploadProgress * 100 + '%' }}></div>
      </div>
    </span>
  );

  renderUpload = () => {
    return (
      <span className="uk-margin-left">
        <div className="uk-form-file">
          <a type="file" className={'uk-button'}>
            <i className="uk-icon-file-zip-o" title="file" /> Upload zip
          </a>
          <input type="file" onChange={(e) => this.props.onUpload(e, this.props.activeCourse)} />
        </div>
      </span>
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
    console.log("PROPS = ", this.props)
    try { 
    var rows = this.props.uploadMessages.map((item, index) => (
      <li className={classDispatch[item.first()]} key={index}>
        {' '}
        {item.last()}
      </li>
    ));
    return (
      <div className="uk-flex uk-flex-wrap uk-margin-top">
        <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
          <div>Upload a zip file with exercises to be imported into this course.</div>
	  <div className="uk-text uk-text-bold uk-text-danger"> DANGER! Existing exercises may be overwritten! </div> 
	<div className="uk-text uk-text-bold uk-text-danger"> Export the existing exercises first so you can restore the exercises</div> 
          <div>{this.renderUpload()}</div>
          {this.props.pendingUpload && this.renderProgress()}
          <ul className="uk-list">{rows}</ul>
        </div>
      </div>
    );
  } catch ( err  )  {
	  var msgs = this.props.uploadMessages;
	  var msg = JSON.stringify( msgs )
	  return ( <div> <Alert type='error' message={msg} /> </div>)

  }
 }
}

const handleUpload = (event, courseKey) => (dispatch) => {
  var file = event.target.files[0];
  dispatch(uploadExercises(courseKey, file));
};

const mapDispatchToProps = (dispatch) => {
  return {
    onUpload: (event, courseKey) => dispatch(handleUpload(event, courseKey))
  };
};

const mapStateToProps = (state) => {
  var activeCourse = state.get('activeCourse');
  var pendingState = state.getIn(['pendingState', 'course', activeCourse], immutable.Map({}));
  return {
    activeCourse: activeCourse,
    pendingState: pendingState,
    pendingUpload: pendingState.getIn(['UploadPending']),
    uploadProgress: pendingState.getIn(['UploadProgress']),
    uploadMessages: immutable.fromJS(pendingState.getIn(['UploadMessages'], []))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseExercisesImport);
