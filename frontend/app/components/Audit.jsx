import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import Image from './Image.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

import { fetchAuditData } from '../fetchers.js';
import { setActiveAudit } from '../actions.js';

const BaseAudit = ({ audits, activeAudit, activeExercise, auditData, onAuditChange }) => {
  var auditsRender = audits.filter( (audit) => audit.get('exercise') === activeExercise )
                           .sort( (a, b) => a.get('date') > b.get('date') )
                            .map( (audit, key) => {
    var liClass = activeAudit === audit.get('pk') ? 'uk-active' : '';
    return (
    <li className={liClass} key={audit.get('pk')}>
      <a onClick={() => onAuditChange(audit.get('pk'))}>
        {key}
      </a>
    </li>
  );
  }).toArray();
  var first = auditData.get('image_answers', immutable.List([])).first();
  var src = first && "/"+SUBPATH+"imageanswer/"+first;
  return (
    <div className="uk-flex uk-flex-wrap">
      <div className="uk-width-1-1">
      <ul className="uk-subnav uk-subnav-line">
       {auditsRender}
      </ul>
      </div>
      <div className="uk-width-1-1">
      <Image src={src}/>
      </div>
    </div>
  );
}

const mapStateToProps = state => {
  var activeAudit = state.getIn(['audit','activeAudit']);
  var pendingState = state.getIn(['pendingState','exercise',state.get('activeExercise')], immutable.Map({}));
  var auditData = state.getIn(['audit', 'auditdata', activeAudit], immutable.Map({}))
  var activeExercise = state.get('activeExercise');
  return {
    audits: state.getIn(['audit', 'audits'], immutable.Map({})),
    auditData: auditData,
    activeAudit: activeAudit,
    activeExercise: activeExercise
  }
};

const mapDispatchToProps = dispatch => ({
  onAuditChange: (pk) => dispatch(fetchAuditData(pk)).then(dispatch(setActiveAudit(pk)))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAudit);
