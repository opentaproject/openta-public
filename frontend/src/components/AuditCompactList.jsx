import React, { Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';

import { fetchStudentDetailResults, fetchNewAudit } from '../fetchers.js';
import { setActiveAudit, setSelectedStudentResults, setDetailResultExercise } from '../actions.js';

import Spinner from './Spinner.jsx';
import AuditStatistics from './AuditStatistics.jsx';
import { handlePublishAndSend } from './Audit.jsx';
import {fetchSendMyAudits } from '../fetchers.js'

const strip_email = (email) => {
  return email.replace(/@.*/, '');
};

const renderAuditListItem = ({ activeExercise, activeAudit, audit, onAuditChange, nInList, pendingStateAudits }) => {
  var activeClass = activeAudit === audit.get('pk') ? ' uk-text-bold ' : ' ';
  var statusColorType = 'unpublished';
  var statusColor = {
    unpublished: '#00a8e6',
    done: '#8cc14c',
    nostatus: '#faa732',
    revision: '#da314b',
    nopoints: '#ffa500',
    inactive: '#666666',
    force_passed: '#CCCCCC',
    peeked: '#aaaaaa'
  };
  var statusInfo = ': Done';
  if (audit.get('revision_needed') !== null) {
    if (!audit.get('revision_needed')) {
      if (audit.get('points')) {
        statusColorType = 'done';
        statusInfo = ': Done';
      } else {
        statusColorType = 'nopoints';
        statusInfo = ': No points assigned';
      }
    } else {
      statusColorType = 'revision';
      statusInfo = ': Revision needed';
    }
  } else {
    if (localStorage.getItem(audit.get('pk'))) {
      statusInfo = ': Peeked';
      statusColorType = 'peeked';
    }
  }
  if (audit.get('message') == 'No data') {
    statusColorType = 'inactive';
    statusInfo = 'No data';
  }
  if (audit.get('force_passed')) {
    statusColorType = 'force_passed';
    statusInfo = 'Student was force_passed';
  }
  var isactive = activeAudit === audit.get('pk');
  var textsize = isactive ? ' uk-text-large ' : ' ';
  return (
    <a
      key={audit.get('pk')}
      onClick={() => onAuditChange(audit.get('pk'), audit.get('student'), activeExercise, activeAudit)}
      className={'uk-contrast uk-button uk-button-mini ' + activeClass}
      title={audit.get('student_username') + statusInfo}
      data-uk-tooltip
      style={{ backgroundColor: statusColor[statusColorType], textShadow: 'none' }}
    >
      {activeAudit === audit.get('pk') && <i className="uk-text-primary uk-icon uk-icon-caret-right uk-icon-small" />}
      {pendingStateAudits.getIn([audit.get('pk'), 'send']) && <Spinner size="" />}
      {pendingStateAudits.getIn([audit.get('pk'), 'publish']) && <Spinner size="" />}
      {(pendingStateAudits.getIn([audit.get('pk'), 'send']) === null ||
        pendingStateAudits.getIn([audit.get('pk'), 'publish']) === null) && (
        <i className="uk-icon uk-icon-exclamation-triangle" />
      )}
      {audit.get('updated') && <i className=" uk-icon uk-icon uk-icon-envelope" />}
      {<span className={textsize}>{strip_email(audit.get('student_username')) + ':' + audit.get('points', '')}</span>}
    </a>
  );
};

const renderAuditCompactList = (
  {
    activeExercise,
    exerciseName,
    activeAudit,
    audits,
    pendingStateAudits,
    pendingNewAudit,
    onAuditChange,
    onAddAudit,
    onPublishAndSend,
    userPk,
    use_email,
    onSendMyAudits,
  },
  filter,
  onFilterChange
) => {
  var auditsList = audits
    .filter((audit) => audit.get('exercise') === activeExercise)
    .filter((audit) => audit.get('auditor') === userPk)
    .filter((item) => filter === '' || item.get('student_username').toLowerCase().indexOf(filter.toLowerCase()) >= 0)
    .toList()
    .sort((a, b) => a.get('student_username').localeCompare(b.get('student_username')));

  var nAudits = auditsList.size;

  var current = auditsList.findEntry((item) => item.get('pk') === activeAudit, null, [0])[0];
  var next = current + 1 < auditsList.size ? current + 1 : current;
  var showNext = current + 1 < auditsList.size;
  var prev = current - 1 >= 0 ? current - 1 : current;
  var showPrev = current - 1 >= 0;

  var auditsRenderPublished = auditsList
    .filter((item) => item.get('published'))
    .map((audit, key) => {
      return renderAuditListItem({
        activeExercise,
        activeAudit,
        audit,
        nInList: key,
        onAuditChange,
        pendingStateAudits
      });
    });
  var auditsUnfinished = auditsList.filter((item) => !item.get('published') && item.get('revision_needed') === null);
  var auditsUnsent = auditsList.filter((item) => !item.get('sent') && item.get('published') );
  var auditsReady = auditsList.filter((item) => !item.get('published') && item.get('revision_needed') !== null);
  var auditsRenderReady = auditsReady.map((audit, key) => {
    return renderAuditListItem({ activeExercise, activeAudit, audit, nInList: key, onAuditChange, pendingStateAudits });
  });
  var auditsRenderUnpublished = auditsUnfinished.map((audit, key) => {
    return renderAuditListItem({ activeExercise, activeAudit, audit, nInList: key, onAuditChange, pendingStateAudits });
  });
  var send_tip = use_email
    ? 'Publish ready audits and send an email to students ; enable or disable in course settings'
    : 'Publish ready ; email is not activated ; enable or  disable in course settings';
  var send_info = use_email ? 'Emails will be sent ' : 'Email will not be sent';
  var use_email_class = use_email ? 'uk-button-text uk-text-success ' : 'uk-button-text uk-text-danger';
  var titleDOM = (
    <div className="uk-float-right">
      <div>
        Audits for{' '}
        <a
          href={'#exercise/' + activeExercise}
          target="_blank"
          className="uk-button"
          title="Click to open exercise in a new tab"
          rel="noreferrer"
        >
          {exerciseName}
        </a>
      </div>
    </div>
  );

  var queueDOM = (
    <div className="uk-flex uk-flex-column">
      <div className="uk-button-group">
        <button
          className="uk-button uk-button-primary uk-width-5-6 uk-text-small queue-done-student"
          type="button"
          onClick={() => onAddAudit(activeExercise, 'fromReady', 1)}
        >
          Queue student who is done {pendingNewAudit && <Spinner size="uk-icon-small" />}
        </button>
        <button
          className="uk-button uk-button-primary uk-width-1-6 uk-text-small"
          type="button"
          onClick={() => onAddAudit(activeExercise, 'fromReady', 10)}
        >
          +10
        </button>
      </div>

      <div className="uk-button-group">
        <button
          className="uk-button uk-button-primary uk-width-5-6 uk-text-small"
          type="button"
          onClick={() => onAddAudit(activeExercise, 'fromNotReady', 1)}
        >
          Queue student who is incomplete
          {pendingNewAudit && <Spinner size="uk-icon-small" />}
        </button>
        <button
          className="uk-button uk-button-primary uk-width-1-6 uk-text-small"
          type="button"
          onClick={() => onAddAudit(activeExercise, 'fromNotReady', 10)}
        >
          +10
        </button>
      </div>

      <div className="uk-button-group">
        <button
          className="uk-button uk-button-primary uk-width-5-6 uk-text-small"
          type="button"
          onClick={() => onAddAudit(activeExercise, 'fromNotActive', 1)}
        >
          Queue inactive student
          {pendingNewAudit && <Spinner size="uk-icon-small" />}
        </button>
        <button
          className="uk-button uk-button-primary uk-width-1-6 uk-text-small"
          type="button"
          onClick={() => onAddAudit(activeExercise, 'fromNotActive', 10)}
        >
          +10
        </button>
      </div>
      <div className="uk-button-group">
        <button
          className={
            'uk-button uk-button-small uk-margin-small-top ' + (auditsRenderReady.size > 0 ? 'uk-button-success' : '')
          }
          type="button"
          onClick={() => onPublishAndSend(auditsReady)}
          data-uk-tooltip
          title={send_tip}
        >
          Publish ready ({auditsRenderReady.size})
        </button>

	{ use_email && (
 	<button
          className={
            'uk-button uk-button-small uk-margin-small-top ' + (auditsUnsent.size > 0 ? 'uk-button-success' : '')
          }
          type="button"
          onClick={() => onSendMyAudits()}
          data-uk-tooltip
          title={send_tip}
        >
          Send published ({auditsUnsent.size})
        </button>
	)}



      </div>
      <div className="uk-button-group">
        <button
          className={'uk-button uk-button-small uk-margin-small-top uk-button-text ' + use_email_class}
          type="button"
          data-uk-tooltip
          title={send_tip}
        >
          {send_info}
        </button>
      </div>
    </div>
  );

  var centerDOM = (
    <div>
      <div className="uk-margin-small-top">
        {' '}
        <input
          className="uk-form-small"
          type="text"
          placeholder="Username filter"
          value={filter}
          onChange={onFilterChange}
        />{' '}
      </div>

      <div className=" uk-margin-right uk-margin-small-top" id="published-audits">
        <div className="uk-margin-right">Published:</div>
        {auditsRenderPublished}
      </div>

      <div className=" uk-margin-right uk-margin-small-top" id="unfinished-audits">
        {auditsRenderReady.size > 0 && <div className="uk-margin-small-right">Unpublished:</div>}
        {auditsRenderReady.size > 0 && auditsRenderReady}
        <div className=" uk-margin-small-right"> Queue : </div>
        {auditsRenderUnpublished}
      </div>
    </div>
  );

  return (
    <div className="uk-padding-large uk-width-1-1 uk-flex uk-flex-center">
      <table className="uk-table">
        <thead>
          <tr>
            <td colSpan="3">{titleDOM}</td>
          </tr>
        </thead>
        <tbody>
          <tr className="">
            <td className="uk-width-1-4">
              <div>
                <AuditStatistics />
              </div>
            </td>
            <td>{centerDOM}</td>
            <td className="uk-width-1-4">{queueDOM}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

class BaseAuditCompactList extends Component {
  constructor() {
    super();
    this.state = {
      filter: ''
    };
  }
  handleFilterChange = (e) => {
    this.setState({ filter: e.target.value });
  };
  render() {
    return renderAuditCompactList(this.props, this.state.filter, this.handleFilterChange);
  }
}

const mapStateToProps = (state) => {
  var activeAudit = state.getIn(['audit', 'activeAudit'], false);
  var auditData = state.getIn(['audit', 'audits', activeAudit], immutable.Map({}));
  var activeExercise = state.get('activeExercise');
  return {
    use_email: state.getIn(['course', 'use_email'], false),
    activeAudit: activeAudit,
    userPk: state.getIn(['login', 'user_pk']),
    audits: state.getIn(['audit', 'audits'], immutable.Map({})),
    activeExercise: activeExercise,
    pendingStateAudits: state.getIn(['pendingState', 'audit', 'audits'], immutable.Map({})),
    pendingNewAudit: state.getIn(['pendingState', 'audit', 'newAudit'], false),
    exerciseName: state.getIn(['exerciseState', activeExercise, 'json', 'exercise', 'exercisename', '$'], '')
  };
};

const mapDispatchToProps = (dispatch) => ({
  onAuditChange: (auditPk, studentPk, exercise, activeAudit) => {
    localStorage.setItem(auditPk, 'true');
    //if( auditPk != activeAudit ){
    //	    dispatch( handleAuditRevision( activeAudit, revision_needed) )
    //		}
    dispatch(setDetailResultExercise(exercise));
    dispatch(setActiveAudit(auditPk));
    dispatch(fetchStudentDetailResults(studentPk));
    dispatch(setSelectedStudentResults(studentPk));
  },
  onAddAudit: (exercise, heap, n_audits) => dispatch(fetchNewAudit(exercise, heap, n_audits)),
  onPublishAndSend: (audits) => dispatch(handlePublishAndSend(audits)),
  onSendMyAudits: () => dispatch(fetchSendMyAudits())
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuditCompactList);
