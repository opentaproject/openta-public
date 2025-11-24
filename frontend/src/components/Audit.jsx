import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Alert from './Alert.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import AuditResponseUpload from './AuditResponseUpload.jsx';
import AuditPreviousMessages from './AuditPreviousMessages.jsx';
import moment from 'moment';
import _ from 'lodash';

import {
  fetchStudentDetailResults,
  fetchCurrentAuditsExercise,
  saveAudit,
  deleteAudit,
  sendAudit
} from '../fetchers.js';
import { updateAudit, updatePendingStateIn } from '../actions.js';

class BaseAudit extends Component {
  constructor(props) {
    super(props);
    this.input = React.createRef();
    this.state = {
      bcc: true, // Set default to true!
      //defaultpoints: '1',
      oldpk: '0'
    };
  }
  handleBccClick = (e) => {
    this.setState({ bcc: e.target.checked });
  };
  //handleDefaultPointsChange(event) {
  //  this.setState({defaultpoints : event.target.value } )
  //  console.log("onSubmit " , this.state.defaultpoints)
  //  event.preventDefault();
  // }

  //unsetFirstTime(event,pk) {
  // //console.log("OLDPK = ", this.state.oldpk , " NEWPK = ", pk )
  // this.setState({oldpk: pk })
  //event.preventDefault();
  //}

