import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
  setResultsFilter
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';

import immutable from 'immutable';
import moment from 'moment';

const BaseStudentResults = ({userResults, pendingResults}) => {
  var required = userResults.get('exercises', immutable.Map({})).filter( item => item.getIn(['meta', 'required'])).toList().sortBy(item => item.getIn(['meta','deadline']));
  return (
    <div className="uk-panel uk-panel-box">
      <article className="uk-article">
      <h1 className="uk-article-title">
      { !pendingResults && userResults.get('username')}
      { pendingResults && <Spinner/> }
      </h1>
      { !pendingResults &&
      <table className="uk-table">
        <thead>
          <tr>
            <th>Exercise</th>
            <th>Passed</th>
            <th>Solution</th>
          </tr>
        </thead>
        <tbody>
          { required.map( e => (
            <tr key={e.get('exercise_key')}>
              <td>{e.get('name')}</td>
              <td>
                {userResults.get('passed_exercises').findIndex( item => item.get('exercise_key') === e.get('exercise_key') ) !== -1 ? <i className="uk-icon uk-icon-check uk-text-success"/> : <i className="uk-icon uk-icon-close uk-text-danger"/> }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      }
      </article>
    </div>
  );
}

const mapStateToProps = state => ({
  userResults: state.getIn(['results', 'detailResults', state.getIn(['results', 'selectedUser'])], immutable.Map({})),
  pendingResults: state.getIn(['pendingState', 'detailedResults', state.getIn(['results', 'selectedUser'])], false),
});

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseStudentResults)
