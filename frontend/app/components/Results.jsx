import React from 'react';
import { connect } from 'react-redux';
import {
fetchStudentDetailResults,
fetchUserExercises,
} from '../fetchers.js';
import {
  setSelectedStudentResults,
  setResultsFilter,
  setDetailResultsFilter,
} from '../actions.js';
import Spinner from './Spinner.jsx';
import Badge from './Badge.jsx';
import Plot from './Plot.jsx';
import Table from './Table.jsx';
import StudentResults from './StudentResults.jsx';
import CustomResult from './CustomResult.jsx';
import CanvasGradebook from './CanvasGradebook.jsx';

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

const renderFilter = ({filteredUsers, onFilterChange, onFilterKeypress, filter, onRequiredDeadline, requiredFilter, onBonusDeadline, bonusFilter}) => (//{{{
      <div className="results-filters uk-margin-right  uk-margin-bottom">
        <div className="uk-panel uk-panel-box uk-margin-top">
          <h3 className="uk-panel-title">Filters</h3>
          <form className="uk-form uk-form-stacked">
            <div className="uk-form-row">
              <span className="uk-form-label">Text search</span>
              <input type="text" placeholder="Filter on name and username" className={"uk-width-1-1 " + (filteredUsers.size === 1 ? 'uk-form-success' : '')} onChange={onFilterChange} onKeyPress={(e) => onFilterKeypress(e, filteredUsers  )} value={filter}/>        
            </div>


          </form>
        </div>
      </div>
)//}}}

const BaseResults = ({menuPath,
                     userResults,
                     pendingResults,
                     onFilterChange,
                     onFilterKeypress,
                     onRequiredDeadline,
                     onBonusDeadline,
                     filter,
                     onUserClick,
                     selectedUser,
                     activeDetailExercise,
                     activeCourse,
                     }) => {
  var renderResults = userResults.filter( item => (item.get('username') + ' ' + item.get('first_name') + ' ' + item.get('last_name')).toLowerCase().indexOf(filter.toLowerCase()) >= 0)
    .map( user => (immutable.Map({
      'username': user.get('username'),
      'pk': user.get('pk'),
      'first_name': user.get('first_name'),
      'last_name': user.get('last_name'),
      'n_passed_required': user.getIn(['required', false]),
      'n_passed_bonus': user.getIn(['bonus', false]),
      'n_after_deadline': '(' + (user.getIn(['required', 'n_correct'])-user.getIn(['required', 'n_image_deadline'])+
                          user.getIn(['bonus', 'n_correct'])-user.getIn(['bonus', 'n_image_deadline'])) + ')',
      'n_passed_optional': user.getIn(['n_optional']),
      'n_passed_total': user.getIn(['total'],0),
      'n_failed_audits': user.getIn(['failed_by_audits']),
      'audits'  : ( user.getIn(['total_audits'],0) - user.getIn(['failed_by_audits'],0) ).toString() + ':' + user.getIn(['failed_by_audits'],0).toString(),
      'total_complete_no_deadline':user.getIn(['total_complete_no_deadline']),
      'required': user.getIn(['required','number_complete_by_deadline']).toString()  + ':' + (  user.getIn(['required','number_complete']) -user.getIn(['required','number_complete_by_deadline']) ).toString() ,
      'required_ok': user.getIn(['required','number_complete_by_deadline']).toString()  ,
      'required_late':  (  user.getIn(['required','number_complete']) -user.getIn(['required','number_complete_by_deadline']) ).toString() ,
      'bonus': user.getIn(['bonus','number_complete_by_deadline']).toString()  + ':' + (  user.getIn(['bonus','number_complete']) -user.getIn(['bonus','number_complete_by_deadline']) ).toString() ,
      'optional': user.getIn(['optional','number_complete_by_deadline']).toString()  + ':' + (  user.getIn(['optional','number_complete']) -user.getIn(['optional','number_complete_by_deadline']) ).toString() ,
      'total' :   user.getIn(['total_complete_before_deadline']).toString()  + ':' + (  user.getIn(['total_complete_no_deadline']) -user.getIn(['total_complete_before_deadline']) ).toString() 
    })));
  var { data: hist2dData, layout: hist2dLayout } = generateHist2dPlot(renderResults);
  var { data: histData, layout: histLayout } = generateHistPlot(renderResults);

  var tableFields = [//{{{
    /*{
      name: 'Student id',
      index: 'pk'
    },*/
    {
      name: 'Username',
      index: 'username',
      type: 'string',
    },
/*  {
      name: 'First',
      index: 'first_name',
      type: 'string',
    },
    {
      name: 'Last',
      index: 'last_name',
      type: 'string',
    },*/
    {
      name: 'Obligatory',
      index: 'required'
    },
    
    {
      name: 'Bonus',
      index: 'bonus'
    },
    {
      name: 'Optional',
      index: 'optional'
    },
    {
      name: 'Audits',
      index: 'audits'
    },
    /*{
      name: 'Late',
      index: 'n_after_deadline'
    }, */
    {
      name: 'Total',
            index: 'total',
    },
  ];//}}}
  var excelParameters = "required_key=" +  "&" + "bonus_key=" ;
  //var filters = {

  return (
    <div className="uk-margin-top uk-width-1-1">
    <div className="uk-flex uk-flex-wrap uk-width-1-1">

    {!menuPositionUnder(menuPath, ['results', 'custom']) &&
      <div className="uk-width-1-1 uk-text-center">
          <div className="uk-flex uk-flex-center uk-flex-middle">
          { pendingResults !== false && <span className="uk-margin-right"><Spinner size="uk-text-medium"/></span>}
          { typeof(pendingResults) !== 'boolean' &&
            <div className="uk-progress uk-width-medium-1-5 uk-width-4-5"><div className="uk-progress-bar" style={{width: pendingResults + '%'}}>{pendingResults}</div></div> }
          </div>
      </div>
    }
      { menuPositionUnder(menuPath, ['results', 'download']) && !pendingResults && 
      <div className="uk-width-1-1 uk-text-center">
        <h1><a href={SUBPATH + "/course/" + activeCourse + "/statistics/results/excel?" + excelParameters}><i className="uk-margin-left uk-icon uk-icon-file-excel-o DownloadExcel"/></a></h1> 
      </div>
      }
      { menuPositionUnder(menuPath, ['results', 'gradebook']) && !pendingResults &&
      <div className="uk-width-1-1 uk-text-center">
        <CanvasGradebook/>
      </div>
      }
      { !activeDetailExercise &&
        !menuPositionUnder(menuPath, ['results', 'download']) &&
        !menuPositionUnder(menuPath, ['results', 'custom']) &&
        !menuPositionUnder(menuPath, ['results', 'gradebook']) &&
        renderFilter({filteredUsers: renderResults, onFilterChange, onFilterKeypress, filter, onRequiredDeadline,  onBonusDeadline}) }
    { !menuPositionUnder(menuPath, ['results', 'custom']) &&
      <div className="results-table" style={{flex:'1'}}> {/*uk-width-4-10 uk-overflow-container*/}
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
        { menuPositionUnder(menuPath, ['results', 'list']) && !activeDetailExercise &&
            <div className="uk-scrollable-box uk-margin-bottom" style={{height:'30vh'}}><Table tableId='results' data={renderResults} fields={tableFields} keyIndex={'pk'} activeItem={selectedUser} onItem={(id) => onUserClick(activeCourse,id)}/></div>
        }
      </div>
    }
        { menuPositionUnder(menuPath, ['results', 'list']) && selectedUser && activeDetailExercise &&
        <div className="uk-width-1-1">
        <StudentResults/> 
        </div>
        }
        { menuPositionUnder(menuPath, ['results', 'list']) && selectedUser && !activeDetailExercise &&
        <div className="uk-margin-left uk-margin-small-right">
        <StudentResults/> 
        </div>
        }
        { menuPositionUnder(menuPath, ['results', 'custom']) &&
          <div className="uk-width-medium-4-5 uk-margin-small-left"><CustomResult/></div>
        }
    </div>
    </div>
  );
}

