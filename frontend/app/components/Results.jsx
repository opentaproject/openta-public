import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Plot from './Plot.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';

const BaseResults = ({ userResults, pendingResults }) => {
  var rows = userResults.map( item => (
    <tr>
      <td>{item.username}</td>
      <td>{item.first_name} {item.last_name}</td>
      <td>{item.n_passed_required}</td>
      <td>{item.n_passed_bonus}</td>
    </tr>
  ));
  var requiredHistogram = userResults.map( item => item.n_passed_required );
  var bonusHistogram = userResults.map( item => item.n_passed_bonus );
  var plotData = [ {
    x: requiredHistogram,
    //opacity: 0.5,
    name: 'Obligatory',
    type: 'histogram',
  },
  {
    x: bonusHistogram,
    //opacity: 0.5,
    name: 'Bonus',
    type: 'histogram',
  }
  ];
  var layout = {
  //bargap: 0.05, 
  bargroupgap: 0.2, 
  barmode: "group", 
  title: "Students result overview", 
  xaxis: {
    title: "Number of exercises",
    tickmode: "linear",
    dtick: 1
  }, 
  yaxis: {title: "Number of students"}
};
  return (
    <div>
    { pendingResults && <span>Collecting results...<Spinner/></span> }
    { !pendingResults && <span></span> } 
    <div className="uk-container-center">
    <Plot data={plotData} layout={layout} config={{}}/>
    </div>
    <table className="uk-table">
      <thead>
        <tr>
          <th>Username</th>
          <th>Name</th>
          <th>Obligatory</th>
          <th>Bonus</th>
        </tr>
      </thead>
      <tbody>
        { rows }
      </tbody>
    </table>
    </div>
  );
}

const mapStateToProps = state => ({
  userResults: state.get('studentResults'),
  pendingResults: state.getIn(['pendingState', 'studentResults'], false),
});

const mapDispatchToProps = dispatch => ({
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseResults)
