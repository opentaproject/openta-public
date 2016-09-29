import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import {uploadImage, fetchExerciseRemoteState} from '../fetchers.js';

const BaseComponent = ({exerciseKey, imageAnswers, uploaded, onUpload, uploadPending, uploadProgress}) => {
  console.dir(imageAnswers.toJS())
  var renderImageAnswers = imageAnswers.map(
    imageAnswerId => (<img src={"/imageanswerthumb/" + imageAnswerId}/>) );
  var progress = ( 
        <div className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove" style={{width: "100px"}}>
          <div className="uk-progress-bar" style={{width: (uploadProgress*100) + "%"}}></div>
        </div>);
        return (
    <div className="uk-button-group uk-align-medium-right"> 
        { renderImageAnswers }
        <div className="uk-form-file">
        <a type="file" className={"uk-button uk-button-small"}>{uploadPending ? (<i className="uk-icon-cog uk-icon-spin"></i>) : (<i className="uk-icon-camera"></i>)}
        { uploadPending && progress }
        </a>
        <input type="file" accept="image/*" onChange={(e) => onUpload(e, exerciseKey)}/>
        </div>
    </div>);
};

const handleUpload = (dispatch, event, exerciseKey) => {
  var file = event.target.files[0];
  dispatch(uploadImage(exerciseKey, file));
}

const mapStateToProps = state => {
  var key = state.get('activeExercise');
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return {
    uploaded: [],
    uploadPending: state.getIn(['pendingState', 'exercises', key, 'imageuploadpending']),
    uploadProgress: state.getIn(['pendingState', 'exercises', key, 'imageupload']),
    exerciseKey: key,
    imageAnswers: activeExerciseState.get('image_answers')
  };
}

const mapDispatchToProps = dispatch => {
  return {
    onUpload: (event, exerciseKey) => handleUpload(dispatch, event, exerciseKey)
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseComponent)
