import React from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import SafeImg from './SafeImg.jsx';
import Badge from './Badge.jsx';
import { uploadImage, updatePendingStateIn, deleteImageAnswer, fetchImageAnswers } from '../fetchers.js';
import { SUBPATH } from '../settings.js';

const BaseComponent = ({
  exerciseKey,
  imageAnswers,
  imageAnswersData,
  uploaded,
  onUpload,
  uploadPending,
  uploadProgress,
  onImageAnswerDelete,
  imageAnswerDeletePending,
  showPDF,
  locked
}) => {
  var renderImageAnswers = imageAnswersData.map((imageAnswer) => (
    <div className="exercise-thumb-wrap" key={imageAnswer.get('pk')}>
      {imageAnswer.get('filetype') === 'IMG' && (
        <a
          href={SUBPATH + '/imageanswer/' + imageAnswer.get('pk')}
          data-uk-lightbox
          data-lightbox-type="image"
          data-uk-tooltip
          title={imageAnswer.get('date').split('.')[0].replace('T', ' ').toString()}
        >
          <SafeImg src={SUBPATH + '/imageanswerthumb/' + imageAnswer.get('pk')}>
            <i className="uk-icon uk-icon-large uk-icon-file-pdf-o" />
          </SafeImg>
        </a>
      )}
      {imageAnswer.get('filetype') === 'PDF' && (
        <a
          href={SUBPATH + '/imageanswer/' + imageAnswer.get('pk')}
          target="_blank"
          data-uk-tooltip
          title={imageAnswer.get('date').split('.')[0].replace('T', ' ').toString()}
          rel="noreferrer"
        >
          <i className="uk-icon uk-icon-large uk-icon-file-pdf-o" />
        </a>
      )}
      {!locked && (
        <div className="exercise-thumb-badge">
          <a onClick={() => onImageAnswerDelete(imageAnswer.get('pk'))}>
            <Badge className="uk-badge-notification">
              {!imageAnswerDeletePending.get(imageAnswer.get('pk'), false) && <i className="uk-icon uk-icon-trash" />}
              {imageAnswerDeletePending.get(imageAnswer.get('pk'), false) && <Spinner />}
            </Badge>
          </a>
        </div>
      )}
    </div>
  ));
  var progress = (
    <div className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove" style={{ width: '100px' }}>
      <div className="uk-progress-bar" style={{ width: uploadProgress * 100 + '%' }}></div>
    </div>
  );
  return (
    <div>
      {renderImageAnswers}
      <div className="uk-button-group uk-align-medium-right">
        {uploadPending && <span className="uk-button">{progress}</span>}
        {!locked && (
          <>
            <div className="uk-form-file">
              <a type="file" className={'uk-button'} capture="camera" title="Take photo with camera">
                {uploadPending ? <i className="uk-icon-cog uk-icon-spin"></i> : <i className="uk-icon-camera"></i>}
              </a>
              <input type="file" accept="image/*" onChange={(e) => onUpload(e, exerciseKey)} capture />
            </div>
            <div className="uk-form-file">
              <a type="file" className={'uk-button'} title="Choose from photos">
                {uploadPending ? (
                  <i className="uk-icon-cog uk-icon-spin"></i>
                ) : (
                  <i className="uk-icon-image" />
                )}
              </a>
              <input type="file" accept="image/*" onChange={(e) => onUpload(e, exerciseKey)} />
            </div>
          </>
        )}
        {!locked && showPDF && (
          <div className="uk-form-file">
            <a type="file" className={'uk-button'}>
              {uploadPending ? (
                <i className="uk-icon-cog uk-icon-spin"></i>
              ) : (
                <i className="uk-icon-file-pdf-o" title="PDF"></i>
              )}
            </a>
            <input type="file" accept="application/pdf" onChange={(e) => onUpload(e, exerciseKey)} />
          </div>
        )}
        <button
          data-uk-tooltip="{pos:'bottom-left'}"
          title="Denna uppgift kräver även bild på lösning. (Om du har en mobil enhet med kamera kan du välja att ta bilderna direkt.) Du kan ladda upp flera bilder samt ta bort de du laddat upp. Kontrollera att bilden är läsbar efter du laddat upp genom att klicka på den/dem."
          className="uk-button"
        >
          <i className="uk-icon uk-icon-question-circle-o" />
        </button>
      </div>
    </div>
  );
};

const handleUpload = (dispatch, event, exerciseKey) => {
  var file = event.target.files[0];
  event.target.value = '';
  // see https://stackoverflow.com/questions/12030686/html-input-file-selection-event-not-firing-upon-selecting-the-same-file
  dispatch(uploadImage(exerciseKey, file)).then((res) => {
    if ('error' in res) {
      UIkit.notify(res.error, { timeout: 10000, status: 'danger' });
    }
  });
};

const handleImageAnswerDelete = (imageAnswerId) => (dispatch, getState) => {
  var state = getState();
  var exerciseKey = state.get('activeExercise');
  dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageanswerdelete', imageAnswerId], true));
  dispatch(deleteImageAnswer(imageAnswerId))
    .then((res) => {
      if ('error' in res) {
        UIkit.notify(res.error, { timeout: 10000, status: 'danger' });
      }
      dispatch(updatePendingStateIn(['exercises', exerciseKey, 'imageanswerdelete', imageAnswerId], false));
      dispatch(fetchImageAnswers(exerciseKey));
    })
    .catch((err) => console.dir(err));
};

const mapStateToProps = (state) => {
  var key = state.get('activeExercise');
  var activeExerciseState = state.getIn(['exerciseState', state.get('activeExercise')], immutable.Map({}));
  return {
    uploaded: [],
    uploadPending: state.getIn(['pendingState', 'exercises', key, 'imageuploadpending']),
    uploadProgress: state.getIn(['pendingState', 'exercises', key, 'imageupload']),
    exerciseKey: key,
    imageAnswers: activeExerciseState.get('image_answers'),
    imageAnswersData: activeExerciseState.get('image_answers_data', immutable.List([])),
    imageAnswerDeletePending: state.getIn(['pendingState', 'exercises', key, 'imageanswerdelete'], immutable.Map({})),
    showPDF: true || activeExerciseState.getIn(['meta', 'allow_pdf']) // patch default to allow pdf uploads
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onUpload: (event, exerciseKey) => handleUpload(dispatch, event, exerciseKey),
    onImageAnswerDelete: (imageAnswerId) => dispatch(handleImageAnswerDelete(imageAnswerId))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseComponent);
