import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

import { 
  fetchStudentDetailResults,
  saveAudit,
} from '../fetchers.js';
import { 
  setActiveAudit,
  updateAudit,
  setSelectedStudentResults,
  setDetailResultExercise,
} from '../actions.js';

const BaseAudit = ({ audits, activeAudit, activeExercise, auditData, onAuditChange, pendingResults, saveAudit, onMessageChange }) => {
  var auditsRender = audits.filter( (audit) => audit.get('exercise') === activeExercise )
                           .sort( (a, b) => a.get('date') > b.get('date') )
                            .map( (audit, key) => {
    var liClass = activeAudit === audit.get('pk') ? 'uk-active' : '';
    return (
    <li className={liClass} key={audit.get('pk')}>
      <a onClick={() => onAuditChange(audit.get('pk'), audit.get('student'), activeExercise)}>
        {key}
      </a>
    </li>
  );
  }).toArray();
  return (
    <div className="uk-flex uk-flex-wrap">
      <div className="uk-width-1-1">
        <div className="uk-panel uk-panel-box">
          <div className="uk-panel uk-panel-box uk-panel-box-primary">
            <div className="uk-button-group uk-display-inline-block">
              <button className="uk-button" type="button" onClick={() => 0}><i className="uk-icon uk-icon-chevron-left"/></button>
              <button className="uk-button" type="button" disabled>{audits.findEntry( item => item.get('pk') === activeAudit, null, [0])[0]}</button>
              <button className="uk-button" type="button" onClick={() => 0}><i className="uk-icon uk-icon-chevron-right"/></button>
            </div>
            <ul className="uk-subnav uk-subnav-line uk-display-inline-block uk-margin-left">
             {auditsRender}
            </ul>
            { activeAudit &&
            <form className="uk-form">
              <div className="uk-form-row">
                <textarea className="uk-width-1-1" onChange={e => onMessageChange(e, activeAudit)} value={audits.getIn([activeAudit, 'message'],'')}></textarea>
              </div>
              <div className="uk-form-row">
                <a className="uk-button uk-button-success" onClick={() => saveAudit(activeAudit)}>Save</a>
              </div>
            </form>
            }
          </div>
          <div className="uk-width-1-1 uk-margin-top">
          { !pendingResults && activeAudit && <StudentAuditExercise anonymous={true}/> }
          { pendingResults && <Spinner/> }
          </div>
        </div>
      </div>
    </div>
  );
}

const handleAuditSave = (auditPk) => (dispatch, getState) => {
  var state = getState();
  if(state.hasIn(['audit', 'audits', auditPk])) {
    var auditData = state.getIn(['audit', 'audits', auditPk]).toJS();
    dispatch(saveAudit(auditPk, auditData));
  } else {
    console.log('No audit with that pk populated');
  }

}

const mapStateToProps = state => {
  var activeAudit = state.getIn(['audit','activeAudit'], false);
  var auditData = state.getIn(['audit', 'auditdata', activeAudit], immutable.Map({}))
  var activeExercise = state.get('activeExercise');
  return {
    audits: state.getIn(['audit', 'audits'], immutable.Map({})),
    auditData: auditData,
    activeAudit: activeAudit,
    activeExercise: activeExercise,
    pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
  }
};

const mapDispatchToProps = dispatch => ({
  onAuditChange: (auditPk, studentPk, exercise) => {
    dispatch(setDetailResultExercise(exercise));
    dispatch(setActiveAudit(auditPk));
    dispatch(fetchStudentDetailResults(studentPk));
    dispatch(setSelectedStudentResults(studentPk));
  },
  saveAudit: (auditPk) => dispatch(handleAuditSave(auditPk)),
  onMessageChange: (e, pk) => dispatch(updateAudit(pk, {'message': e.target.value}))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
