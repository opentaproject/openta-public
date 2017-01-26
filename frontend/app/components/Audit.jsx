import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import _ from 'lodash';

import { 
  fetchStudentDetailResults,
  fetchNewAudit,
  saveAudit,
} from '../fetchers.js';
import { 
  setActiveAudit,
  updateAudit,
  setSelectedStudentResults,
  setDetailResultExercise,
} from '../actions.js';

const BaseAudit = ({ audits, activeAudit, activeExercise, auditData, onAuditChange, pendingResults, onSaveAudit, onMessageChange, onAddAudit}) => {
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
  return (
    <div className="uk-flex uk-flex-wrap uk-margin-top">
      <div className="uk-width-1-1">
        <div className="uk-panel uk-panel-box">
          <div className="uk-panel uk-panel-box uk-panel-box-primary">
            <div className="uk-button-group uk-display-inline-block">
              <button className="uk-button" type="button" onClick={ () => onAddAudit(activeExercise) }>Add audit</button>
              <button className="uk-button" type="button" onClick={() => showPrev ? onAuditChange(auditsList.getIn([prev, 'pk']), auditsList.getIn([prev,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-left"/></button>
              <button className="uk-button" type="button" disabled>{nAudits > 0 ? (current+1) : 0} / {auditsList.size} </button>
              <button className="uk-button" type="button" onClick={() => showNext ? onAuditChange(auditsList.getIn([next, 'pk']), auditsList.getIn([next,'student']), activeExercise) : 0}><i className="uk-icon uk-icon-chevron-right"/></button>
            </div>
            <div className="uk-grid uk-margin-left uk-margin-small-top">
             {auditsRender}
            </div>
            { activeAudit && audits.getIn([activeAudit, 'exercise']) == activeExercise &&
            <form className="uk-form">
              <div className="uk-form-row">
                <textarea className="uk-width-1-1" onChange={e => onMessageChange(e, activeAudit)} value={audits.getIn([activeAudit, 'message'],'')}></textarea>
              </div>
              <div className="uk-form-row">
                <a className="uk-button uk-button-success" onClick={() => onSaveAudit(activeAudit)}>Save</a>
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
  }
};

const mapDispatchToProps = dispatch => ({
  onAuditChange: (auditPk, studentPk, exercise) => {
    dispatch(setDetailResultExercise(exercise));
    dispatch(setActiveAudit(auditPk));
    dispatch(fetchStudentDetailResults(studentPk));
    dispatch(setSelectedStudentResults(studentPk));
  },
  onSaveAudit: (auditPk) => dispatch(handleAuditSave(auditPk)),
  onAddAudit: (exercise) => dispatch(fetchNewAudit(exercise)),
  onMessageChange: (e, pk) =>  {
    dispatch(updateAudit(pk, {'message': e.target.value}))
    throttleSave(dispatch, pk);
  },
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
