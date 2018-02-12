import React from 'react';
import { connect } from 'react-redux';
import {
    reloadExercises
} from '../fetchers.js';
import {
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

const BaseReloadExercises = ({ messages, pendingReload, onPerformReload, coursePk }) => {
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
    { pendingReload && <span><Spinner/></span> }
    { !pendingReload && <span>Please review for any errors or warnings:</span> } 
    { !pendingReload &&
    <ul className="uk-list">
        { rows }
    </ul>
    }
    { !pendingReload &&
    <a className="uk-button" onClick={() => onPerformReload(coursePk)}>Perform reload</a>
    }
    </div>
  );
}

const mapStateToProps = state => ({
  messages: state.get('exercisesReloadMessages', immutable.List([])),
  pendingReload: state.getIn(['pendingState', 'exercisesReload'], false),
  coursePk: state.get('activeCourse')
});

const mapDispatchToProps = dispatch => ({
    onPerformReload: (coursePk) => dispatch(reloadExercises(true, coursePk))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseReloadExercises)
