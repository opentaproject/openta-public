import React, { PropTypes } from 'react';
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

const BaseAuditStatistics = ({ nAudits, nComplete, nTotal, nYourAudits, nUnaudited }) => {
  return (
    <span data-uk-dropdown="{mode:'click'}">
    <span className="uk-button uk-button-small uk-margin-small-top uk-button-primary" title="Click for more statistics">{nUnaudited} unaudited</span>
    <div className="uk-dropdown" style={{width: 'auto'}}>
      <table className="uk-table uk-table-condensed uk-margin-remove">
        <tbody>
          <tr><td className="uk-text-right">Your audits:</td><td>{nYourAudits}</td></tr>
          <tr><td className="uk-text-right">Unaudited: </td><td>{nUnaudited}</td></tr>
          <tr><td className="uk-text-right">Completed students:</td><td>{nComplete}</td></tr>
          <tr><td className="uk-text-right">Total students: </td><td>{nTotal}</td></tr>
        </tbody>
      </table>
    </div>
    </span>
  );
}

const mapStateToProps = (state, ownProps) => {
  const activeExercise = state.get('activeExercise');
  return {
    nAudits: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_auditees']),
    nYourAudits: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_your_audits']),
    nComplete: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_complete']),
    nUnaudited: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_unaudited']),
    nTotal: state.getIn(['exerciseState', activeExercise, 'auditStats', 'n_total'])
  };
}

const mapDispatchToProps = (dispatch, ownProps) => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuditStatistics)
