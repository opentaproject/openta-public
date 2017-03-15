import React, { PropTypes, Component } from 'react';
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


const auditRender = ({ audits, activeAudit, activeExercise, exerciseState, auditData, onAuditChange, pendingResults, onSendAudit, pendingSend, pendingSave, onMessageChange, onOldMessageClick, onAddAudit, onDeleteAudit, pendingDelete, onSubjectChange, onPublishAudit, pendingPublish, onPassAudit, onRevisionAudit, pendingRevision, onPublishAndSend, pendingStateAudits}, bccStatus, onBccClick, filter, onFilterChange) => {
  var auditsList = audits.filter( (audit) => audit.get('exercise') === activeExercise )
                         .filter( item => filter === '' || (item.get('student_username') /*+ ' ' + item.get('first_name') + ' ' + item.get('last_name')*/).toLowerCase().indexOf(filter.toLowerCase()) >= 0)
                         .toList()
                         .sort( (a, b) => a.get('date') > b.get('date') );
  var nAudits = auditsList.size;

  const renderAuditListItem = (audit, nInList) => {
    var activeClass = activeAudit === audit.get('pk') ? ' uk-text-bold ' : ' ';
    var statusColorType = 'unpublished'; 
    var statusColor = {
      unpublished: '#00a8e6',
      done: '#8cc14c',
      nostatus: '#faa732',
      revision: '#da314b'
    }
    if(audit.get('revision_needed') !== null)
      if(!audit.get('revision_needed'))
        statusColorType = 'done'
      else 
        statusColorType = 'revision'
    return (
      <a key={audit.get('pk')} onClick={() => onAuditChange(audit.get('pk'), audit.get('student'), activeExercise)} className={"uk-contrast uk-button uk-button-mini " + activeClass} title={audit.get('student_username')} data-uk-tooltip style={{backgroundColor: statusColor[statusColorType], textShadow: 'none'}}>
        { activeAudit === audit.get('pk') && <i className="uk-text-primary uk-icon uk-icon-caret-right uk-icon-small"/> }
        {nInList+1}
        { pendingStateAudits.getIn([audit.get('pk'), 'send']) && <Spinner size=''/> }
        { pendingStateAudits.getIn([audit.get('pk'), 'publish']) && <Spinner size=''/> }
        { (pendingStateAudits.getIn([audit.get('pk'), 'send']) === null ||  
          pendingStateAudits.getIn([audit.get('pk'), 'publish']) === null ) && <i className="uk-icon uk-icon-exclamation-triangle"/> }
      </a>
    );
  };
  var auditsRenderPublished =  auditsList.filter(item => item.get('published')).map( (audit, key) => {
    return renderAuditListItem(audit, key);
  });
  var auditsUnfinished = auditsList.filter(item => !item.get('published') && item.get('revision_needed') === null);
  var auditsReady = auditsList.filter(item => !item.get('published') && item.get('revision_needed') !== null);
  var auditsRenderReady = auditsReady.map( (audit, key) => {
    return renderAuditListItem(audit, key);
  });
  var auditsRenderUnpublished = auditsUnfinished.map( (audit, key) => {
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
            <div className="uk-flex uk-flex-right">
            <div>
            <div className="uk-grid uk-margin-small-left uk-margin-right uk-margin-small-top">
             <div className="uk-margin-right">Published:</div>
             {auditsRenderPublished}
            </div>
            <div className="uk-grid uk-margin-small-left uk-margin-right uk-margin-small-top">
             { auditsRenderReady.size > 0 && <div className="uk-margin-small-right">Ready:</div>}
             { auditsRenderReady.size > 0 && auditsRenderReady }
             <div className="uk-margin-small-left uk-margin-small-right uk-padding-remove">Unfinished:</div>
             {auditsRenderUnpublished}
            </div>
            </div>
            <div className="uk-flex uk-flex-column">
            <button className="uk-button uk-button-primary" type="button" onClick={ () => onAddAudit(activeExercise) }>Add student</button>
            <button className={"uk-button uk-button-medium uk-margin-small-top " + (auditsRenderReady.size > 0 ? 'uk-button-success' : '')} type="button" onClick={ () => onPublishAndSend(auditsReady) }>Publish ready ({auditsRenderReady.size})</button>
            <div className="uk-margin-small-top"><input className="uk-form-width-small uk-form-small" type="text" placeholder="Username filter" value={filter} onChange={onFilterChange}/></div>
            </div>
            <div className="uk-button-group uk-display-inline-block uk-margin-small-top">
              { /*
              <button className="uk-button" type="button" onClick={() => showPrev ? onAuditChange(auditsList.getIn([prev, 'pk']), auditsList.getIn([prev,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-left"/></button>
              <button className="uk-button" type="button" disabled>{nAudits > 0 ? (current+1) : 0} / {auditsList.size} </button>
              <button className="uk-button" type="button" onClick={() => showNext ? onAuditChange(auditsList.getIn([next, 'pk']), auditsList.getIn([next,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-right"/></button>
             */ }
            </div>
            </div>
          </div>);//}}}
  var sendClass = audits.getIn([activeAudit, 'sent']) ? 'uk-button-primary' : 'uk-button-primary';
  var sendName = audits.getIn([activeAudit, 'sent']) ? 'Resend' : 'Send';
  var publishName = audits.getIn([activeAudit, 'published']) ? 'Retract' : 'Publish';
  var publishClass = audits.getIn([activeAudit, 'published']) ? 'uk-button-primary' : 'uk-button-success';
  var revisionNeeded = audits.getIn([activeAudit, 'revision_needed']);
  var passedClass = '';
  var revisionClass = '';
  if(revisionNeeded !== null) {
    passedClass = revisionNeeded === true ? '' : 'uk-text-bold';
    revisionClass = revisionNeeded === true ? 'uk-text-bold' : '';
  }
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
                <div className="uk-flex uk-flex-middle uk-flex-wrap uk-margin-small-top">
                  <a className={"uk-button uk-margin-small-top uk-position-relative " + sendClass} onClick={() => onSendAudit(activeAudit, bccStatus)}>{sendName} 
                  { pendingSend && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  <label data-uk-tooltip title="Send copy to auditor (and you if different)"><input type="checkbox" className="uk-margin-small-right uk-margin-left" checked={bccStatus} onChange={onBccClick}/>Bcc</label>
                </div>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                <div className="uk-button-group uk-flex uk-flex-center">
                  <a className={"uk-button uk-margin-small-top uk-position-relative uk-button-success " + passedClass} onClick={() => onRevisionAudit(activeAudit, false)} data-uk-tooltip title="The student has completed all tasks and no further action is required. Unless otherwise stated this means the student has passed.">
                    Passed { audits.getIn([activeAudit, 'revision_needed']) === false && <i className="uk-icon uk-icon-check uk-icon-medium"/> }
                    { pendingRevision && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  <a className={"uk-button uk-margin-small-top uk-position-relative uk-button-danger " + revisionClass} onClick={() => onRevisionAudit(activeAudit, true)} data-uk-tooltip title="Student need to amend their answer/files.">
                    Revision needed
                    { audits.getIn([activeAudit, 'revision_needed']) === true && <i className="uk-icon uk-icon-check uk-icon-medium"/> }
                  { pendingRevision && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                </div>
              </div>
              <div className="uk-form-row uk-margin-small-top">
                <div className="uk-flex uk-flex-middle uk-flex-space-between uk-flex-wrap uk-margin-small-top">
                  { audits.getIn([activeAudit, 'revision_needed']) === null && <a className="uk-button uk-text-muted" title="Please select status before publishing." data-uk-tooltip>Publish</a> }
                  { audits.getIn([activeAudit, 'revision_needed']) !== null &&
                  <a className={"uk-button uk-margin-small-top uk-position-relative " + publishClass} onClick={() => onPublishAudit(activeAudit, audits.getIn([activeAudit, 'published']))} data-uk-tooltip title="The audit will become visible for the student.">{publishName} 
                  { pendingPublish && <Spinner size="uk-icon-small uk-position-top-right"/> }
                  </a>
                  }
                  <a className="uk-button uk-button-danger uk-margin-small-top uk-position-relative" onClick={() => onDeleteAudit(activeAudit)}>Delete
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

const handleAuditPublish = (auditPk, currentlyPublished) => dispatch => {
  dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'publish'], true));
  dispatch(updateAudit(auditPk, { published: !currentlyPublished }))
  return dispatch(handleAuditSave(auditPk))
    .then(() => dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'publish'], false)))
    .catch( err => {
      dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'publish'], null))
      dispatch(updateAudit(auditPk, { published: currentlyPublished }))
    });
}

