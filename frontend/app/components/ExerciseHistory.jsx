import React, { PropTypes, Component } from 'react';
import { connect } from 'react-redux';
import immutable from 'immutable';
import Spinner from './Spinner.jsx';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import _ from 'lodash';
import {
  updatePendingStateIn,
  fetchExerciseHistoryList,
  fetchExerciseXMLHistory,
} from '../fetchers.js';

import {
  setExerciseModifiedState
} from '../actions.js';

class BaseExerciseHistory extends Component {
  constructor() {
    super();
    this.state = { 
    }
  }


  renderItem = (item) => {
    const timeAgo = moment.utc(1000*item.get('modified')).fromNow();
    return (
      <tr key={item.get('filename')} onClick={() => this.props.onItemClick(this.props.exercise, item.get('filename'))}>
        <td className="uk-text-small"> {item.get('filename')} </td>
        <td> { timeAgo } </td>
      </tr>
    )
  }

  render() {
    const items = this.props.history.sort( (a,b) => b.get('modified') - a.get('modified')).map(this.renderItem);
    return (
      <div data-uk-dropdown="{mode:'click'}">
        <span className="uk-button uk-button-small uk-button-success" title="Snapshot history of XML" data-uk-tooltip onClick={() => this.props.onHistory(this.props.exercise)}>History</span>
        <div className="uk-dropdown" style={{width: 'auto'}}>
          { items.size == 0 &&
            <span>Empty</span>
          }
          <table className="uk-table uk-table-condensed uk-margin-remove uk-table-hover">
            <tbody>
              {items}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
}

const handleItemClick = (exercise, name) => dispatch => {
  return dispatch(fetchExerciseXMLHistory(exercise, name))
  .then(() => dispatch(setExerciseModifiedState(exercise, true)));
}

const mapDispatchToProps = dispatch => {
  return {
    onHistory: (exercise) => dispatch(fetchExerciseHistoryList(exercise)),
    onItemClick: (exercise, name) => dispatch(handleItemClick(exercise, name))
  }
}

const mapStateToProps = (state) => {
  const activeExercise = state.get('activeExercise');
  return {
    exercise: activeExercise,
    history: state.getIn(['exerciseState', activeExercise, 'history'], immutable.List([]))
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseExerciseHistory);
