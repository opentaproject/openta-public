import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import _ from 'lodash';
import {
    updatePendingStateIn,
    uploadExercises,
} from '../fetchers.js';

class BaseCourseImport extends Component {

    renderProgress = () => (
            <span className="uk-button">
                <div className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove" style={{width: "100px"}}>
                    <div className="uk-progress-bar" style={{width: (this.props.uploadProgress*100) + "%"}}></div>
                </div>
            </span>
    )

    renderUpload = () => {
        return (
            <span className="uk-margin-left">
                <div className="uk-form-file">
                    <a type="file" className={"uk-button"}><i className="uk-icon-file-zip-o" title="file"/> Upload zip
                    </a>
                    <input type="file" onChange={(e) => this.props.onUpload(e, this.props.activeCourse)}/>
                </div>
            </span>
        );
    }

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
            success: 'uk-text-success',
        };
        var rows = this.props.uploadMessages.map( (item, index) => (
            <li className={classDispatch[item.first()]} key={index}> {item.last()}</li>
        ));
        return <div className="uk-flex uk-flex-wrap uk-margin-top">
            <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
              <div>
                Upload a zip file with exercises to be imported into this course.
              </div>
              <div>{this.renderUpload()}</div>
              {this.props.pendingUpload && this.renderProgress()}
              <ul className="uk-list">{rows}</ul>
            </div>
          </div>;
    }
}

const handleUpload = (event, courseKey) => dispatch => {
  var file = event.target.files[0];
  dispatch(uploadExercises(courseKey, file));
}

const mapDispatchToProps = dispatch => {
    return {
        onUpload: (event, courseKey) => dispatch(handleUpload(event, courseKey)),
    }
}

const mapStateToProps = state => {
  var activeCourse = state.get("activeCourse");
  var pendingState = state.getIn(["pendingState", "course", activeCourse], immutable.Map({}));
  return {
    activeCourse: activeCourse,
    pendingState: pendingState,
    pendingUpload: pendingState.getIn(["exercisesUploadPending"]),
    uploadProgress: pendingState.getIn(["exercisesUploadProgress"]),
    uploadMessages: immutable.fromJS(pendingState.getIn(["exercisesUploadMessages"], [])),
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseCourseImport);
