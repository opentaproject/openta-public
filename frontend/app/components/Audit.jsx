import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import Exercise from './Exercise.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import AuditStatistics from './AuditStatistics.jsx';
import AuditResponseUpload from './AuditResponseUpload.jsx';
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
  setActiveAudit,
  updateAudit,
  updatePendingStateIn,
  setSelectedStudentResults,
  setDetailResultExercise,
} from '../actions.js';

const BaseAudit = ({ audits, activeAudit, activeExercise, exerciseState, auditData, onAuditChange, pendingResults, onSendAudit, pendingSend, pendingSave, onMessageChange, onOldMessageClick, onAddAudit, onDeleteAudit, pendingDelete, onSubjectChange, onResolveAudit, pendingResolve, onPassAudit}) => {
  var auditsList = audits.filter( (audit) => audit.get('exercise') === activeExercise )
                         .toList()
                         .sort( (a, b) => a.get('date') > b.get('date') );
  var nAudits = auditsList.size;

  const renderAuditListItem = (audit, nInList) => {
    var activeClass = activeAudit === audit.get('pk') ? ' uk-text-bold ' : ' ';
    var doneClass = (audit.get('sent') && audit.get('resolved')) ? ' uk-button-success ' : ' ';
    var unresolvedClass = !audit.get('resolved') ? ' uk-button-danger ' : ' uk-button-primary ';
    return (
      <a key={audit.get('pk')} onClick={() => onAuditChange(audit.get('pk'), audit.get('student'), activeExercise)} className={"uk-button uk-button-mini " + doneClass + unresolvedClass + activeClass} title={audit.get('student_username')} data-uk-tooltip>
        { activeAudit === audit.get('pk') && <i className="uk-text-primary uk-icon uk-icon-caret-right uk-icon-small"/> }
        {nInList+1}
      </a>
    );
  };
  var auditsRender =  auditsList.map( (audit, key) => {
    return renderAuditListItem(audit, key);
  });
  var current = auditsList.findEntry( item => item.get('pk') === activeAudit, null, [0])[0];
  var next = current + 1 < auditsList.size ? current + 1 : current;
  var showNext = current + 1 < auditsList.size;
  var prev = current - 1 >= 0 ? current - 1 : current;
  var showPrev = current -1 >= 0;
  var exerciseName = exerciseState.getIn(['json', 'exercise', 'exercisename', '$'], '');
  var auditList = //{{{
    (
          <div className="uk-panel uk-panel-box uk-panel-box-primary" style={{padding: '5px'}}>
            <div className="uk-float-left"><div>Audits for <a href={"#exercise/"+activeExercise} target="_blank" className="uk-button" title="Click to open exercise in a new tab">{exerciseName}</a></div><div><AuditStatistics/></div></div>
            <div className="uk-flex uk-flex-wrap uk-flex-right">
            <div>
            <div className="uk-grid uk-margin-small-left uk-margin-right uk-margin-small-top">
             {auditsRender}
            </div>
            </div>
            <div className="uk-button-group uk-display-inline-block uk-margin-small-top">
              <button className="uk-button" type="button" onClick={ () => onAddAudit(activeExercise) }>Add student</button>
              <button className="uk-button" type="button" onClick={() => showPrev ? onAuditChange(auditsList.getIn([prev, 'pk']), auditsList.getIn([prev,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-left"/></button>
              <button className="uk-button" type="button" disabled>{nAudits > 0 ? (current+1) : 0} / {auditsList.size} </button>
              <button className="uk-button" type="button" onClick={() => showNext ? onAuditChange(auditsList.getIn([next, 'pk']), auditsList.getIn([next,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-right"/></button>
            </div>
            </div>
          </div>);//}}}
  var sendClass = audits.getIn([activeAudit, 'sent']) ? 'uk-button-primary' : 'uk-button-success';
  var sendName = audits.getIn([activeAudit, 'sent']) ? 'Resend' : 'Send';
  var resolveName = audits.getIn([activeAudit, 'resolved']) ? 'Unresolve' : 'Resolve';
  var resolveClass = audits.getIn([activeAudit, 'resolved']) ? 'uk-button-primary' : 'uk-button-success';
  var auditMessage = activeAudit && audits.getIn([activeAudit, 'exercise']) == activeExercise && //{{{
          (<div className="uk-panel uk-panel-box uk-panel-box-primary">
            <form className="uk-form">
              <div className="uk-form-row">
                <label className="uk-form-label">Subject <i className={"uk-float-right uk-icon uk-icon-save " + (!pendingSave ? "uk-text-success" : "")}/></label>
                <input type="text" className="uk-width-1-1 uk-form-small" value={audits.getIn([activeAudit, 'subject'])} onChange={e => onSubjectChange(e, activeAudit)}/>
              </div>
              <div className="uk-form-row">
                <label className="uk-form-label">Message</label>
                <textarea className="uk-width-1-1" rows="5" onChange={e => onMessageChange(e, activeAudit)} value={audits.getIn([activeAudit, 'message'],'')}></textarea>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                  <AuditResponseUpload/>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                <div className="uk-flex uk-flex-space-between uk-flex-wrap uk-margin-small-top">
                  <a className={"uk-button uk-margin-small-top uk-position-relative " + sendClass} onClick={() => onSendAudit(activeAudit)}>{sendName} 
                  { pendingSend && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  <a className={"uk-button uk-margin-small-top uk-position-relative " + resolveClass} onClick={() => onResolveAudit(activeAudit, audits.getIn([activeAudit, 'resolved']))}>{resolveName} 
                  { pendingResolve && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  <a className="uk-button uk-button-danger uk-margin-small-top uk-position-relative" onClick={() => onDeleteAudit(activeAudit)}>Delete
                  { pendingDelete && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                </div>
              </div>
              <div className="uk-form-row uk-margin-remove">
                <div className="uk-flex uk-flex-space-between uk-flex-wrap uk-margin-small-top">
                  <a className={"uk-button uk-margin-small-top uk-button-primary "} onClick={() => onPassAudit(activeAudit, audits.getIn([activeAudit, 'student']), audits.getIn([activeAudit, 'force_passed']))}>Pass student
                  { audits.getIn([activeAudit, 'force_passed']) && <i className="uk-icon uk-icon-circle uk-text-success uk-margin-small-left"/> }
                  </a>
                </div>
              </div>
            </form>
            </div>
            );//}}}
  var previousMessages = activeAudit && //{{{
    (
      <div className="uk-panel uk-panel-box uk-margin-small-top">
      <h3 className="uk-panel-title">Other messages</h3>
      <table className="uk-table uk-table-hover">
      <tbody>
      { auditsList.filter( audit => /*audit.get('sent') &&*/ audit.get('message','').length > 0)
      .groupBy( audit => audit.get('message') )
      .map( group => group.first() )
      .map( audit => (
        <tr key={audit.get('pk')} onClick={() => onOldMessageClick(activeAudit, audit.get('message'))}>
          <td>{ audit.get('message') }</td>
        </tr>
      ))
     .toList() }
      </tbody>
      </table>
      </div>
    );//}}}
  return (
      <div className="uk-width-1-1 uk-margin-top">
        <div className="uk-panel uk-panel-box">
          <div className="uk-flex uk-flex-column">
            <div className="uk-width-1-1">{auditList}</div>
            <div className="uk-flex" >
              { audits.getIn([activeAudit, 'exercise']) == activeExercise &&
              <div className="uk-flex-item-1 uk-margin-small-top" style={{maxWidth: '75vw'}}>
                { !pendingResults && activeAudit  && <StudentAuditExercise anonymous={true}/> }
                { pendingResults && <Spinner/> }
              </div>
              }
              { audits.getIn([activeAudit, 'exercise']) == activeExercise &&
              <div className="uk-width-2-10 uk-margin-small-top uk-margin-small-left">
                { auditMessage }
                <div className="uk-text-small">
                  { previousMessages }
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
      .then( () => dispatch(updatePendingStateIn(['audit', 'audits', auditPk, 'save'], false)));
  } else {
    return console.log('No audit with that pk populated');
  }
}

const handleAuditSend = (auditPk) => dispatch => {
   dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], true))
   return dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(sendAudit(auditPk)))
    .then( res => dispatch(updateAudit(auditPk, { sent: 'success' in res })))
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], false)))
    .catch( err => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], false)));
}

const handleAuditPass = (auditPk, studentPk, currentlyPassed) => dispatch => {
  dispatch(updateAudit(auditPk, { force_passed: !currentlyPassed}))
  return dispatch(handleAuditSave(auditPk))
    .then(dispatch(fetchStudentDetailResults(studentPk)))
    .catch( err => console.dir(err));
}

const handleAuditResolve = (auditPk, currentlyResolved) => dispatch => {
  dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'resolve'], true));
  dispatch(updateAudit(auditPk, { resolved: !currentlyResolved }))
  return dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'resolve'], false)))
    .catch( err => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'resolve'], false)));
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
    audits: state.getIn(['audit', 'audits'], immutable.Map({})),
    auditData: auditData,
    activeAudit: activeAudit,
    activeExercise: activeExercise,
    exerciseState: state.getIn(['exerciseState', activeExercise]),
    pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
    pendingSend: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'send'], false),
    pendingSave: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'save'], false),
    pendingDelete: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'delete'], false),
    pendingResolve: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'resolve'], false),
  }
};

const mapDispatchToProps = dispatch => ({
  onAuditChange: (auditPk, studentPk, exercise) => {
    dispatch(setDetailResultExercise(exercise));
    dispatch(setActiveAudit(auditPk));
    dispatch(fetchStudentDetailResults(studentPk));
    dispatch(setSelectedStudentResults(studentPk));
  },
  onSendAudit: (auditPk) => dispatch(handleAuditSend(auditPk)),
  onResolveAudit: (auditPk, currentlyResolved) => dispatch(handleAuditResolve(auditPk, currentlyResolved)),
  onAddAudit: (exercise) => dispatch(fetchNewAudit(exercise)),
  onDeleteAudit: (auditPk) => dispatch(handleDeleteAudit(auditPk)),
  onPassAudit: (auditPk, studentPk, currentlyPassed) => dispatch(handleAuditPass(auditPk, studentPk, currentlyPassed)),
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

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
