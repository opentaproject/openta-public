import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Table from './Table.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import { menuPositionAt, menuPositionUnder } from '../menu.js';

const BaseAuditOverview = ({menuPath, audits,
                     }) => {
  var renderAudits = audits
    .map( audit => (immutable.Map({
      'username': audit.get('student_username'),
      'pk': audit.get('pk'),
    })));

  var tableFields = [
    {
      name: 'Username',
      index: 'username',
      type: 'string',
    },
    {
      name: 'Pk',
      index: 'pk'
    },
  ];

  return (
    <div className="uk-margin-left uk-margin-top uk-width-1-1">
      <div className="uk-flex uk-flex-wrap uk-width-1-1">
        <div className="uk-width-1-1 uk-text-center">
          <h1>
            { pendingAudits && <Spinner size="uk-icon"/> }
          </h1>
        </div>
        { menuPositionUnder(menuPath, ['audit']) && 
          <div className="uk-scrollable-box uk-margin-bottom" style={{height:'70vh'}}><Table tableId='auditOverview' data={renderAudits} fields={tableFields} keyIndex={'pk'} onItem={(id) => onAuditClick(id)}/></div>
        }
      </div>
    </div>
  );
}

function handleAuditClick(auditPk) {
  return dispatch => {
  }
}

const mapStateToProps = state => ({
  menuPath: state.getIn(['menuPath']),
  audits: state.getIn(['audit', 'audits']),
});

const mapDispatchToProps = dispatch => ({
  onAuditClick: (auditPk) => dispatch(handleAuditClick(auditPk))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseAuditOverview)
