import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Exercise from './Exercise.jsx';
import Alert from './Alert.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import AuditResponseUpload from './AuditResponseUpload.jsx';
import AuditPreviousMessages from './AuditPreviousMessages.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import _ from 'lodash';

import { 
  fetchStudentDetailResults,
  fetchCurrentAuditsExercise,
  fetchNewAudit,
  saveAudit,
  deleteAudit,
  sendAudit,
} from '../fetchers.js';
import { 
  updateAudit,
  updatePendingStateIn,
} from '../actions.js';


const auditRender = ({ audits, activeAudit, activeExercise, exerciseState, auditData, pendingResults, onSendAudit, pendingSend, pendingSave, onMessageChange, onOldMessageClick, onDeleteAudit, pendingDelete, onSubjectChange, onPublishAudit, pendingPublish, onPassAudit, onRevisionAudit, onSaveAudit, pendingRevision, userPk}, bccStatus, onBccClick) => {
  const auditsList = audits.filter( (audit) => audit.get('exercise') === activeExercise )
                           .filter( (audit) => audit.get('auditor') === userPk )
                           .toList()
                           .sort( (a, b) => a.get('date') > b.get('date') );

  var sendClass = audits.getIn([activeAudit, 'sent']) ? 'uk-button-primary' : 'uk-button-primary';
  var sendName = audits.getIn([activeAudit, 'sent']) ? 'Resend' : 'Send';
  var publishName = audits.getIn([activeAudit, 'published']) ? 'Retract' : 'Publish';
  var publishClass = audits.getIn([activeAudit, 'published']) ? 'uk-button-primary' : 'uk-button-success';
  var revisionNeeded = audits.getIn([activeAudit, 'revision_needed']);
  if(audits.getIn([activeAudit, 'updated']))
      revisionNeeded = null;
  var passedClass = '';
  var revisionClass = '';
  if(revisionNeeded !== null) {
    passedClass = revisionNeeded === true ? '' : 'uk-text-bold';
    revisionClass = revisionNeeded === true ? 'uk-text-bold' : '';
  }
  var auditControls = activeAudit && audits.getIn([activeAudit, 'exercise']) == activeExercise && //{{{
          (<div className="uk-panel uk-panel-box uk-panel-box-primary">
              {
                  pendingSave === null &&
                  <Alert type="error">
                      Error while saving current audit, please copy any unsaved data and reload.
                      <a className="uk-button uk-margin-small-left" onClick={e => onSaveAudit(activeAudit)}>Retry</a>
                  </Alert>
              }
            <form className="uk-form">
              <div className="uk-form-row">
                  <label className="uk-form-label">Subject
                      { pendingSave !== null && <i className={"uk-float-right uk-icon uk-icon-save " + (!pendingSave ? "uk-text-success" : "")}/> }
              { pendingSave === null && <i className={"uk-float-right uk-icon uk-icon-save uk-text-danger"}/> }
                  </label>
                <input type="text" className="uk-width-1-1 uk-form-small" value={audits.getIn([activeAudit, 'subject'])} onChange={e => onSubjectChange(e, activeAudit)}/>
              </div>
              <div className="uk-form-row">
                <label className="uk-form-label">Message</label>
                <textarea className="uk-width-1-1" rows="5" onChange={e => onMessageChange(e, activeAudit)} value={audits.getIn([activeAudit, 'message'],'')} id="audit-message"></textarea>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                  <AuditResponseUpload/>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                <div className="uk-flex uk-flex-middle uk-flex-wrap uk-margin-small-top">
                  <a className={"uk-button uk-margin-small-top uk-position-relative " + sendClass} onClick={() => onSendAudit(activeAudit, bccStatus)} data-uk-tooltip title="Send/resend email">{sendName} 
                  { pendingSend && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  <label data-uk-tooltip title="Send copy to auditor (and you if different)"><input type="checkbox" className="uk-margin-small-right uk-margin-left" checked={bccStatus} onChange={onBccClick}/>Bcc</label>
                </div>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                <div className="uk-button-group uk-flex uk-flex-center">
                  <a className={"uk-button uk-margin-small-top uk-position-relative uk-button-success " + passedClass} onClick={() => onRevisionAudit(activeAudit, false)} data-uk-tooltip title="The student has completed all tasks and no further action is required. Unless otherwise stated this means the student has passed." id="revision-not-needed">
                    Passed { revisionNeeded === false && <i className="uk-icon uk-icon-check uk-icon-medium" id="revision-not-needed-done"/> }
                    { pendingRevision && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  <a className={"uk-button uk-margin-small-top uk-position-relative uk-button-danger " + revisionClass} onClick={() => onRevisionAudit(activeAudit, true)} data-uk-tooltip title="Student need to amend their answer/files." id="revision-needed">
                    Revision needed
                    { revisionNeeded === true && <i className="uk-icon uk-icon-check uk-icon-medium"/> }
                  { pendingRevision && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                </div>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                <div className="uk-flex uk-flex-middle uk-flex-space-between uk-flex-wrap uk-margin-small-top">
                  { audits.getIn([activeAudit, 'revision_needed']) === null && <a className="uk-button uk-text-muted" title="Please select status before publishing." data-uk-tooltip id="publish-single">Publish</a> }
                  { audits.getIn([activeAudit, 'revision_needed']) !== null &&
                  <a className={"uk-button uk-margin-small-top uk-position-relative " + publishClass} onClick={() => onPublishAudit(activeAudit, audits.getIn([activeAudit, 'published']), audits.getIn([activeAudit, 'sent']), bccStatus)} data-uk-tooltip title="The audit will become visible for the student and an email will be sent if first time." id="publish-single">{publishName} 
                  { pendingPublish && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  }
                  <a className="uk-button uk-button-danger uk-margin-small-top uk-position-relative" onClick={() => onDeleteAudit(activeAudit)} data-uk-tooltip title="Delete audit (no trace will remain and the result of the student will be unaffected)">Delete
                  { pendingDelete && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                </div>
              </div>
              <div className="uk-form-row uk-margin-remove">
                <div className="uk-flex uk-flex-space-between uk-flex-wrap uk-margin-small-top">
                  <a className={"uk-button uk-button-small uk-margin-small-top uk-button-primary "} onClick={() => onPassAudit(activeAudit, audits.getIn([activeAudit, 'student']), audits.getIn([activeAudit, 'force_passed']))} data-uk-tooltip title="This will mark the student as passed even if certain required steps are missing.">Pass student
                  { audits.getIn([activeAudit, 'force_passed']) && <i className="uk-icon uk-icon-circle uk-text-success uk-margin-small-left"/> }
                  </a>
                </div>
              </div>
            </form>
            </div>
            );//}}}

  return (
      <div className="uk-width-1-1 uk-margin-small-top uk-padding-remove">
        <div className="uk-panel uk-panel-box">
          <div className="uk-flex uk-flex-column">
            <div className="uk-flex" >
              { audits.getIn([activeAudit, 'exercise']) == activeExercise &&
              <div className="uk-flex-item-1 uk-margin-small-top" style={{maxWidth: '75vw'}}>
                { audits.getIn([activeAudit, 'updated'], false) &&
                  <Badge type="success" className="uk-margin-small-bottom uk-width-1-1 uk-text-center uk-text-large">
                    <span id="audit-updated"/>
                    Updated by student ({ moment(audits.getIn([activeAudit, 'updated_date'], '')).format('YYYY-MM-DD HH:mm')})
                  </Badge>
                }
                { !audits.getIn([activeAudit, 'updated'], false)
               && audits.getIn([activeAudit, 'updated_date']) !== null
               && audits.getIn([activeAudit, 'revision_needed'])
                  &&
                  <Badge type="info" className="uk-margin-small-bottom uk-width-1-1 uk-text-center uk-text-large">
                    Awaiting new response (Previous update by student at { moment(audits.getIn([activeAudit, 'updated_date'], '')).format('YYYY-MM-DD HH:mm')})
                  </Badge>
                }
                { !pendingResults && activeAudit  &&
                  <StudentAuditExercise anonymous={true}/>
                }
                { pendingResults && <Spinner/> }
              </div>
              }
              { audits.getIn([activeAudit, 'exercise']) == activeExercise &&
              <div className="uk-width-2-10 uk-margin-small-top uk-margin-small-left">
                { auditControls }
                <div className="uk-text-small">
                  {activeAudit && <AuditPreviousMessages activeAudit={activeAudit} auditsList={auditsList} onOldMessageClick={onOldMessageClick} confirm={audits.getIn([activeAudit, 'message'], '').length > 0}/>}
                </div>
              </div>
              }
            </div>
          </div>
        </div>
      </div>
  );
}

const handleOldMessageClick = (auditPk, msg) => (dispatch) => {
    dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'save'], true));
    dispatch(updateAudit(auditPk, { message: msg }));
    return dispatch(handleAuditSave(auditPk));
}

const handleAuditSave = (auditPk) => (dispatch, getState) => {
  var state = getState();
  if(state.hasIn(['audit', 'audits', auditPk])) {
    var auditData = state.getIn(['audit', 'audits', auditPk]);
    return dispatch(saveAudit(auditPk, auditData))
      .then( () => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'save'], false)))
      .catch( err => { 
        dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'save'], null));
        throw "saveError";
      })
  } else {
    return console.log('No audit with that pk populated');
  }
}