  render(bccStatus, onBccClick) {
    var audits = this.props.audits;
    var activeAudit = this.props.activeAudit;
    var activeExercise = this.props.activeExercise;
    var exerciseState = this.props.exerciseState;
    var auditData = this.props.auditData;
    var pendingResults = this.props.pendingResults;
    var onSendAudit = this.props.onSendAudit;
    var pendingSend = this.props.pendingSend;
    var pendingSave = this.props.pendingSave;
    var onMessageChange = this.props.onMessageChange;
    var onPointsChange = this.props.onPointsChange;
    var onOldMessageClick = this.props.onOldMessageClick;
    var onDeleteAudit = this.props.onDeleteAudit;
    var pendingDelete = this.props.pendingDelete;
    var onSubjectChange = this.props.onSubjectChange;
    var onPublishAudit = this.props.onPublishAudit;
    var pendingPublish = this.props.pendingPublish;
    var onPassAudit = this.props.onPassAudit;
    var onRevisionAudit = this.props.onRevisionAudit;
    var onSaveAudit = this.props.onSaveAudit;
    var pendingRevision = this.props.pendingRevision;
    var userPk = this.props.userPk;
    var use_email = this.props.use_email;

    var sendClass = audits.getIn([activeAudit, 'sent']) ? 'uk-button-primary' : 'uk-button-primary';
    var sendName = audits.getIn([activeAudit, 'sent']) ? 'Resend Email Now ' : 'Send Email Now';
    var publishName = audits.getIn([activeAudit, 'published']) ? 'Unpublish' : 'Publish';
    var publishClass = audits.getIn([activeAudit, 'published']) ? 'uk-button-primary' : 'uk-button-success';
    var revisionNeeded = audits.getIn([activeAudit, 'revision_needed']);
    if (audits.getIn([activeAudit, 'updated'])) {
      revisionNeeded = null;
    }
    var passedClass = '';
    var revisionClass = '';
    if (revisionNeeded !== null) {
      passedClass = revisionNeeded === true ? '' : 'uk-text-bold';
      revisionClass = revisionNeeded === true ? 'uk-text-bold' : '';
    }
    var points = audits.getIn([activeAudit, 'points'], '');
    const auditsList = audits
      .filter((audit) => audit.get('exercise') === activeExercise)
      .filter((audit) => audit.get('auditor') === userPk)
      .filter((audit) => audit.get('pk') !== activeAudit)
      .toList();

    //console.log("NEW PK = ", activeAudit, " OLDPK " , this.state.oldpk )
    //if ( activeAudit !== this.state.oldpk && points == '' ){
    //	  points = this.state.defaultpoints
    //	}
    var message = audits.getIn([activeAudit, 'message'], '');
    var auditControls = activeAudit &&
      audits.getIn([activeAudit, 'exercise']) == activeExercise && ( //{{{
        <div className="uk-panel uk-panel-box uk-panel-box-primary">
          {pendingSave === null && (
            <Alert type="error">
              Error while saving current audit, please copy any unsaved data and reload.
              <a className="uk-button uk-margin-small-left" onClick={(e) => onSaveAudit(activeAudit)}>
                Retry
              </a>
            </Alert>
          )}
          <form className="uk-form">
            <div className="uk-form-row">
              <label className="uk-form-label">
                Subject
                {pendingSave !== null && (
                  <i className={'uk-float-right uk-icon uk-icon-save ' + (!pendingSave ? 'uk-text-success' : '')} />
                )}
                {pendingSave === null && <i className={'uk-float-right uk-icon uk-icon-save uk-text-danger'} />}
              </label>
              <input
                type="text"
                className="uk-width-1-1 uk-form-small"
                value={audits.getIn([activeAudit, 'subject'])}
                onChange={(e) => onSubjectChange(e, activeAudit)}
              />
            </div>

            <div className="uk-form-row">
              <label className="uk-form-label">Message</label>
              <textarea
                className="uk-width-1-1"
                rows="5"
                onChange={(e) => onMessageChange(e, activeAudit)}
                value={audits.getIn([activeAudit, 'message'], '')}
                id="audit-message"
              ></textarea>
            </div>

            <div className="uk-text-small">
              {activeAudit && (
                <AuditPreviousMessages
                  activeAudit={activeAudit}
                  auditsList={auditsList}
                  onOldMessageClick={onOldMessageClick}
                  confirm={audits.getIn([activeAudit, 'message'], '').length > 0}
                />
              )}
            </div>

            <div className="uk-form-row">
              <label className="uk-form-label">Points: </label>
              <input
                onChange={(e) => onPointsChange(e, activeAudit)}
                type="text"
                ref={this.input}
                value={points}
                id="audit-points"
              />
            </div>

            <div className="uk-form-row uk-margin-small-top">
              <AuditResponseUpload />
            </div>
            {!use_email && (
              <button
                className={
                  'uk-button uk-button-medium uk-margin-small-top uk-button-text uk-button-small uk-button-text'
                }
                type="button"
                data-uk-tooltip
              >
                {' '}
                No email will be sent{' '}
              </button>
            )}

            {use_email && (
              <div className="uk-form-row uk-margin-small-top">
                <div className="uk-flex uk-flex-middle uk-flex-wrap uk-margin-small-top">
                  <a
                    className={'uk-button uk-button-small uk-margin-small-top uk-position-relative ' + sendClass}
                    onClick={() => onSendAudit(activeAudit, bccStatus)}
                    data-uk-tooltip
                    title="Send/resend email"
                  >
                    {sendName}
                    {pendingSend && <Spinner size="uk-icon-small uk-position-top-right" />}
                  </a>
                  <label data-uk-tooltip title="Send copy to auditor (and you if different)">
                    <input
                      type="checkbox"
                      className="uk-margin-small-right uk-margin-left"
                      checked={bccStatus}
                      onChange={onBccClick}
                    />
                    Bcc
                  </label>
                </div>
              </div>
            )}

            <div className="uk-flex uk-flex-between uk-form-column uk-text-small uk-width-1-1 uk-margin-small-top">
              <a
                className={
                  'uk-button uk-margin-small-top uk-position-relative uk-button-small uk-button-success ' + passedClass
                }
                onClick={() => onRevisionAudit(activeAudit, false)}
                data-uk-tooltip
                title="The student has completed all tasks and no further action is required. Unless otherwise stated this means the student has passed."
                id="revision-not-needed"
              >
                Mark as final{' '}
                {revisionNeeded === false && (
                  <i className="uk-icon uk-icon-check uk-icon-small " id="revision-not-needed-done" />
                )}
                {pendingRevision && <Spinner size="uk-icon-small uk-position-top-right" />}
              </a>

              <a
                className={'uk-button uk-margin-small-top uk-button-small uk-button-danger ' + revisionClass}
                onClick={() => onRevisionAudit(activeAudit, true)}
                data-uk-tooltip
                title="Student need to amend their answer/files."
                id="revision-needed"
              >
                Allow resubmit
                {revisionNeeded === true && <i className="uk-icon uk-icon-check uk-icon-small" />}
                {pendingRevision && <Spinner size="uk-icon-small uk-position-top-right" />}
              </a>

              <a
                className={'uk-button uk-margin-small-top uk-button-small uk-button-primary' + revisionClass}
                onClick={() => onRevisionAudit(activeAudit, null)}
                data-uk-tooltip
                title="postpone"
                id="revision-postponed"
              >
                Undecided so keep in queue
                {revisionNeeded === true && <i className="uk-icon uk-icon-check uk-icon-small" />}
                {pendingRevision && <Spinner size="uk-icon-small uk-position-top-right" />}
              </a>
            </div>

            <div className="uk-form-column uk-width-1-1 uk-margin-small-top">
              <div className="uk-flex  uk-flex-middle uk-flex-space-between uk-flex-wrap uk-margin-small-top">
                {audits.getIn([activeAudit, 'revision_needed']) === null && (
                  <a
                    className="uk-button uk-button-small uk-text-muted"
                    title="Please select status before publishing."
                    data-uk-tooltip
                    id="publish-single"
                  >
                    Publish
                  </a>
                )}
                {audits.getIn([activeAudit, 'revision_needed']) !== null && (
                  <a
                    className={'uk-button uk-button-small uk-margin-small-top uk-position-relative ' + publishClass}
                    onClick={() =>
                      onPublishAudit(
                        activeAudit,
                        audits.getIn([activeAudit, 'published']),
                        audits.getIn([activeAudit, 'sent']),
                        bccStatus,
                        userPk
                      )
                    }
                    data-uk-tooltip
                    title="The audit will become visible for the student and if email will be sent if first time and email is activated."
                    id="publish-single"
                  >
                    {publishName}
                    {pendingPublish && <Spinner size="uk-icon-small uk-position-top-right" />}
                  </a>
                )}
                <a
                  className="uk-button uk-button-small uk-button-danger uk-margin-small-top uk-position-relative"
                  onClick={() => onDeleteAudit(activeAudit)}
                  data-uk-tooltip
                  title="Delete audit (no trace will remain and the result of the student will be unaffected)"
                >
                  Delete from queue
                  {pendingDelete && <Spinner size="uk-icon-small uk-position-top-right" />}
                </a>
              </div>
            </div>
            <div className="uk-form-row uk-margin-remove">
              <div className="uk-flex uk-flex-space-between uk-flex-wrap uk-margin-small-top">
                {!audits.getIn([activeAudit, 'force_passed'], false) && (
                  <a
                    className={'uk-button uk-button-small uk-margin-small-top uk-width-1-1 uk-button-primary '}
                    onClick={() =>
                      onPassAudit(
                        activeAudit,
                        audits.getIn([activeAudit, 'student']),
                        audits.getIn([activeAudit, 'force_passed'])
                      )
                    }
                    data-uk-tooltip
                    title="This will mark the student as passed even if certain required steps are missing."
                  >
                    Force Pass
                  </a>
                )}
                {audits.getIn([activeAudit, 'force_passed'], false) && (
                  <a
                    className={'uk-button uk-button-small uk-margin-small-top uk-width-1-1 uk-button-primary '}
                    onClick={() =>
                      onPassAudit(
                        activeAudit,
                        audits.getIn([activeAudit, 'student']),
                        audits.getIn([activeAudit, 'force_passed'])
                      )
                    }
                    data-uk-tooltip
                    title="This will mark the student as passed even if certain required steps are missing."
                  >
                    Undo Force Pass{' '}
                  </a>
                )}
              </div>
            </div>
          </form>
        </div>
      ); //}}}

    return (
      <div className="uk-flex uk-padding-large uk-flex-center uk-width-1-1">
        <div className="uk-width-1-1 uk-margin-small-top uk-padding-remove">
          <div className="uk-panel uk-panel-box">
            <div className="uk-flex uk-flex-column">
              <div className="uk-flex">
                {audits.getIn([activeAudit, 'exercise']) == activeExercise && (
                  <div className="uk-flex-item-1 uk-margin-small-top" style={{ maxWidth: '75vw' }}>
                    {audits.getIn([activeAudit, 'updated'], false) && (
                      <Badge
                        type="success"
                        className="uk-margin-small-bottom uk-width-1-1 uk-text-center uk-text-large"
                      >
                        <span id="audit-updated" />
                        Updated by student (
                        {moment(audits.getIn([activeAudit, 'updated_date'], '')).format('YYYY-MM-DD HH:mm')})
                      </Badge>
                    )}
                    {!audits.getIn([activeAudit, 'updated'], false) &&
                      audits.getIn([activeAudit, 'updated_date']) !== null &&
                      audits.getIn([activeAudit, 'revision_needed']) && (
                        <Badge type="info" className="uk-margin-small-bottom uk-width-1-1 uk-text-center uk-text-large">
                          Awaiting new response (Previous update by student at{' '}
                          {moment(audits.getIn([activeAudit, 'updated_date'], '')).format('YYYY-MM-DD HH:mm')})
                        </Badge>
                      )}
                    {!pendingResults && activeAudit && <StudentAuditExercise anonymous={true} />}
                    {pendingResults && <Spinner />}
                  </div>
                )}
                {audits.getIn([activeAudit, 'exercise']) == activeExercise && (
                  <div className="uk-width-2-10 uk-margin-small-top uk-margin-small-left">{auditControls}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

const handleOldMessageClick = (auditPk, msg, points, revision_needed) => (dispatch) => {
  dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'save'], true));
  dispatch(updateAudit(auditPk, { message: msg, points: points, revision_needed: revision_needed }));
  return dispatch(handleAuditSave(auditPk));
};

const handleAuditSave = (auditPk) => (dispatch, getState) => {
  var state = getState();
  if (state.hasIn(['audit', 'audits', auditPk])) {
    var auditData = state.getIn(['audit', 'audits', auditPk]);
    return dispatch(saveAudit(auditPk, auditData))
      .then(() => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'save'], false)))
      .catch((err) => {
        dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'save'], null));
        // throw "saveError"; // SAVE ERROR WHEN ENTERING POINTS FOR THE FIRST TIME
      });
  } else {
    return console.log('No audit with that pk populated');
  }
};

