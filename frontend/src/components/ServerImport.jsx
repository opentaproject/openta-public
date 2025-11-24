// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import { SUBPATH } from '../settings.js';
import { uploadServer } from '../fetchers.js';

class BaseServerImport extends Component {
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
          <button className={'uk-button UploadCourseZipButton'}>
            <i className="uk-icon-file-zip-o" title="file" /> Upload zip
          </button>
          <input id="upl" className="UploadCourseZip" type="file" onChange={(e) => this.props.onUpload(e)} />
        </div>
      </span>
    );
  };

  render() {
    var classDispatch = {
      error: 'uk-text-danger',
      info: 'uk-text-primary',
      warning: 'uk-text-warning',
      success: 'uk-text-success'
    };

    if ( this.props.username != 'super' ) {
    return( <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box"> Only the server website admin can import a  course </div>)
    }

    if (this.props.processStatus.includes('Done')) {
      return (
        <div className="uk-flex uk-flex-wrap uk-margin-top uk-margin-left">
          <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
            {/* <div uk-alert="true">  */}
            <a className="uk-alert-close" href={SUBPATH + '/logout/' + this.props.course_name + '/'}>
              {' '}
              <h3> Success: you must now logout {SUBPATH}</h3>{' '}
            </a>
            {/* </div> */}
          </div>
        </div>
      );
    }
    return (
      <div className="uk-flex uk-flex-wrap uk-margin-top">
        <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
          <div className="uk-text uk-align-middle">
            Upload a zip file with server content. <p />
            <em>
              {' '}
              Note that the old server will be overwritten. <p />
              Make sure you export the course first and save the old zip file <p />
              before proceeding
            </em>
          </div>
          <div className={this.props.processStatus}>{this.renderUpload()}</div>
          {this.props.pendingUpload && this.renderProgress()}
          {this.props.processStatus}
        </div>
      </div>
    );
  }
}

const handleUpload = (event) => (dispatch) => {
  var file = event.target.files[0];
  dispatch(uploadServer(file));
};

const mapDispatchToProps = (dispatch) => {
  return {
    onUpload: (event) => dispatch(handleUpload(event))
  };
};

const mapStateToProps = (state) => {
  var activeCourse = state.get('activeCourse');
  var pendingState = state.getIn(['pendingState', 'server'], immutable.Map({}));
  return {
    activeCourse: activeCourse,
    pendingState: pendingState,
    pendingUpload: pendingState.getIn(['uploadPending']),
    uploadProgress: pendingState.getIn(['uploadProgress']),
    processStatus: pendingState.getIn(['processStatus'], ''),
    course_name: state.getIn(['course', 'course_name']),
    username: state.getIn(['login', 'username'])
	  
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseServerImport);
