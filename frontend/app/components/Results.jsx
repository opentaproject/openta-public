import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import {
fetchStudentDetailResults
} from '../fetchers.js';
import {
  setSelectedStudentResults,
  setResultsFilter
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Plot from './Plot.jsx';
import Table from './Table.jsx';
import StudentResults from './StudentResults.jsx';

import immutable from 'immutable';
import moment from 'moment';
import {SUBPATH} from '../settings.js';
import { menuPositionAt, menuPositionUnder } from '../menu.js';


function generateHist2dPlot(userResults) {//{{{
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
}//}}}

function generateHistPlot(userResults) {//{{{
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
}//}}}

const renderFilter = ({onFilterChange, filter, onRequiredDeadline, requiredFilter, onBonusDeadline, bonusFilter}) => (//{{{
      <div className="results-filters uk-width-3-10">
        <div className="uk-panel uk-panel-box uk-margin-top">
          <form className="uk-form uk-form-stacked">
            <div className="uk-form-row">
              <span className="uk-form-label">Text search</span>
              <input type="text" placeholder="Filter on name and username" className="uk-width-1-1" onChange={onFilterChange} value={filter}/>        
            </div>

            <span className="uk-form-label uk-margin-top">Obligatory deadline</span>
            <div className="uk-form-row uk-margin-small-top">
              <label>
              <input type="radio" name="required" className="uk-width-1-1 uk-margin-small-right" onChange={() => onRequiredDeadline('n_correct')} checked={requiredFilter === 'n_correct'}/>        
              No deadline
              </label>
            </div>
            <div className="uk-form-row uk-margin-small-top">
              <label>
              <input type="radio" name="required" className="uk-width-1-1 uk-margin-small-right" onChange={() => onRequiredDeadline('n_deadline')} checked={requiredFilter === 'n_deadline'}/>        
              Answer
              </label>
            </div>
            <div className="uk-form-row uk-margin-small-top">
              <label>
              <input type="radio" name="required" className="uk-width-1-1 uk-margin-small-right" onChange={() => onRequiredDeadline('n_image_deadline')} checked={requiredFilter === 'n_image_deadline'}/>        
              Answer & Image
              </label>
            </div>

            <span className="uk-form-label uk-margin-top">Bonus deadline</span>
            <div className="uk-form-row uk-margin-small-top">
              <label>
              <input type="radio" name="bonus" className="uk-width-1-1 uk-margin-small-right" onChange={() => onBonusDeadline('n_correct')} checked={bonusFilter === 'n_correct'}/>        
              No deadline
              </label>
            </div>
            <div className="uk-form-row uk-margin-small-top">
              <label>
              <input type="radio" name="bonus" className="uk-width-1-1 uk-margin-small-right" onChange={() => onBonusDeadline('n_deadline')} checked={bonusFilter === 'n_deadline'}/>        
              Answer
              </label>
            </div>
            <div className="uk-form-row uk-margin-small-top">
              <label>
              <input type="radio" name="bonus" className="uk-width-1-1 uk-margin-small-right" onChange={() => onBonusDeadline('n_image_deadline')} checked={bonusFilter === 'n_image_deadline'}/>        
              Answer & Image
              </label>
            </div>
          </form>
        </div>
      </div>
)//}}}

const BaseResults = ({menuPath, 
                     userResults, 
                     pendingResults, 
                     onFilterChange, 
                     onRequiredDeadline,
                     onBonusDeadline,
                     filter, 
                     requiredFilter, 
                     bonusFilter,
                     onUserClick,
                     selectedUser,
                     }) => {
  var renderResults = userResults.filter( item => (item.get('username') + ' ' + item.get('first_name') + ' ' + item.get('last_name')).toLowerCase().indexOf(filter.toLowerCase()) >= 0)
    .map( user => (immutable.Map({
      'username': user.get('username'),
      'pk': user.get('pk'),
      'first_name': user.get('first_name'),
      'last_name': user.get('last_name'),
      'n_passed_required': user.getIn(['required', requiredFilter]),
      'n_passed_bonus': user.getIn(['bonus', bonusFilter]),
      'n_passed_total': user.getIn(['total']),
    })));
  var { data: hist2dData, layout: hist2dLayout } = generateHist2dPlot(renderResults);
  var { data: histData, layout: histLayout } = generateHistPlot(renderResults);

  var tableFields = [//{{{
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
  ];//}}}
  var excelParameters = "required_key=" + requiredFilter + "&" + "bonus_key=" + bonusFilter;
  //var filters = {

  return (
    <div className="uk-margin-top uk-width-1-1">
    <div className="uk-grid uk-width-1-1">
      { renderFilter({onFilterChange, filter, onRequiredDeadline, requiredFilter, onBonusDeadline, bonusFilter}) }
      <div className="results-table uk-width-4-10 uk-overflow-container">
        <h1>
          Results 
          { pendingResults && <Spinner size="uk-icon"/> }
          { !pendingResults && <a href={"/statistics/results/excel?" + excelParameters}><i className="uk-margin-left uk-icon uk-icon-file-excel-o"/></a> }
        </h1>
        <div className="uk-container-center">
        { menuPositionUnder(menuPath, ['results', 'histogram']) && !pendingResults && 
          <article className="uk-article">
          <p className="uk-article-meta">Number of students that have passed specific number of obligatory and bonus exercises.</p>
          <Plot key={"resultsPlot"} data={histData} layout={histLayout} config={{}} key={"histplot"}/>
          </article>
        }
        { menuPositionUnder(menuPath, ['results', 'histogram2d']) && !pendingResults && 
          <article className="uk-article">
          <p className="uk-article-meta">Area proportional to number of students, hover with pointer for values.</p>
          <Plot key={"resultsPlot2d"} data={hist2dData} layout={hist2dLayout} config={{}} key={"hist2dplot"}/>
          </article>
        }
        </div>
        { menuPositionUnder(menuPath, ['results', 'list']) &&
            <Table tableId='results' data={renderResults} fields={tableFields} keyIndex={'pk'} onItem={(id) => onUserClick(id)}/>
        }
      </div>
      { selectedUser && 
        <div className="uk-width-3-10">
        <StudentResults/> 
        </div>
      }
    </div>
    </div>
  );
}

function handleUserClick(userPk, deadline, imageDeadline) {
  return dispatch => {
    dispatch(fetchStudentDetailResults(userPk))
    dispatch(setSelectedStudentResults(userPk))
  }
}

const mapStateToProps = state => ({
  menuPath: state.getIn(['menuPath']),
  userResults: state.getIn(['results', 'studentResults']),
  selectedUser: state.getIn(['results', 'selectedUser']),
  filter: state.getIn(['results', 'filters', 'text']),
  requiredFilter: state.getIn(['results', 'filters', 'requiredKey'], 'n_correct'),
  bonusFilter: state.getIn(['results', 'filters', 'bonusKey'], 'n_correct'),
  pendingResults: state.getIn(['pendingState', 'studentResults'], false),
});

const mapDispatchToProps = dispatch => ({
  onFilterChange: (e) => dispatch(setResultsFilter({'text': e.target.value})),
  onRequiredDeadline: (value) => dispatch(setResultsFilter({ 'requiredKey': value})),
  onBonusDeadline: (value) => dispatch(setResultsFilter({ 'bonusKey': value})),
  onUserClick: (userPk, deadline, imageDeadline) => dispatch(handleUserClick(userPk, deadline, imageDeadline))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseResults)
