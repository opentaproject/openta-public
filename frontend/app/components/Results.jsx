import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
} from '../fetchers.js';
import {
  setResultsFilter
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Plot from './Plot.jsx';
import Table from './Table.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import { menuPositionAt, menuPositionUnder } from '../menu.js';

const BaseResults = ({menuPath, userResults, pendingResults, onFilterChange, filter}) => {
  var requiredHistogram = userResults.map( item => item.get('n_passed_required') );
  var bonusHistogram = userResults.map( item => item.get('n_passed_bonus') );
  var plotData = [ {
    x: requiredHistogram.toJS(),
    name: 'Obligatory',
    type: 'histogram',
  },
  {
    x: bonusHistogram.toJS(),
    name: 'Bonus',
    type: 'histogram',
  }
  ];
  var layout = {
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
  var tableFields = [
    {
      name: 'Username',
      index: 'username',
      type: 'string',
    },
    {
      name: 'First',
      index: 'first_name',
      type: 'string',
    },
    {
      name: 'Last',
      index: 'last_name',
      type: 'string',
    },
    {
      name: 'Obligatory',
      index: 'n_passed_required'
    },
    {
      name: 'Bonus',
      index: 'n_passed_bonus'
    },
    {
      name: 'Total',
      index: 'n_passed_total'
    },
  ];
  var renderResults = userResults.filter( item => (item.get('username') + ' ' + item.get('first_name') + ' ' + item.get('last_name')).indexOf(filter) >= 0)
  return (
    <div className="uk-margin-top">
    <h1>Results { pendingResults && <Spinner size="uk-icon"/> }</h1>
    <div className="uk-container-center">
    { menuPositionUnder(menuPath, ['results', 'histogram']) && !pendingResults && <Plot key={"resultsPlot"} data={plotData} layout={layout} config={{}}/>}
    </div>
    { menuPositionUnder(menuPath, ['results', 'list']) &&
    <form className="uk-form">
      <div className="uk-form-row">
        <input type="text" placeholder="Filter on name and username" className="uk-width-1-1" onChange={onFilterChange} value={filter}/>        
      </div>
    </form>
    }
    { menuPositionUnder(menuPath, ['results', 'list']) &&
      <Table tableId='results' data={renderResults} fields={tableFields} keyIndex={'username'}/>
    }

    </div>
  );
}

const mapStateToProps = state => ({
  menuPath: state.getIn(['menuPath']),
  userResults: state.getIn(['results', 'studentResults']),
  filter: state.getIn(['results', 'studentResultsFilter']),
  pendingResults: state.getIn(['pendingState', 'studentResults'], false),
});

const mapDispatchToProps = dispatch => ({
  onFilterChange: (e) => dispatch(setResultsFilter(e.target.value))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseResults)
