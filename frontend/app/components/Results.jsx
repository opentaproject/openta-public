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

const BaseResults = ({ userResults }) => {
  var rows = userResults.map( item => (
    <tr>
      <td>item.username</td>
      <td></td>
      <td></td>
    </tr>
  ));
  return (
    <table className="uk-table">
      <caption>Results</caption>
      <thead>
        <tr>
          <th>Username</th>
          <th>First</th>
          <th>Last</th>
        </tr>
      </thead>
      <tbody>
        { rows }
      </tbody>
    </table>
  );
}

const mapStateToProps = state => ({
  userResults: state.get('studentResults')
});

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseResults)
