import React from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import SafeImg from './SafeImg.jsx';
import Badge from './Badge.jsx';
import {
  uploadAuditResponseFile,
  fetchCurrentAuditsExercise,
  deleteAuditResponseFile,
  updatePendingStateIn
} from '../fetchers.js';
import { SUBPATH } from '../settings.js';

const BaseComponent = ({
  auditPk,
  auditResponseFiles,
  uploaded,
  onUpload,
  uploadPending,
  uploadProgress,
  onAuditResponseFileDelete,
  auditResponseFileDeletePending
}) => {
  var renderAuditResponse = auditResponseFiles.map((auditResponse) => (
    <div className="exercise-thumb-wrap" key={auditResponse.get('id')}>
      {auditResponse.get('filetype') === 'IMG' && (
        <a
          href={SUBPATH + '/auditresponsefile/view/' + auditResponse.get('id')}
          data-uk-lightbox
          data-lightbox-type="image"
        >
          <SafeImg src={SUBPATH + '/auditresponsefile/view/' + auditResponse.get('id') + '/thumb'}>
            <i className="uk-icon uk-icon-large uk-icon-question" />
          </SafeImg>
        </a>
      )}
      {auditResponse.get('filetype') === 'PDF' && (
        <a href={SUBPATH + '/auditresponsefile/view/' + auditResponse.get('id')} target="_blank" rel="noreferrer">
          <i className="uk-icon uk-icon-large uk-icon-file-pdf-o" />
        </a>
      )}

      <div className="exercise-thumb-badge">
        <a
          onClick={() =>
            UIkit.modal.confirm('Delete response file?', () =>
              onAuditResponseFileDelete(auditPk, auditResponse.get('id'))
            )
          }
        >
          <Badge className="uk-badge-notification">
            {!auditResponseFileDeletePending.get(auditResponse.get('id'), false) && (
              <i className="uk-icon uk-icon-trash" />
            )}
            {auditResponseFileDeletePending.get(auditResponse.get('id'), false) && <Spinner />}
          </Badge>
        </a>
      </div>
    </div>
  ));
  var progress = (
    <div className="uk-progress uk-progress-mini uk-display-inline-block uk-margin-remove" style={{ width: '100px' }}>
      <div className="uk-progress-bar" style={{ width: uploadProgress * 100 + '%' }}></div>
    </div>
  );
  return (
    <div>
      {renderAuditResponse}
      <div className="uk-button-group uk-align-medium-right uk-margin-small">
        {uploadPending && (
          <span className="uk-button">
            {progress} {uploadPending ? <i className="uk-icon-cog uk-icon-spin"></i> : ''}
          </span>
        )}

        <div className="uk-form-file">
          <a type="file" className={'uk-button'}>
            <i className="uk-icon-camera" />
          </a>
          <input type="file" accept="image/*" onChange={(e) => onUpload(e, auditPk)} />
        </div>

        <div className="uk-form-file">
          <a type="file" className={'uk-button'}>
            <i className="uk-icon-file-pdf-o" title="PDF" />
          </a>
          <input type="file" accept="application/pdf" onChange={(e) => onUpload(e, auditPk)} />
        </div>
      </div>
    </div>
  );
};

const handleUpload = (dispatch, event, auditPk) => {
  var file = event.target.files[0];
  dispatch(uploadAuditResponseFile(auditPk, file));
};

const handleAuditResponseFileDelete = (auditPk, auditResponseId) => (dispatch, getState) => {
  var state = getState();
  var exerciseKey = state.get('activeExercise');
  dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'deletePending', auditResponseId], true));
  dispatch(deleteAuditResponseFile(auditResponseId))
    .then(() => {
      dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'deletePending', auditResponseId], false));
      dispatch(fetchCurrentAuditsExercise());
    })
    .catch((err) => console.dir(err));
};

const mapStateToProps = (state) => {
  const auditPk = state.getIn(['audit', 'activeAudit']);
  var activeAuditState = state.getIn(['audit', 'audits', auditPk], immutable.Map({}));
  return {
    uploaded: [],
    uploadPending: state.getIn(['pendingState', 'audit', 'audits', auditPk, 'uploadPending']),
    uploadProgress: state.getIn(['pendingState', 'audit', 'audits', auditPk, 'uploadProgress']),
    auditPk: auditPk,
    auditResponseFiles: activeAuditState.getIn(['responsefiles'], immutable.List([])),
    auditResponseFileDeletePending: state.getIn(
      ['pendingState', 'audit', 'audits', auditPk, 'deletePending'],
      immutable.Map({})
    )
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    onUpload: (event, auditPk) => handleUpload(dispatch, event, auditPk),
    onAuditResponseFileDelete: (auditPk, auditResponseId) =>
      dispatch(handleAuditResponseFileDelete(auditPk, auditResponseId))
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(BaseComponent);
