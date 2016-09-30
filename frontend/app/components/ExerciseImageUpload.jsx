import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import {
  uploadImage, 
  fetchExerciseRemoteState,
  updatePendingStateIn,
  deleteImageAnswer,
  fetchImageAnswers
} from '../fetchers.js';

const BaseComponent = ({exerciseKey, imageAnswers, uploaded, onUpload, uploadPending, uploadProgress, onImageAnswerDelete, imageAnswerDeletePending}) => {
  var renderImageAnswers = imageAnswers.map(
    imageAnswerId => (
      <div className="exercise-thumb-wrap">
      <a href={"/imageanswer/" + imageAnswerId} data-uk-lightbox data-lightbox-type="image">
      <img src={"/imageanswerthumb/" + imageAnswerId}/>
      </a>
      <div className="exercise-thumb-badge">
        <a onClick={() => onImageAnswerDelete(imageAnswerId)}><Badge className="uk-badge-notification uk-badge-danger">
        { !imageAnswerDeletePending.get(imageAnswerId, false) && <i className="uk-icon uk-icon-close"/> }
        { imageAnswerDeletePending.get(imageAnswerId, false) && <Spinner/> }
        </Badge></a>
      </div>
      </div>
    )
  );
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

const handleImageAnswerDelete = (imageAnswerId) => 
  (dispatch, getState) => {
    var state = getState();
    var exerciseKey = state.get('activeExercise');
    dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageanswerdelete', imageAnswerId], true));
    dispatch(deleteImageAnswer(imageAnswerId))
      .then( () => { 
          dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageanswerdelete', imageAnswerId], false));
          dispatch(fetchImageAnswers(exerciseKey));
      }
           )
      .catch( err => console.dir(err) )
  }

const mapStateToProps = state => {
  var key = state.get('activeExercise');
  var activeExerciseState = state.getIn(['exerciseState',state.get('activeExercise')], immutable.Map({}));
  return {
    uploaded: [],
    uploadPending: state.getIn(['pendingState', 'exercises', key, 'imageuploadpending']),
    uploadProgress: state.getIn(['pendingState', 'exercises', key, 'imageupload']),
    exerciseKey: key,
    imageAnswers: activeExerciseState.get('image_answers'),
    imageAnswerDeletePending: state.getIn(['pendingState', 'exercises', key, 'imageanswerdelete'], immutable.Map({})),
  };
}

const mapDispatchToProps = dispatch => {
  return {
    onUpload: (event, exerciseKey) => handleUpload(dispatch, event, exerciseKey),
    onImageAnswerDelete: (imageAnswerId) => dispatch(handleImageAnswerDelete(imageAnswerId))
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseComponent)