function handleUserClick(coursePk,userPk, deadline, imageDeadline) {
  return dispatch => {
    dispatch(fetchStudentDetailResults(userPk))
    dispatch(setSelectedStudentResults(userPk))
    dispatch(fetchUserExercises(coursePk,userPk) )
  }
}

const mapStateToProps = state => ({
  menuPath: state.getIn(['menuPath']),
  userResults: state.getIn(['results', 'studentResults']),
  selectedUser: state.getIn(['results', 'selectedUser']),
  filter: state.getIn(['results', 'filters', 'text']),
  pendingResults: state.getIn(['pendingState', 'studentResults'], false),
  activeDetailExercise: state.getIn(['results', 'detailResultExercise'], false),
  activeCourse: state.get('activeCourse')
});

const handleRequiredDeadline = (value) => (dispatch) => {
    dispatch(setResultsFilter({ 'requiredKey': value}))
    switch(value) {
      case 'n_correct':
        return dispatch(setDetailResultsFilter({ 'requiredKeys': ['correct', 'image'] }));
      case 'n_deadline':
        return dispatch(setDetailResultsFilter({ 'requiredKeys': ['correct_deadline', 'image'] }));
      case 'n_image_deadline':
        return dispatch(setDetailResultsFilter({ 'requiredKeys': ['correct_deadline', 'image_deadline'] }));
    }
  }
const handleBonusDeadline = (value) => (dispatch) => {
    dispatch(setResultsFilter({ 'bonusKey': value}))
    switch(value) {
      case 'n_correct':
        return dispatch(setDetailResultsFilter({ 'bonusKeys': ['correct', 'image'] }));
      case 'n_deadline':
        return dispatch(setDetailResultsFilter({ 'bonusKeys': ['correct_deadline', 'image'] }));
      case 'n_image_deadline':
        return dispatch(setDetailResultsFilter({ 'bonusKeys': ['correct_deadline', 'image_deadline'] }));
    }
  }

const mapDispatchToProps = dispatch => ({
  onFilterChange: (e) => dispatch(setResultsFilter({'text': e.target.value})),
  onFilterKeypress: (e, filteredUsers, coursePk, deadline, imageDeadline) => {
    if(e.key === 'Enter') {
      e.preventDefault();
      if(filteredUsers.size === 1) {
        dispatch(handleUserClick(coursePk,filteredUsers.first().get('pk'), deadline, imageDeadline))
      }
    }
  },
  onRequiredDeadline: (value) => dispatch(handleRequiredDeadline(value)), //dispatch(setResultsFilter({ 'requiredKey': value})),
  onBonusDeadline: (value) => dispatch(handleBonusDeadline(value)),//dispatch(setResultsFilter({ 'bonusKey': value})),
  onUserClick: (coursePk, userPk,  deadline, imageDeadline) => dispatch(handleUserClick(coursePk,userPk, deadline, imageDeadline))
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseResults)
