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


function generateHist2dPlot(userResults) {
  var requiredHistogram = userResults.map( item => item.get('n_passed_required') );
  var bonusHistogram = userResults.map( item => item.get('n_passed_bonus') );
  var maxReq = Math.max(...requiredHistogram.toJS(),0)+1;
  var maxBonus = Math.max(...bonusHistogram.toJS(),0)+1;
  var datax = []
  var datay = []
  var datasize = []
  if(maxReq*maxBonus > 0) {
  var hist2d = Array.from(Array(maxReq*maxBonus), () => 0);
  for(var val of userResults){
    hist2d[val.get('n_passed_required')+val.get('n_passed_bonus') * maxReq]++;
  }
  for(var y = 0; y < maxBonus; y++)
    for(var x = 0; x < maxReq; x++)
      if(hist2d[y*maxReq + x] > 0) {
        datax.push(x);
        datay.push(y);
        datasize.push(hist2d[y*maxReq+x])
      }
  }
  var plotHist2dData = [{
    mode:'markers',
    x: datax,
    y: datay,
    text: datasize,
    marker: {
      sizemode: 'area',
      size: datasize,
      sizeref: 0.1
    }
  }]
  var plotHist2dLayout = {
    hovermode: 'closest',
    xaxis: {
      title: "Required",
      tickmode: "linear",
      dtick: 1
    }, 
    yaxis: {
      title: "Bonus",
      tickmode: "linear",
      dtick: 1
    },
    margin: {
      b: 80,
      t: 0,
      r: 0,
      h: 0
    }
  };
  return {
    data: plotHist2dData,
    layout: plotHist2dLayout
  }
}

function generateHistPlot(userResults) {
  var requiredHistogram = userResults.map( item => item.get('n_passed_required') );
  var bonusHistogram = userResults.map( item => item.get('n_passed_bonus') );
  var plotData2d = [{
    x: requiredHistogram.toJS(),
    y: bonusHistogram.toJS(),
    type: 'histogram2d',
    autobinx: false,
    xbins: {
      start: 0,
      end: 12,
      size: 1
    },
    autobiny: false,
    ybins: {
      start: 0,
      end: 12,
      size: 1
    },
  }];
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
  xaxis: {
    title: "Number of exercises",
    tickmode: "linear",
    dtick: 1
  }, 
  yaxis: {title: "Number of students"},
    margin: {
      b: 80,
      t: 0,
      r: 0,
      h: 0
    }
};
  return {
    data: plotData,
    layout: layout
  }
}

const BaseResults = ({menuPath, userResults, pendingResults, onFilterChange, filter}) => {
  var { data: hist2dData, layout: hist2dLayout } = generateHist2dPlot(userResults);
  var { data: histData, layout: histLayout } = generateHistPlot(userResults);

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
  var renderResults = userResults.filter( item => (item.get('username') + ' ' + item.get('first_name') + ' ' + item.get('last_name')).toLowerCase().indexOf(filter.toLowerCase()) >= 0)
  return (
    <div className="uk-margin-top">
    <h1>
      Results 
      { pendingResults && <Spinner size="uk-icon"/> }
      { !pendingResults && <a href="/statistics/results/excel"><i className="uk-margin-left uk-icon uk-icon-file-excel-o"/></a> }
    </h1>
    <div className="uk-container-center">
    { menuPositionUnder(menuPath, ['results', 'histogram']) && !pendingResults && 
      <article className="uk-article">
      <h1 className="uk-article-title">Histogram</h1>
      <p className="uk-article-meta">Number of students that have passed specific number of obligatory and bonus exercises.</p>
      <Plot key={"resultsPlot"} data={histData} layout={histLayout} config={{}}/>
      </article>
    }
    { menuPositionUnder(menuPath, ['results', 'histogram2d']) && !pendingResults && 
      <article className="uk-article">
      <h1 className="uk-article-title">2d histogram</h1>
      <p className="uk-article-meta">Area proportional to number of students, hover with pointer for values.</p>
      <Plot key={"resultsPlot2d"} data={hist2dData} layout={hist2dLayout} config={{}}/>
      </article>
    }
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
