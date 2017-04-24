import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';

import { 
  fetchStudentDetailResults,
  fetchNewAudit,
} from '../fetchers.js';
import { 
  setActiveAudit,
  setSelectedStudentResults,
  setDetailResultExercise,
} from '../actions.js';

import Spinner from './Spinner.jsx';
import AuditStatistics from './AuditStatistics.jsx';
import { handlePublishAndSend } from './Audit.jsx';

const renderAuditListItem = ({activeExercise, activeAudit, audit, onAuditChange, nInList, pendingStateAudits}) => {
  var activeClass = activeAudit === audit.get('pk') ? ' uk-text-bold ' : ' ';
  var statusColorType = 'unpublished'; 
  var statusColor = {
    unpublished: '#00a8e6',
    done: '#8cc14c',
    nostatus: '#faa732',
    revision: '#da314b'
  }
  if(audit.get('revision_needed') !== null)
    if(!audit.get('revision_needed'))
      statusColorType = 'done'
  else 
    statusColorType = 'revision'
  return (
    <a key={audit.get('pk')} onClick={() => onAuditChange(audit.get('pk'), audit.get('student'), activeExercise)} className={"uk-contrast uk-button uk-button-mini " + activeClass} title={audit.get('student_username')} data-uk-tooltip style={{backgroundColor: statusColor[statusColorType], textShadow: 'none'}}>
      { activeAudit === audit.get('pk') && <i className="uk-text-primary uk-icon uk-icon-caret-right uk-icon-small"/> }
      {nInList+1}
      { pendingStateAudits.getIn([audit.get('pk'), 'send']) && <Spinner size=''/> }
      { pendingStateAudits.getIn([audit.get('pk'), 'publish']) && <Spinner size=''/> }
      { (pendingStateAudits.getIn([audit.get('pk'), 'send']) === null ||  
         pendingStateAudits.getIn([audit.get('pk'), 'publish']) === null ) && <i className="uk-icon uk-icon-exclamation-triangle"/> }
      { audit.get('updated') && <i className="uk-margin-small-left uk-icon uk-icon uk-icon-envelope"/>}
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
    onPublishAndSend,
    userPk
  }, filter, onFilterChange) => {
  var auditsList = audits.filter( (audit) => audit.get('exercise') === activeExercise )
                         .filter( (audit) => audit.get('auditor') === userPk )
                         .filter( item => filter === '' || (item.get('student_username')).toLowerCase().indexOf(filter.toLowerCase()) >= 0)
                         .toList()
                         .sort( (a, b) => a.get('date') > b.get('date') );
  var nAudits = auditsList.size;

  var current = auditsList.findEntry( item => item.get('pk') === activeAudit, null, [0])[0];
  var next = current + 1 < auditsList.size ? current + 1 : current;
  var showNext = current + 1 < auditsList.size;
  var prev = current - 1 >= 0 ? current - 1 : current;
  var showPrev = current -1 >= 0;

  var auditsRenderPublished =  auditsList.filter(item => item.get('published')).map( (audit, key) => {
    return renderAuditListItem({activeExercise, activeAudit, audit, nInList: key, onAuditChange, pendingStateAudits});
  });
  var auditsUnfinished = auditsList.filter(item => !item.get('published') && item.get('revision_needed') === null);
  var auditsReady = auditsList.filter(item => !item.get('published') && item.get('revision_needed') !== null);
  var auditsRenderReady = auditsReady.map( (audit, key) => {
    return renderAuditListItem({activeExercise, activeAudit, audit, nInList: key, onAuditChange, pendingStateAudits});
  });
  var auditsRenderUnpublished = auditsUnfinished.map( (audit, key) => {
    return renderAuditListItem({activeExercise, activeAudit, audit, nInList: key, onAuditChange, pendingStateAudits});
  });
  return  (
          <div className="uk-panel uk-panel-box uk-panel-box-primary" style={{padding: '5px'}}>
            <div className="uk-float-left"><div>Audits for <a href={"#exercise/"+activeExercise} target="_blank" className="uk-button" title="Click to open exercise in a new tab">{exerciseName}</a></div><div><AuditStatistics/></div></div>
            <div className="uk-flex uk-flex-right">
            <div>
            <div className="uk-grid uk-margin-small-left uk-margin-right uk-margin-small-top">
             <div className="uk-margin-right">Published:</div>
             {auditsRenderPublished}
            </div>
            <div className="uk-grid uk-margin-small-left uk-margin-right uk-margin-small-top">
             { auditsRenderReady.size > 0 && <div className="uk-margin-small-right">Ready:</div>}
             { auditsRenderReady.size > 0 && auditsRenderReady }
             <div className="uk-margin-small-left uk-margin-small-right uk-padding-remove">Unfinished:</div>
             {auditsRenderUnpublished}
            </div>
            </div>
            <div className="uk-flex uk-flex-column">
            <button className="uk-button uk-button-primary" type="button" onClick={ () => onAddAudit(activeExercise) }>Add student { pendingNewAudit && <Spinner size="uk-icon-small"/> }</button>
            <button className={"uk-button uk-button-medium uk-margin-small-top " + (auditsRenderReady.size > 0 ? 'uk-button-success' : '')} type="button" onClick={ () => onPublishAndSend(auditsReady) } data-uk-tooltip title="Publish ready audits and send an email to students.">Publish ready ({auditsRenderReady.size})</button>
            <div className="uk-margin-small-top"><input className="uk-form-width-small uk-form-small" type="text" placeholder="Username filter" value={filter} onChange={onFilterChange}/></div>
            </div>
            </div>
          </div>);
}

class BaseAuditCompactList extends Component {
  constructor() {
    super();
    this.state = { 
      filter: ''
    }
  }
  handleFilterChange = (e) => {
    this.setState( {filter: e.target.value} );
  }
  render() {
    return renderAuditCompactList(this.props, this.state.filter, this.handleFilterChange);
  }
}

const mapStateToProps = state => {
  var activeAudit = state.getIn(['audit','activeAudit'], false);
  var auditData = state.getIn(['audit', 'auditdata', activeAudit], immutable.Map({}))
  var activeExercise = state.get('activeExercise');
  return {
    activeAudit: activeAudit,
    userPk: state.getIn(['login', 'user_pk']),
    audits: state.getIn(['audit', 'audits'], immutable.Map({})),
    activeExercise: activeExercise,
    pendingStateAudits: state.getIn(['pendingState', 'audit', 'audits'], immutable.Map({})),
    pendingNewAudit: state.getIn(['pendingState', 'audit', 'newAudit'], false),
    exerciseName: state.getIn(['exerciseState', activeExercise, 'json', 'exercise', 'exercisename', '$'], '')
  }
};

const mapDispatchToProps = dispatch => ({
  onAuditChange: (auditPk, studentPk, exercise) => {
    dispatch(setDetailResultExercise(exercise));
    dispatch(setActiveAudit(auditPk));
    dispatch(fetchStudentDetailResults(studentPk));
    dispatch(setSelectedStudentResults(studentPk));
  },
  onAddAudit: (exercise) => dispatch(fetchNewAudit(exercise)),
  onPublishAndSend: (audits) => dispatch(handlePublishAndSend(audits)),
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuditCompactList);
