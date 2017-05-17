import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import SafeImg from './SafeImg.jsx';
import Exercise from './Exercise.jsx';
import StudentAuditExercise from './StudentAuditExercise.jsx';
import AuditStatistics from './AuditStatistics.jsx';
import AuditResponseUpload from './AuditResponseUpload.jsx';
import Badge from './Badge';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import _ from 'lodash';

import { 
  fetchExerciseRemoteState,
  fetchStudentDetailResults,
  fetchCurrentAuditsExercise,
  fetchNewAudit,
  saveAudit,
  deleteAudit,
  sendAudit,
  updateAuditStudent,
} from '../fetchers.js';
import { 
  setActiveAudit,
  updateAudit,
  updatePendingStateIn,
  setSelectedStudentResults,
  setDetailResultExercise,
} from '../actions.js';

const BaseAuditViewStudent = ({ activeExercise, hasAuditData, auditPk, auditor, auditFiles, subject, message, revisionNeeded, currentlyUpdated, onUpdated, pendingUpdate }) => {
  var renderAuditFiles = auditFiles.map(
    auditResponse => (
      <li key={auditResponse.get('id')}>
      <div className="exercise-thumb-wrap" >
      { auditResponse.get('filetype') === 'IMG' &&
      <a href={SUBPATH + "/auditresponsefile/view/" + auditResponse.get('id')} data-uk-lightbox data-lightbox-type="image">
      <SafeImg src={SUBPATH + "/auditresponsefile/view/" + auditResponse.get('id') + "/thumb"}><i className="uk-icon uk-icon-large uk-icon-question"/></SafeImg>
      </a>
      }
      { auditResponse.get('filetype') === 'PDF' &&
      <a href={SUBPATH + "/auditresponsefile/view/" + auditResponse.get('id')} target="_blank">
      <i className="uk-icon uk-icon-large uk-icon-file-pdf-o"/>
      </a>
      }
      </div>
      </li>
    ));
  if(hasAuditData)
    return (
        <div className="uk-block uk-block-primary uk-width-1-1 uk-contrast uk-margin-small-left uk-padding-bottom-remove">
            <div className="uk-container">
                <div className="uk-flex uk-margin-bottom">
                    <div className="uk-width-2-3">
                        <div className="uk-flex">
                            <div>
                                <h3 className="uk-margin-small-bottom">
                                    Granskning
                                    { !revisionNeeded && <Badge type="success" className="uk-margin-left"><i className="uk-icon uk-icon-medium uk-icon-check" /><span id="revision-not-needed"/> Godkänd.</Badge> }
                                    { revisionNeeded && <Badge type="error" className="uk-margin-left" ><span id="revision-needed"/>Uppdatering krävs.</Badge> }
                                </h3>
                                <div className="uk-text-small">
                                    Granskad av <a href={"mailto:" + auditor.get('email')} className="uk-text-bold uk-contrast">{auditor.get('first_name')} {auditor.get('last_name')}</a>
                                </div>
                            </div>
        { revisionNeeded &&
          <div className="uk-margin-left uk-flex uk-flex-column">
            <div>
            <a className="uk-button" data-uk-tooltip title="Klicka här när du uppdaterat din lösning." onClick={e => onUpdated(activeExercise, auditPk, !currentlyUpdated)} id="revision-update">Uppdaterad
            { !currentlyUpdated && <i className="uk-margin-small-left uk-icon uk-icon-small uk-icon-square-o"/>}
            { currentlyUpdated && <i className="uk-text-success uk-margin-small-left uk-icon uk-icon-small uk-icon-check-square-o"/>}
            { pendingUpdate && <Spinner size="uk-icon-small"/>}
            </a>
            </div>
            { currentlyUpdated && <div><span className="uk-text-small" id="revision-updated">(Granskare uppmärksammad)</span></div>}
            </div>
        }
                        </div>
                        <hr/>
                        <h4>{subject}</h4>
                        <div id="audit-message">{message}</div>
                    </div>
                    { renderAuditFiles.size > 0 && 
                      <div className="uk-margin-left">
                          <h3>Filer</h3>
                          <ul className="uk-subnav uk-subnav-line">
                              {renderAuditFiles}
                          </ul>
                      </div>
                    }
                </div>
                <div className="uk-width-1-1">
                </div>
            </div>
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
        auditPk: auditData.get('pk'),
        activeExercise: activeExercise,
        exerciseState: state.getIn(['exerciseState', activeExercise]),
        auditFiles: auditData.get('responsefiles'),
        auditor: auditData.get('auditor_data'),
        message: auditData.get('message'),
        subject: auditData.get('subject'),
        revisionNeeded: auditData.get('revision_needed'),
        currentlyUpdated: auditData.get('updated'),
        pendingUpdate: state.getIn(['pendingState', 'audit', 'audits', auditData.get('pk'), 'updateStudent']),
    }
};

const mapDispatchToProps = dispatch => {
    return {
        onUpdated: (exercise, auditPk, updated) => {
            dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'updateStudent'], true))
            dispatch(updateAuditStudent(auditPk, updated))
                .then(json => {
                    if(!json.error){
                        dispatch(fetchExerciseRemoteState(exercise));
                    }
                    dispatch(updatePendingStateIn( ['audit', 'audits', auditPk, 'updateStudent'], false))
                })
        }
    }
}
export default connect(mapStateToProps, mapDispatchToProps)(BaseAuditViewStudent);
