import React from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';


const BaseAuditStatistics = ({
  nAudits,
  nComplete,
  nTotal,
  nYourAudits,
  nNotToBeAudited,
  nUnaudited,
  nTried,
  inOverview,
  inHeapForAudit,
  notReadyForAudit,
  notActive,
}) => {
  if (inOverview) {
    var n_inOverview = inOverview.size;
    var renderinOverview = inOverview.map((item, index) => (
      <tr key={"r" + index}>
        <td className="uk-text-right">{index + 1}</td>
        <td className="uk-text-right">{item}</td>
      </tr>
    ));
  } else {
    var renderinOverview = "";
    var n_inOverview = 0;
  }
 if (notActive) {
   var n_notActive = notActive.size;
   var rendernotActive = notActive.map((item, index) =>
    <tr key={"r" + index}>
      <td className="uk-text-right">{index + 1}</td>
      <td className="uk-text-right">{item}</td>
    </tr>);
 } else {
  var rendernotActive = "";
  var n_notActive = 0;
 }


  if (inHeapForAudit) {
    var n_inHeapForAudit = inHeapForAudit.size;
    var renderinHeapForAudit = inHeapForAudit.map((item, index) => (
      <tr key={"s" + index}>
        <td className="uk-text-right">{index + 1}</td>
        <td className="uk-text-right">{item}</td>
      </tr>
    ));
  } else {
    var renderinHeapForAudit = "";
    var n_inHeapForAudit = 0;
  }
  if (notReadyForAudit) {
    var n_notReadyForAudit = notReadyForAudit.size;
    var rendernotReadyForAudit = notReadyForAudit.map((item, index) => (
      <tr key={"t" + index}>
        <td className="uk-text-right">{index + 1}</td>
        <td className="uk-text-right">{item}</td>
      </tr>
    ));
  } else {
    var rendernotReadyForAudit = "";
    var n_notReadyForAudit = 0;
  }

  return <div>
      <h3>
        {nTried} tried this problem and {nTried - n_notReadyForAudit} are eligible for audit{" "}
      </h3>
      <div className="uk-button-group">
        <span data-uk-dropdown="{mode:'click'}">
          <span className="uk-button uk-button-small uk-margin-small-top uk-button-primary" title="Click for more statistics">
            {n_inOverview} in Overview {" "}
          </span>
          <div className="uk-dropdown" style={{ width: "auto" }}>
            <table className="uk-table uk-table-condensed uk-margin-remove">
              <tbody>{renderinOverview}</tbody>
            </table>
          </div>
        </span>

        <span data-uk-dropdown="{mode:'click'}">
          <span className="uk-button uk-button-small uk-margin-small-top uk-button-primary" title="Click for more statistics">
            {n_inHeapForAudit} Ready for audit {" "}
          </span>
          <div className="uk-dropdown" style={{ width: "auto" }}>
            <table className="uk-table uk-table-condensed uk-margin-remove">
              <tbody>{renderinHeapForAudit}</tbody>
            </table>
          </div>
        </span>

        <span data-uk-dropdown="{mode:'click'}">
          <span className="uk-button uk-button-small uk-margin-small-top uk-button-primary" title="Click for more statistics">
            {n_notReadyForAudit} Students who are late or incorrect
          </span>
          <div className="uk-dropdown" style={{ width: "auto" }}>
            <table className="uk-table uk-table-condensed uk-margin-remove">
              <tbody>{rendernotReadyForAudit}</tbody>
            </table>
          </div>
        </span>

        <span data-uk-dropdown="{mode:'click'}">
          <span className="uk-button uk-button-small uk-margin-small-top uk-button-primary" title="Click for more statistics">
            {n_notActive} Students not active
          </span>
          <div className="uk-dropdown" style={{ width: "auto" }}>
            <table className="uk-table uk-table-condensed uk-margin-remove">
              <tbody>{rendernotActive}</tbody>
            </table>
          </div>
        </span>

        <span data-uk-dropdown="{mode:'click'}">
          <span className="uk-button uk-button-small uk-margin-small-top uk-button-primary" title="Click for more statistics">
            Stats
          </span>
          <div className="uk-dropdown" style={{ width: "auto" }}>
            <table className="uk-table uk-table-condensed uk-margin-remove">
              <tbody>
                <tr>
                  <td className="uk-text-right">Number of audits listed in Overview: </td>
                  <td>{n_inOverview}</td>
                </tr>
                <tr>
                  <td className="uk-text-right">Number of ready students without auditor: </td>
                  <td>{n_inHeapForAudit}</td>
                </tr>
                <tr>
                  <td className="uk-text-right">Number who are late and unaudited:</td>
                  <td>{n_notReadyForAudit}</td>
                </tr>
                <tr>
                  <td className="uk-text-right">Number of students who do not qualify for audit : </td>
                  <td>{n_notActive}</td>
                </tr>
                <tr>
                  <td className="uk-text-right" colSpan="2" />
                </tr>
                <tr>
                  <td className="uk-text-right">Number of audits that are yours:</td>
                  <td>{nYourAudits}</td>
                </tr>
                <tr>
                  <td className="uk-text-right">Total students in the course: </td>
                  <td>{nTotal}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </span>
      </div>
    </div>;
};

const mapStateToProps = (state, ownProps) => {
  const activeExercise = state.get('activeExercise');
  return {
    nAudits: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_auditees']),
    nYourAudits: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_your_audits']),
    nComplete: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_complete']),
    nUnaudited: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_unaudited']),
    nTotal: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_total']),
    nTried: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_tried']),
    nNotToBeAudited: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_not_to_be_audited']),
    inOverview: state.getIn(['exerciseState', activeExercise, 'auditStats', 'in_overview']),
    inHeapForAudit: state.getIn(['exerciseState', activeExercise, 'auditStats', 'in_heap_for_audit']),
    notReadyForAudit: state.getIn(['exerciseState', activeExercise, 'auditStats', 'not_ready_for_audit']),
    notActive: state.getIn(['exerciseState', activeExercise, 'auditStats', 'not_active']),
  };
}

const mapDispatchToProps = (dispatch, ownProps) => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuditStatistics)
