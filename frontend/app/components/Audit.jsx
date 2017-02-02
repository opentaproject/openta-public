import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import Exercise from './Exercise.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
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

const BaseAudit = ({ audits, activeAudit, activeExercise, auditData, onAuditChange, pendingResults, onSendAudit, pendingSave, onMessageChange, onOldMessageClick, onAddAudit, onDeleteAudit, pendingDelete, onSubjectChange}) => {
  var auditsList = audits.filter( (audit) => audit.get('exercise') === activeExercise )
                         .toList()
                         .sort( (a, b) => a.get('date') > b.get('date') );
  var nAudits = auditsList.size;
  var auditsRender =  auditsList.map( (audit, key) => {
    var activeClass = activeAudit === audit.get('pk') ? 'uk-active uk-button-primary' : '';
    var sentClass = audit.get('sent') ? ' uk-button-success' : '';
    return (
      <a key={audit.get('pk')} onClick={() => onAuditChange(audit.get('pk'), audit.get('student'), activeExercise)} className={"uk-button uk-button-mini " + activeClass + sentClass}>{key+1}</a>
    );
  });
  var current = auditsList.findEntry( item => item.get('pk') === activeAudit, null, [0])[0];
  var next = current + 1 < auditsList.size ? current + 1 : current;
  var showNext = current + 1 < auditsList.size;
  var prev = current - 1 >= 0 ? current - 1 : current;
  var showPrev = current -1 >= 0;
  var auditList = //{{{
    (
          <div className="uk-panel uk-panel-box uk-panel-box-primary" style={{padding: '5px'}}>
            <div className="uk-flex uk-flex-wrap">
            <div className="uk-button-group uk-display-inline-block">
              <button className="uk-button" type="button" onClick={ () => onAddAudit(activeExercise) }>Add audit</button>
              <button className="uk-button" type="button" onClick={() => showPrev ? onAuditChange(auditsList.getIn([prev, 'pk']), auditsList.getIn([prev,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-left"/></button>
              <button className="uk-button" type="button" disabled>{nAudits > 0 ? (current+1) : 0} / {auditsList.size} </button>
              <button className="uk-button" type="button" onClick={() => showNext ? onAuditChange(auditsList.getIn([next, 'pk']), auditsList.getIn([next,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-right"/></button>
            </div>
            <div className="uk-grid uk-margin-left uk-margin-small-top">
             {auditsRender}
            </div>
            </div>
          </div>);//}}}
  var sendClass = audits.getIn([activeAudit, 'sent']) ? 'uk-button-success' : 'uk-button-primary';
  var sendName = audits.getIn([activeAudit, 'sent']) ? 'Resend' : 'Send';
  var auditMessage = activeAudit && audits.getIn([activeAudit, 'exercise']) == activeExercise && //{{{
          (<div className="uk-panel uk-panel-box uk-panel-box-primary">
            <form className="uk-form">
              <div className="uk-form-row">
                <input type="text" className="uk-width-1-1 uk-form-small" value={audits.getIn([activeAudit, 'subject'])} onChange={e => onSubjectChange(e, activeAudit)}/>
              </div>
              <div className="uk-form-row">
                <textarea className="uk-width-1-1" rows="5" onChange={e => onMessageChange(e, activeAudit)} value={audits.getIn([activeAudit, 'message'],'')}></textarea>
              </div>
              <div className="uk-form-row">
                <a className={"uk-button " + sendClass} onClick={() => onSendAudit(activeAudit)}>{sendName} 
                { pendingSave && <Spinner size="uk-icon-small"/> }
                </a>
                <a className="uk-button uk-button-danger uk-float-right" onClick={() => onDeleteAudit(activeAudit)}>Delete
                { pendingDelete && <Spinner size="uk-icon-small"/> }
                </a>
              </div>
            </form>
            </div>
            );//}}}
  var previousMessages = activeAudit && 
    (
      <div className="uk-panel uk-panel-box uk-margin-small-top">
      <h3 className="uk-panel-title">Other messages</h3>
      <table className="uk-table uk-table-hover">
      <tbody>
      { auditsList.filter( audit => /*audit.get('sent') &&*/ audit.get('message','').length > 0)
      .map( audit => (
        <tr key={audit.get('pk')} onClick={() => onOldMessageClick(activeAudit, audit.get('message'))}>
          <td>{ audit.get('message') }</td>
        </tr>
      )) }
      </tbody>
      </table>
      </div>
    );
  return (
      <div className="uk-width-1-1 uk-margin-top">
        <div className="uk-panel uk-panel-box">
          <div className="uk-flex uk-flex-column">
            <div className="uk-width-1-1">{auditList}</div>
            <div className="uk-flex">
              <div className="uk-width-2-10">
                <Exercise/>
              </div>
              { audits.getIn([activeAudit, 'exercise']) == activeExercise &&
              <div className="uk-width-6-10 uk-margin-top">
                { !pendingResults && activeAudit  && <StudentAuditExercise anonymous={true}/> }
                { pendingResults && <Spinner/> }
              </div>
              }
              { audits.getIn([activeAudit, 'exercise']) == activeExercise &&
              <div className="uk-width-2-10 uk-margin-top uk-margin-small-left">
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
    console.log("Updated message");
    return dispatch(updateAudit(auditPk, { message: msg }));
}

const handleAuditSave = (auditPk) => (dispatch, getState) => {
  var state = getState();
  if(state.hasIn(['audit', 'audits', auditPk])) {
    var auditData = state.getIn(['audit', 'audits', auditPk]).toJS();
    return dispatch(saveAudit(auditPk, auditData));
  } else {
    console.log('No audit with that pk populated');
  }
}

const handleAuditSend = (auditPk) => dispatch => {
   dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], true))
   dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(sendAudit(auditPk)))
    .then( res => dispatch(updateAudit(auditPk, { sent: 'success' in res })))
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], false)))
    .catch( err => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'send'], false)));
}

const handleDeleteAudit = (auditPk) => dispatch => {
   dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'delete'], true))
   dispatch(deleteAudit(auditPk))
    .then(json => {
      if('success' in json)
        return json;
      else
        throw "Delete failed";
    })
    .then( () => console.log('Before fetch audits') )
    .then( () => dispatch(fetchCurrentAuditsExercise()) )
    .then( () => console.log('After fetch audits') )
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
    pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
    pendingSave: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'send'], false),
    pendingDelete: state.getIn(['pendingState', 'audit', 'audits', activeAudit, 'delete'], false),
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
  onAddAudit: (exercise) => dispatch(fetchNewAudit(exercise)),
  onDeleteAudit: (auditPk) => dispatch(handleDeleteAudit(auditPk)),
  onMessageChange: (e, pk) =>  {
    dispatch(updateAudit(pk, {'message': e.target.value}))
    throttleSave(dispatch, pk);
  },
  onSubjectChange: (e, pk) =>  {
    dispatch(updateAudit(pk, {'subject': e.target.value}))
    throttleSave(dispatch, pk);
  },
  onOldMessageClick: (audit, msg) => dispatch(handleOldMessageClick(audit, msg)),
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