const handleAuditSend = (auditPk, bcc) => (dispatch) => {
  dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'send'], true));
  return dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(sendAudit(auditPk, bcc)))
    .then((res) => dispatch(updateAudit(auditPk, { sent: 'success' in res, source: 'A' })))
    .then(() => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'send'], false)))
    .catch((err) => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'send'], null)));
};

const handleAuditPass = (auditPk, studentPk, currentlyPassed) => (dispatch) => {
  dispatch(updateAudit(auditPk, { force_passed: !currentlyPassed }));
  return dispatch(handleAuditSave(auditPk))
    .then(dispatch(fetchStudentDetailResults(studentPk)))
    .catch((err) => console.dir(err));
};

const handleAuditPublish = (auditPk, currentlyPublished, sent, bcc, auditor) => (dispatch, getState) => {
  dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'publish'], true));
  dispatch(updateAudit(auditPk, { published: !currentlyPublished, auditor: auditor }));
  return dispatch(handleAuditSave(auditPk))
    //.then(() => {
    //  if (!currentlyPublished && !sent) {
    //    dispatch(handleAuditSend(auditPk, bcc));
    //  }
    //})
    .then(() => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'publish'], false)))
    .catch((err) => {
      var state = getState();
      var auditee = state.getIn(['audit', 'audits', auditPk, 'student_username'], '');
      var auditor = state.getIn(['audit', 'audits', auditPk, 'auditor'], '');
      UIkit.notify(
        'An error occured while publishing audit for ' + auditee + ', please reload this page and try again.',
        { status: 'danger' }
      );
      dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'publish'], null));
      dispatch(updateAudit(auditPk, { published: currentlyPublished, auditor: auditor }));
    });
};