const handleAuditSend = (auditPk, bcc) => dispatch => {
   dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], true))
   return dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(sendAudit(auditPk, bcc)))
    .then( res => dispatch(updateAudit(auditPk, { sent: 'success' in res })))
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], false)))
    .catch( err => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], null)));
}

const handleAuditPass = (auditPk, studentPk, currentlyPassed) => dispatch => {
  dispatch(updateAudit(auditPk, { force_passed: !currentlyPassed}))
  return dispatch(handleAuditSave(auditPk))
    .then(dispatch(fetchStudentDetailResults(studentPk)))
    .catch( err => console.dir(err));
}

const handleAuditPublish = (auditPk, currentlyPublished, sent, bcc) => (dispatch, getState) => {
  dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'publish'], true));
  dispatch(updateAudit(auditPk, { published: !currentlyPublished }))
  return dispatch(handleAuditSave(auditPk))
      .then(() => {
          if(!currentlyPublished && !sent)dispatch(handleAuditSend(auditPk, bcc));
      })
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'publish'], false)))
    .catch( err => {
        var state = getState();
        var auditee = state.getIn(['audit', 'audits', auditPk, 'student_username'], '');
        UIkit.notify('An error occured while publishing audit for ' + auditee + ', please reload this page and try again.', { status: 'danger' });
      dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'publish'], null))
      dispatch(updateAudit(auditPk, { published: currentlyPublished }))
    });
}

