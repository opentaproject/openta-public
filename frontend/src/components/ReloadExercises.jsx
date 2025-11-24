// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import React from 'react';
import { connect } from 'react-redux';
import { reloadExercises } from '../fetchers.js';
import {} from '../actions.js';
import Spinner from './Spinner.jsx';

import immutable from 'immutable';

const BaseReloadExercises = ({ messages, pendingReload, onPerformReload, coursePk , username}) => {
  var classDispatch = {
    error: 'uk-text-danger',
    info: 'uk-text-primary',
    warning: 'uk-text-warning',
    success: 'uk-text-success'
  };
console.log("USERNAME = ", username)
if ( 'super' != username ){
return( <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box"> Only the server server admin can reload the exercises </div>)
 } 
else {
  var rows = messages.map((item, index) => ( item.first &&  (
    <li className={classDispatch[item.first()]} key={index}>
      {' '}
      {item.last()}
    </li> )
  ));
  //var rows = messages.map( item => console.dir(item) );
  return (
    <div>
      {pendingReload && (
        <span>
          <Spinner msg={'exercisesReloading'} />
        </span>
      )}
      {!pendingReload && <span>Please review for any errors or warnings:</span>}
      {!pendingReload && <ul className="uk-list">{rows}</ul>}
      {!pendingReload && (
        <a className="uk-button" onClick={() => onPerformReload(coursePk)}>
          Perform reload
        </a>
      )}
    </div>
  );
} };

const mapStateToProps = (state) => ({
  messages: state.get('exercisesReloadMessages', immutable.List([])),
  pendingReload: state.getIn(['pendingState', 'exercisesReload'], false),
  username: state.getIn(['login', 'username']),
  coursePk: state.get('activeCourse')
});

const mapDispatchToProps = (dispatch) => ({
  onPerformReload: (coursePk) => dispatch(reloadExercises(true, coursePk))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseReloadExercises);