const handlePublishAndSend = (audits) => (dispatch) => {
  // allaudits = audits => [ (audit.get('pk'), false, audit.get('sent'),false, audit.getIn(['auditor_data','id']))];
  console.log(JSON.stringify( audits ));
  var allaudits = audits.forEach((audit) => {
    audit.get('pk'), false, audit.get('sent'), false, audit.getIn(['auditor_data', 'id']) } );
  console.log(JSON.stringify( allaudits));
  audits.forEach((audit) => {
    dispatch(handleAuditPublish(audit.get('pk'), false, audit.get('sent'), false, audit.getIn(['auditor_data', 'id'])));
  });
  /**/
};

const handleAuditRevision = (auditPk, needRevision) => (dispatch) => {
  dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'revision'], true));
  dispatch(updateAudit(auditPk, { revision_needed: needRevision, updated: false }));
  return dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'revision'], false)))
    .catch((err) => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'revision'], false)));
};

const handleDeleteAudit = (auditPk) => (dispatch) => {
  dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'delete'], true));
  return dispatch(deleteAudit(auditPk))
    .then((json) => {
      if ('success' in json) {
        return json;
      } else {
        throw 'Delete failed';
      }
    })
    .then(() => dispatch(fetchCurrentAuditsExercise()))
    .then(() => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'delete'], false)))
    .catch((err) => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'delete'], false)));
};

