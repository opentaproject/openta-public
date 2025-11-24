// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import { connect } from 'react-redux';
import Exercise from './Exercise.jsx';
import AuditViewStudent from './AuditViewStudent';

const BaseStudentExercise = ({ hasAudit, hasPublishedAudit }) => (
  <div className="uk-flex uk-width-1-1 uk-flex-wrap">
    {hasPublishedAudit && <AuditViewStudent />}
    <Exercise />
  </div>
);

const mapStateToProps = (state) => {
  var activeExercise = state.get('activeExercise');
  var hasAudit = state.hasIn(['exerciseState', activeExercise, 'audit']);
  var hasPublishedAudit = state.getIn(['exerciseState', activeExercise, 'audit', 'published'], false);
  return {
    hasAudit: hasAudit,
    hasPublishedAudit: hasPublishedAudit
  };
};

export default connect(mapStateToProps)(BaseStudentExercise);
