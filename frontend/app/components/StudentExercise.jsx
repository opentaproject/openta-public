import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import Exercise from './Exercise.jsx';
import AuditViewStudent from './AuditViewStudent';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

const BaseStudentExercise = ({ hasAudit, hasPublishedAudit }) => (
  <div className="uk-flex uk-width-1-1 uk-flex-wrap">
    { hasPublishedAudit && <AuditViewStudent/> }
    <Exercise/>
  </div>
);

const mapStateToProps = state => {
  var activeExercise = state.get('activeExercise');
  var hasAudit = state.hasIn(['exerciseState', activeExercise, 'audit']);
  var hasPublishedAudit = state.getIn(['exerciseState', activeExercise, 'audit', 'published'], false);
  return {
    hasAudit: hasAudit,
    hasPublishedAudit: hasPublishedAudit,
  }
};

export default connect(mapStateToProps)(BaseStudentExercise);
