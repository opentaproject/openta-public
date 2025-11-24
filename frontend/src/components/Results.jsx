import React from 'react';
//import { faker } from '@faker-js/faker';
import { connect } from 'react-redux';
import { fetchStudentDetailResults, fetchUserExercises } from '../fetchers.js';
import { setSelectedStudentResults, setResultsFilter, setDetailResultsFilter } from '../actions.js';
import Table from './Table.jsx';
import StudentResults from './StudentResults.jsx';
import CustomResult from './CustomResult.jsx';
import CanvasGradebook from './CanvasGradebook.jsx';
import { updateCustomResults } from '../actions.js';
import { Histogram1 } from './Histogram1.jsx';
import HistogramAll from './HistogramAll.jsx';
import { Histogram2 } from './Histogram2.jsx';
import { Histogram3 } from './Histogram3.jsx';

import immutable from 'immutable';
import { SUBPATH } from '../settings.js';
import { menuPositionUnder } from '../menu.js';

import { enqueueTask } from '../fetchers.js';

const renderFilter = (
  {
    filteredUsers,
    onFilterChange,
    onFilterKeypress,
    filter,
    onRequiredDeadline,
    requiredFilter,
    onBonusDeadline,
    bonusFilter
  } //{{{
) => (
  <div className="uk-sticky uk-margin-top">
    <form className="uk-form ">
      <div className="uk-form-row">
        <input
          type="text"
          placeholder="Filter on name and username"
          className={'uk-width-1-1 ' + (filteredUsers.size === 1 ? 'uk-form-success' : '')}
          onChange={onFilterChange}
          onKeyPress={(e) => onFilterKeypress(e, filteredUsers)}
          value={filter}
        />
      </div>
    </form>
  </div>
); //}}}

