import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import ExerciseSelect from './ExerciseSelect.jsx';

import { fetchCustomResults, enqueueTask } from '../fetchers.js';
import { updateCustomResults } from '../actions.js';

const BaseCustomResult = ({onGenerateResults, exerciseState, taskId, progress, done}) => {
  var selected = exerciseState.filter( exercise => exercise.get('selected'));
  var keys = selected.keySeq().toJS();
  var urlkeys = keys.join(',');
  return (
    <div className="uk-flex uk-flex-wrap">
      <div className="uk-panel-box" style={{flex: '1'}}><ExerciseSelect/></div>
      <div data-uk-sticky="{top:100}">
      <div className="uk-flex uk-flex-column uk-flex-middle uk-margin-left uk-panel uk-panel-box">
        <div><p>Select exercises on the left</p></div>
        { selected.size > 0 &&
          <div><a className="uk-button" onClick={() => onGenerateResults(exerciseState)}>Generate results</a></div>
        }
        <div className="uk-width-1-1 uk-margin-top">
          { progress > 0 && done !== true &&
          <div className="uk-progress">
            <div className="uk-progress-bar" style={{width: progress + "%"}}>{progress}%</div>
          </div>
          }
        </div>
        { done &&
          <div>
            <a href={"/queuetask/" + taskId + "/resultfile"}>Download excel file</a>
          </div>
        }
      </div>
      </div>
    </div>
  );
}

const mapDispatchToProps = (dispatch) => ({
  onGenerateResults: (exerciseState) => {
    var selected = exerciseState.filter( exercise => exercise.get('selected'));
    var exercises = selected.keySeq().toJS();
    //dispatch(fetchCustomResults(exercises));
    dispatch(enqueueTask('/statistics/customresult', { data: {exercises: exercises}, method: "POST" } ))
     .then( taskId => dispatch(updateCustomResults({taskId: taskId})) );
  }
})

const mapStateToProps = (state) => {
  var taskId = state.getIn(['results', 'customResults', 'taskId']);
  return {
    taskId: taskId,
    exerciseState: state.get('exerciseState'),
    progress: state.getIn(['tasks', taskId, 'progress']),
    done: state.getIn(['tasks', taskId, 'done']),
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(BaseCustomResult)