const throttleSave = _.throttle((dispatch, auditPk) => {
  dispatch(handleAuditSave(auditPk));
}, 1000);

const mapStateToProps = (state) => {
  var activeAudit = state.getIn(['audit', 'activeAudit'], false);
  //var changedAudit = state.getIn(['audit','activeAuditChanged'], false);
  var auditData = state.getIn(['audit', 'auditdata', activeAudit], immutable.Map({}));
  var activeExercise = state.get('activeExercise');
  return {
    use_email: state.getIn(['course', 'use_email'], false),
    userPk: state.getIn(['login', 'user_pk']),
    audits: state.getIn(['audit', 'audits'], immutable.Map({})),
    auditData: auditData,
    activeAudit: activeAudit,
    activeExercise: activeExercise,
    exerciseState: state.getIn(['exerciseState', activeExercise]),
    pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
    pendingSend: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'send'], false),
    pendingSave: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'save'], false),
    pendingDelete: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'delete'], false),
    pendingPublish: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'publish'], false),
    pendingRevision: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'revision'], false),
    pendingStateAudits: state.getIn(['pendingState', 'audit', 'audits'], immutable.Map({}))
  };
};

const mapDispatchToProps = (dispatch) => ({
  onSendAudit: (auditPk, bcc) => dispatch(handleAuditSend(auditPk, bcc)),
  onPublishAudit: (auditPk, currentlyPublished, sent, bcc, auditor) =>
    dispatch(handleAuditPublish(auditPk, currentlyPublished, sent, bcc, auditor)),
  onRevisionAudit: (auditPk, needRevision) => dispatch(handleAuditRevision(auditPk, needRevision)),
  onDeleteAudit: (auditPk) => dispatch(handleDeleteAudit(auditPk)),
  onPassAudit: (auditPk, studentPk, currentlyPassed) => dispatch(handleAuditPass(auditPk, studentPk, currentlyPassed)),
  onSaveAudit: (auditPk) => dispatch(handleAuditSave(auditPk)),

  onMessageChange: (e, pk) => {
    dispatch(updatePendingStateIn(['audit', 'audits', pk, 'save'], true));
    dispatch(updateAudit(pk, { message: e.target.value, modified: moment().format() }));
    throttleSave(dispatch, pk);
  },

  onPointsChange: (e, pk) => {
    dispatch(updatePendingStateIn(['audit', 'audits', pk, 'save'], true));
    dispatch(updateAudit(pk, { points: e.target.value, modified: moment().format() }));
    throttleSave(dispatch, pk);
  },

  onSubjectChange: (e, pk) => {
    dispatch(updatePendingStateIn(['audit', 'audits', pk, 'save'], true));
    dispatch(updateAudit(pk, { subject: e.target.value }));
    throttleSave(dispatch, pk);
  },
  onOldMessageClick: (audit, msg, points, revision_needed) =>
    dispatch(handleOldMessageClick(audit, msg, points, revision_needed))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
export { handlePublishAndSend, handleAuditRevision, updateAudit };
