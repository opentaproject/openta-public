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

const BaseAuditViewStudent = ({ hasAuditData, auditor, auditFiles, subject, message, resolved }) => {
  if(hasAuditData)
    return (
    <div className="uk-panel uk-panel-box uk-panel-box-primary uk-margin uk-margin-left uk-margin-right">
      <article className="uk-comment">
        <header className="uk-comment-header">
            <h4 className="uk-comment-title">{auditor.get('first_name')} {auditor.get('last_name')}</h4>
            <div className="uk-comment-meta">{/*moment(auditDate).format("YY")*/}</div>
        </header>
        <div className="uk-comment-body">...</div>
      </article>
    </div>
    );
  return (<span/>);
}

const mapStateToProps = state => {
  var activeExercise = state.get('activeExercise');
  var auditData = state.getIn(['exerciseState', activeExercise, 'audit'], immutable.Map({}));
  var hasAuditData = state.hasIn(['exerciseState', activeExercise, 'audit']);

  return {
    hasAuditData: hasAuditData,
    activeExercise: activeExercise,
    exerciseState: state.getIn(['exerciseState', activeExercise]),
    auditFiles: auditData.get('responsefiles'),
    auditor: auditData.get('auditor_data'),
    message: auditData.get('message'),
    subject: auditData.get('subject'),
    resolved: auditData.get('resolved'),
  }
};

export default connect(mapStateToProps)(BaseAuditViewStudent);
