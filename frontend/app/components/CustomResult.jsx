import React, { PropTypes } from 'react';
import { connect } from 'react-redux';
import ExerciseSelect from './ExerciseSelect.jsx';

import { fetchCustomResults } from '../fetchers.js';

const BaseCustomResult = ({onGenerateResults, exerciseState, taskId, progress, done}) => {
  var selected = exerciseState.filter( exercise => exercise.get('selected'));
  var keys = selected.keySeq().toJS();
  var urlkeys = keys.join(',');
  return (
    <div className="uk-flex">
      <div className="uk-width-1-2"><ExerciseSelect/></div>
      <div className="uk-flex uk-width-1-2 uk-flex-column uk-flex-middle uk-margin-left">
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
  );
}

const mapDispatchToProps = (dispatch) => ({
  onGenerateResults: (exerciseState) => {
    var selected = exerciseState.filter( exercise => exercise.get('selected'));
    var exercises = selected.keySeq().toJS();
    dispatch(fetchCustomResults(exercises));
  }
})

const mapStateToProps = (state) => ({
  exerciseState: state.get('exerciseState'),
  taskId: state.getIn(['results', 'customResults', 'taskId']),
  progress: state.getIn(['results', 'customResults', 'progress']),
  done: state.getIn(['results', 'customResults', 'done']),
})

export default connect(mapStateToProps, mapDispatchToProps)(BaseCustomResult)