const BaseResults = ({
  menuPath,
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
  progress,
  onGenerateResults,
  done,
  taskId,
  exerciseState,
  courseAggregates,
  admin
}) => {
  {
    /* // THIS FAILS SINCE userResults object contains function
  var store_key = 'userResults' + activeCourse
  if ( false && userResults.size > 0 ){
	console.log("LOCAL STORE IS UPDATEWD size= ", userResults.size )
  	localStorage.setItem(store_key, JSON.stringify( userResults) )
    }
  if (  true  localStorage.getItem(store_key)  ){
	console.log("LOCAL STORE IS ACCESED")
  	userResults = JSON.parse(  localStorage.getItem(store_key) ) 
	}
*/
  }
  //faker.setLocale('sv');
  //var TSH=s=>{ for(var i=0,h=9;i<s.length;)h=Math.imul(h^s.charCodeAt(i++),9**9); return ( ( Math.abs( h^h>>>9 ) % 100000 ).toString() ).padStart(5,"0") }
  //var TSH=s=> { return faker.name.firstName() + ' ' + faker.name.lastName() }

  var d = userResults.filter(  item => item.get('date',false) ).toJS() 
  try {
  	var date_computed = d.pop().date 
  } catch (error ) {
	var date_computed = 'XXXXX';
	}
  var renderResults = userResults.filter(  item => item.get('username',false) )
    .filter(
      (item) =>
        (item.get('username') + ' ' + item.get('first_name') + ' ' + item.get('last_name'))
          .toLowerCase()
          .indexOf(filter.toLowerCase()) >= 0
    )
    .map((user) =>
      immutable.Map({
        username: user.get('username'),
        pk: user.get('pk'),
        first_name: user.get('first_name'),
        last_name: user.get('last_name'),
        n_passed_required: user.getIn(['required', 'n_complete_no_deadline']),
        n_passed_bonus: user.getIn(['bonus', 'n_complete_no_deadline']),
        n_after_deadline:
          '(' +
          (user.getIn(['required', 'n_correct']) -
            user.getIn(['required', 'n_image_deadline']) +
            user.getIn(['bonus', 'n_correct']) -
            user.getIn(['bonus', 'n_image_deadline'])) +
          ')',
        n_passed_optional: user.getIn(['n_optional']),
        n_passed_total: user.getIn(['total'], 0),
        n_failed_audits: user.getIn(['failed_by_audits']),
        audits:
          (user.getIn(['total_audits'], 0) - user.getIn(['failed_by_audits'], 0)).toString() +
          ':' +
          user.getIn(['failed_by_audits'], 0).toString(),
        total_complete_no_deadline: user.getIn(['total_complete_no_deadline']),
        required:
          user.getIn(['required', 'number_complete_by_deadline'],0).toString() +
          ':' +
          (
            user.getIn(['required', 'number_complete'],0) - user.getIn(['required', 'number_complete_by_deadline'],0)
          ).toString(),
        required_ok: user.getIn(['required', 'number_complete_by_deadline'],0).toString(),
        required_late: (
          user.getIn(['required', 'number_complete'],0) - user.getIn(['required', 'number_complete_by_deadline'],0)
        ).toString(),
        bonus:
          user.getIn(['bonus', 'number_complete_by_deadline'],0).toString() +
          ':' +
          (user.getIn(['bonus', 'number_complete'],0) - user.getIn(['bonus', 'number_complete_by_deadline'],0)).toString(),
        optional:
          user.getIn(['optional', 'number_complete_by_deadline'],0).toString() +
          ':' +
          (
            user.getIn(['optional', 'number_complete'],0) - user.getIn(['optional', 'number_complete_by_deadline'],0)
          ).toString(),
        total:
          user.getIn(['total_complete_before_deadline'],0).toString() +
          ':' +
          (user.getIn(['total_complete_no_deadline'],0) - user.getIn(['total_complete_before_deadline'],0)).toString(),
	total_queries: user.getIn(['total_queries'],0),
	total_correct_queries: user.getIn(['total_correct_queries'],0)
      })
    );
  //localStorage.setItem('renderResults', userResults )
  //} else {
  //var renderResults = JSON.parse( localStorage.getItem('renderedResults') )
  // }
  //console.log("renderResults = ", renderResults.toJS() )
  //
  var fusername = admin ? 'Username' : 'Fake Username';
  var ffirst = admin ? 'First' : 'Fake First';
  var flast = admin ? 'Last' : 'Fake Last';
  var tableFields = [
    //{{{
    /*{
      name: 'Student id',
      index: 'pk'
    },*/
    {
      name: fusername,
      index: 'username',
      type: 'string'
    },
    {
      name: ffirst,
      index: 'first_name',
      type: 'string'
    },
    {
      name: flast,
      index: 'last_name',
      type: 'string'
    },
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
      index: 'total'
    }
  ]; //}}}
  //if  ( ! admin ){
  //tableFields = anon_tableFields
  //}
  var excelParameters = 'required_key=' + '&' + 'bonus_key=';
  //var filters = {
  var filterDOM = renderFilter({
    filteredUsers: renderResults,
    onFilterChange,
    onFilterKeypress,
    filter,
    onRequiredDeadline,
    onBonusDeadline
  });

  var dats = 'DATS';
  var txt = ( typeof(pendingResults) !== 'boolean' ) ? '     ' + pendingResults : ''
  var caption = "Results as of " + date_computed + '    ' + txt
  return (
    <div className="uk-margin-top uk-width-1-1">
      <div className="uk-flex uk-flex-wrap uk-width-1-1">
        {/*!menuPositionUnder(menuPath, ['results', 'custom']) &&
      <div className="uk-width-1-1 uk-text-center">
          <div className="uk-flex uk-flex-center uk-flex-middle">
          {  pendingResults !== false && <span className="uk-text-small uk-margin-right"><Spinner size="uk-text-small"/></span>}
          { ( ( typeof(pendingResults) !== 'boolean' ) ) &&
            <div className="uk-progress uk-progress-mini uk-width-1-2">
			  <div className="uk-text-small uk-progress-bar" style={{width: pendingResults + '%'}}>{pendingResults}</div></div> }
          </div>
      </div>
    */}
        {
          menuPositionUnder(menuPath, ['results', 'download']) && !pendingResults && (
            <div className="uk-width-1-2 uk-text-center">
              <div>
                <a className="uk-button GenerateResults" onClick={() => onGenerateResults(exerciseState, activeCourse)}>
                  GenerateResults
                </a>
              </div>
              <div className="uk-width-1-1 uk-margin-top">
                {progress >= 0 && done !== true && (
                  <div className="uk-progress">
                    <div className="uk-progress-bar" style={{ width: progress + '%' }}></div>
                  </div>
                )}
              </div>
              {done && (
                <div>
                  <a className="DownloadExcel" href={SUBPATH + '/queuetask/' + taskId + '/resultfile'}>
                    Download excel file
                  </a>
                </div>
              )}
            </div>
          )

          //<div className="uk-width-1-1 uk-text-center">
          //  <h1><a href={SUBPATH + "/course/" + activeCourse + "/statistics/results/excel?" + excelParameters}><i className="uk-margin-left uk-icon uk-icon-file-excel-o DownloadExcel"/></a></h1>
          //</div>
        }
        {menuPositionUnder(menuPath, ['results', 'gradebook']) && !pendingResults && (
          <div className="uk-width-1-1 uk-text-center">
            <CanvasGradebook />
          </div>
        )}
        {/* !activeDetailExercise &&
        !menuPositionUnder(menuPath, ['results', 'download']) &&
        !menuPositionUnder(menuPath, ['results', 'custom']) &&
        !menuPositionUnder(menuPath, ['results', 'gradebook']) &&
        renderFilter({filteredUsers: renderResults, onFilterChange, onFilterKeypress, filter, onRequiredDeadline,  onBonusDeadline})  */}
        {!menuPositionUnder(menuPath, ['results', 'custom']) && (
          <div className="results-table" style={{ flex: '1' }}>
            {' '}
            {/*uk-width-4-10 uk-overflow-container*/}
            <div className="uk-container-center">
              {menuPositionUnder(menuPath, ['results', 'histogram']) && <Histogram1 renderResults={renderResults} />}
              {menuPositionUnder(menuPath, ['results', 'histogram2']) && <Histogram2 renderResults={renderResults} />}
		{menuPositionUnder(menuPath, ['results', 'histogram3']) && <Histogram3 renderResults={renderResults} />}
              {menuPositionUnder(menuPath, ['results', 'histogramall']) && <HistogramAll />}
              {/* menuPositionUnder(menuPath, ['results', 'histogramall']) &&
			 <button onClick={() => GonGenerateCourseResults( activeCourse)}> {dats} </button> 
	*/}
              {menuPositionUnder(menuPath, ['results', 'list']) && !activeDetailExercise && (
                <div className="uk-width-1-1 uk-margin-bottom">
                  { false && typeof pendingResults !== 'boolean' && (
			  <div className="uk-width-1-1">
			  <span className="uk-text uk-text-warning  uk-align-right"> {pendingResults} </span> 
			  </div>

		  
                    /* <div className="uk-progress uk-progress-mini uk-width-1-1">
                      <div className="uk-text-small uk-progress-bar" style={{ width: pendingResults + '%' }}>
                        {pendingResults}
                      </div>
                    </div>
		    */
                  )}
                  {filterDOM}
                  <div className="uk-scrollable-box">
                    <Table
		      caption={caption}
                      tableId="results"
                      data={renderResults}
                      fields={tableFields}
                      keyIndex={'pk'}
                      activeItem={selectedUser}
                      onItem={(id) => onUserClick(activeCourse, id)}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {menuPositionUnder(menuPath, ['results', 'list']) && selectedUser && activeDetailExercise && (
          <div className="uk-width-1-1">
            <StudentResults />
          </div>
        )}
        {menuPositionUnder(menuPath, ['results', 'list']) && selectedUser && !activeDetailExercise && (
          <div className="uk-margin-left uk-margin-small-right">
            <StudentResults />
          </div>
        )}
        {menuPositionUnder(menuPath, ['results', 'custom']) && (
          <div className="uk-width-medium-4-5 uk-margin-small-left">
            <CustomResult />
          </div>
        )}
      </div>
    </div>
  );
};

function handleUserClick(coursePk, userPk, deadline, imageDeadline) {
  return (dispatch) => {
    dispatch(fetchStudentDetailResults(userPk));
    dispatch(setSelectedStudentResults(userPk));
    dispatch(fetchUserExercises(coursePk, userPk));
  };
}

const mapStateToProps = (state) => {
  var taskId = state.getIn(['results', 'customResults', 'taskId']);
  return {
    taskId: taskId,
    exerciseState: state.get('exerciseState'),
    menuPath: state.getIn(['menuPath']),
    userResults: state.getIn(['results', 'studentResults']),
    selectedUser: state.getIn(['results', 'selectedUser']),
    filter: state.getIn(['results', 'filters', 'text']),
    pendingResults: state.getIn(['pendingState', 'studentResults'], false),
    activeDetailExercise: state.getIn(['results', 'detailResultExercise'], false),
    activeCourse: state.get('activeCourse'),
    progress: state.getIn(['tasks', taskId, 'progress']),
    done: state.getIn(['tasks', taskId, 'done']),
    courseAggregates: state.getIn(['statistics', 'course_aggregates']),
    admin: state.getIn(['login', 'groups'], immutable.List([])).includes('Admin')
  };
};

const handleRequiredDeadline = (value) => (dispatch) => {
  dispatch(setResultsFilter({ requiredKey: value }));
  switch (value) {
    case 'n_correct':
      return dispatch(setDetailResultsFilter({ requiredKeys: ['correct', 'image'] }));
    case 'n_deadline':
      return dispatch(setDetailResultsFilter({ requiredKeys: ['correct_deadline', 'image'] }));
    case 'n_image_deadline':
      return dispatch(setDetailResultsFilter({ requiredKeys: ['correct_deadline', 'image_deadline'] }));
  }
};
const handleBonusDeadline = (value) => (dispatch) => {
  dispatch(setResultsFilter({ bonusKey: value }));
  switch (value) {
    case 'n_correct':
      return dispatch(setDetailResultsFilter({ bonusKeys: ['correct', 'image'] }));
    case 'n_deadline':
      return dispatch(setDetailResultsFilter({ bonusKeys: ['correct_deadline', 'image'] }));
    case 'n_image_deadline':
      return dispatch(setDetailResultsFilter({ bonusKeys: ['correct_deadline', 'image_deadline'] }));
  }
};

const mapDispatchToProps = (dispatch) => ({
  onFilterChange: (e) => dispatch(setResultsFilter({ text: e.target.value })),
  onFilterKeypress: (e, filteredUsers, coursePk, deadline, imageDeadline) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredUsers.size === 1) {
        dispatch(handleUserClick(coursePk, filteredUsers.first().get('pk'), deadline, imageDeadline));
      }
    }
  },
  onRequiredDeadline: (value) => dispatch(handleRequiredDeadline(value)), //dispatch(setResultsFilter({ 'requiredKey': value})),
  onBonusDeadline: (value) => dispatch(handleBonusDeadline(value)), //dispatch(setResultsFilter({ 'bonusKey': value})),
  onUserClick: (coursePk, userPk, deadline, imageDeadline) =>
    dispatch(handleUserClick(coursePk, userPk, deadline, imageDeadline)),
  onGenerateResults: (exerciseState, activeCourse) => {
    dispatch(enqueueTask('/course/' + activeCourse + '/statistics/results/excel')).then((taskId) =>
      dispatch(updateCustomResults({ taskId: taskId }))
    );
  }
});

export default connect(mapStateToProps, mapDispatchToProps)(BaseResults);
