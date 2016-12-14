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

const BaseReloadExercises = ({ messages, pendingReload }) => {
  var classDispatch = {
    error: 'uk-text-danger',
    info: 'uk-text-primary',
    warning: 'uk-text-warning',
    success: 'uk-text-success',
  };
  var rows = messages.map( (item, index) => (
    <li className={classDispatch[item.first()]} key={index}> {item.last()}</li>
  ));
  //var rows = messages.map( item => console.dir(item) );
  return (
    <div>
    { pendingReload && <span>Reloading exercises...<Spinner/></span> }
    { !pendingReload && <span>Reload finished, please review the messages for any errors or warnings:</span> } 
    <ul className="uk-list">
        { rows }
    </ul>
    </div>
  );
}

const mapStateToProps = state => ({
  messages: state.get('exercisesReloadMessages', immutable.List([])),
  pendingReload: state.getIn(['pendingState', 'exercisesReload'], false),
});

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseReloadExercises)