const handlePublishAndSend = (audits) => dispatch => {
  audits.forEach( audit => {
    dispatch(handleAuditPublish(audit.get('pk'), false))
      .then(() => dispatch(handleAuditSend(audit.get('pk'))));
  });
  /**/
}

const handleAuditRevision= (auditPk, needRevision) => dispatch => {
  dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'revision'], true));
  dispatch(updateAudit(auditPk, { revision_needed: needRevision }))
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
  onAuditChange: (auditPk, studentPk, exercise) => {
    dispatch(setDetailResultExercise(exercise));
    dispatch(setActiveAudit(auditPk));
    dispatch(fetchStudentDetailResults(studentPk));
    dispatch(setSelectedStudentResults(studentPk));
  },
  onSendAudit: (auditPk, bcc) => dispatch(handleAuditSend(auditPk, bcc)),
  onPublishAudit: (auditPk, currentlyPublished) => dispatch(handleAuditPublish(auditPk, currentlyPublished)),
  onPublishAndSend: (audits) => dispatch(handlePublishAndSend(audits)),
  onRevisionAudit: (auditPk, needRevision) => dispatch(handleAuditRevision(auditPk, needRevision)),
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

class BaseAudit extends Component {
  constructor() {
    super();
    this.state = { 
      bcc: false,
      filter: ''
    }
  }
  handleFilterChange = (e) => {
    this.setState( {filter: e.target.value} );
  }
  handleBccClick = (e) => {
    this.setState( {bcc: e.target.checked} );
  }
  render() {
    return auditRender(this.props, this.state.bcc, this.handleBccClick, this.state.filter, this.handleFilterChange);
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