const handlePublishAndSend = (audits) => dispatch => {
  audits.forEach( audit => {
    dispatch(handleAuditPublish(audit.get('pk'), false, audit.get('sent'), false))
      .then(() => dispatch(handleAuditSend(audit.get('pk'), false)));
  });
  /**/
}

const handleAuditRevision= (auditPk, needRevision) => dispatch => {
  dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'revision'], true));
  dispatch(updateAudit(auditPk, { revision_needed: needRevision, updated: false }))
  return dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'revision'], false)))
    .catch( err => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'revision'], false)));
}

const handleDeleteAudit = (auditPk) => dispatch => {
   dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'delete'], true))
   return dispatch(deleteAudit(auditPk))
    .then(json => {
      if('success' in json)
        return json;
      else
        throw "Delete failed";
    })
    .then( () => dispatch(fetchCurrentAuditsExercise()) )
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'delete'], false)))
    .catch( err => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'delete'], false)));
}

const throttleSave = _.throttle( (dispatch, auditPk) => {
  dispatch(handleAuditSave(auditPk));
}, 1000);

const mapStateToProps = state => {
  var activeAudit = state.getIn(['audit','activeAudit'], false);
  //var changedAudit = state.getIn(['audit','activeAuditChanged'], false);
  var auditData = state.getIn(['audit', 'auditdata', activeAudit], immutable.Map({}))
  var activeExercise = state.get('activeExercise');
  return {
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
    pendingStateAudits: state.getIn(['pendingState', 'audit', 'audits'], immutable.Map({})),
  }
};

const mapDispatchToProps = dispatch => ({
  onSendAudit: (auditPk, bcc) => dispatch(handleAuditSend(auditPk, bcc)),
  onPublishAudit: (auditPk, currentlyPublished, sent, bcc) => dispatch(handleAuditPublish(auditPk, currentlyPublished, sent, bcc)),
  onRevisionAudit: (auditPk, needRevision) => dispatch(handleAuditRevision(auditPk, needRevision)),
  onDeleteAudit: (auditPk) => dispatch(handleDeleteAudit(auditPk)),
  onPassAudit: (auditPk, studentPk, currentlyPassed) => dispatch(handleAuditPass(auditPk, studentPk, currentlyPassed)),
  onSaveAudit: (auditPk) => dispatch(handleAuditSave(auditPk)),
  onMessageChange: (e, pk) =>  {
    dispatch(updatePendingStateIn(['audit', 'audits', pk, 'save'], true));
    dispatch(updateAudit(pk, {'message': e.target.value}))
    throttleSave(dispatch, pk);
  },
  onSubjectChange: (e, pk) =>  {
    dispatch(updatePendingStateIn(['audit', 'audits', pk, 'save'], true));
    dispatch(updateAudit(pk, {'subject': e.target.value}))
    throttleSave(dispatch, pk);
  },
  onOldMessageClick: (audit, msg) => dispatch(handleOldMessageClick(audit, msg)),
});

class BaseAudit extends Component {
  constructor() {
    super();
    this.state = { 
      bcc: false,
    }
  }
  handleBccClick = (e) => {
    this.setState( {bcc: e.target.checked} );
  }
  render() {
    return auditRender(this.props, this.state.bcc, this.handleBccClick);
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
export { handlePublishAndSend };
