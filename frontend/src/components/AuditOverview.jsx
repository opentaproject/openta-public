import React from 'react';
import { connect } from 'react-redux';
import { fetchStudentDetailResults } from '../fetchers.js';
import { setActiveAudit, setDetailResultExercise, setSelectedStudentResults } from '../actions.js';
import Spinner from './Spinner.jsx';
import Table from './Table.jsx';
import Audit from './Audit.jsx';

import immutable from 'immutable';
import moment from 'moment';
import { menuPositionUnder } from '../menu.js';

const trimMessage = (msg) => {
  return msg.length > 50 ? msg.substring(0, 50) + '...' : msg;
};

const BaseAuditOverview = ({
  menuPath,
  audits,
  pendingAudits,
  onAuditClick,
  activeAudit,
  activeExercise,
  exerciseName
}) => {
  var renderAudits = audits
    .map((audit) =>
      immutable.Map({
        username: audit.get('student_username'),
        pk: audit.get('pk'),
        auditor:
          '[' +
          audit.getIn(['auditor'], '') +
          '] ' +
          audit.getIn(['auditor_data', 'first_name']) +
          ' ' +
          audit.getIn(['auditor_data', 'last_name']),
        //'auditor_data': audit.getIn(['auditor_data', 'first_name']) + ' ' + audit.getIn(['auditor_data', 'last_name']),
        passed: !audit.get('revision_needed') ? 'Yes' : 'No',
        published: audit.get('published') ? 'Yes' : 'No',
        points: audit.get('points', ''),
        force_passed: audit.get('force_passed') ? 'Yes' : 'No',
        message: trimMessage(audit.get('message', '')),
        date: moment(audit.get('date')).format('YYYY-MM-DD HH:mm'),
        sent: audit.getIn(['sent'], '') ? 'Yes' : 'No'
      })
    )
    .toList();

  var tableFields = [
    {
      name: 'Student',
      index: 'username',
      classname: ''
    },
    {
      name: 'Auditor',
      index: 'auditor',
      classname: ''
    },

    //{
    //  name: 'Auditor_Data',
    //  index: 'auditor_data',
    //  classname: ''
    //},

    {
      name: '----Date----',
      index: 'date',
      classname: ''
    },

    {
      name: 'Final',
      index: 'passed',
      classname: ''
    },
    {
      name: 'Published',
      index: 'published',
      classname: ''
    },
    {
      name: 'Points',
      index: 'points',
      classname: ''
    },

    {
      name: 'ForcePass',
      index: 'force_passed',
      classname: ''
    },
    {
      name: 'emailed',
      index: 'sent',
      classname: ''
    },
    {
      name: ' --------------------------- Message ---------------------------',
      index: 'message',
      classname: 'uk-width uk-width-1-3'
    }
  ];
  return (
    <div className="uk-margin-left uk-margin-top uk-width-1-1">
      <div className="uk-flex uk-flex-wrap uk-width-1-1">
        <div>
          <h2>All audits for {exerciseName}</h2>
        </div>
        <div className="uk-width-1-1 uk-text-center">
          <h1>{pendingAudits && <Spinner size="uk-icon" />}</h1>
        </div>
        {menuPositionUnder(menuPath, ['activeExercise', 'audit', 'overview']) && (
          <div className="uk-width-1-1 uk-scrollable-box uk-margin-bottom" style={{ height: '70vh' }}>
            <Table
              tableId="auditOverview"
              data={renderAudits}
              fields={tableFields}
              keyIndex={'pk'}
              onItem={(id) => onAuditClick(activeExercise, id)}
              activeItem={activeAudit}
            />
          </div>
        )}
        {activeAudit && <Audit />}
      </div>
    </div>
  );
};

function handleAuditClick(exercise, auditPk) {
  return (dispatch, getState) => {
    const state = getState();
    const studentPk = state.getIn(['audit', 'audits', auditPk, 'student']);
    dispatch(setDetailResultExercise(exercise));
    dispatch(fetchStudentDetailResults(studentPk));
    dispatch(setSelectedStudentResults(studentPk));
    dispatch(setActiveAudit(auditPk));
  };
}

const mapStateToProps = (state) => ({
  menuPath: state.getIn(['menuPath']),
  audits: state.getIn(['audit', 'audits'], immutable.List([])),
  activeAudit: state.getIn(['audit', 'activeAudit'], false),
  activeExercise: state.get('activeExercise'),
  exerciseName: state.getIn(
    ['exerciseState', state.get('activeExercise'), 'json', 'exercise', 'exercisename', '$'],
    ''
  ),
  pendingAudits: state.getIn(['pendingState', 'audit', 'fetchAudits'])
});

const mapDispatchToProps = (dispatch) => ({
  onAuditClick: (exercise, auditPk) => dispatch(handleAuditClick(exercise, auditPk))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuditOverview);
